"""
Stitch-job worker – Redis Streams consumer.

Run:  python -m app.worker

Reads messages from the `stitch:jobs` stream via a consumer group,
downloads input photos from S3, runs the Exposea CLI, uploads results
back to S3, and updates the DB status accordingly.

Environment variables (see app/config.py):
    REDIS_URL, REDIS_ENABLED, STREAM_KEY, CONSUMER_GROUP,
    CONSUMER_NAME, BLOCK_MS, CLAIM_IDLE_MS, MAX_RETRIES, WORK_DIR,
    EXPOSEA_PATH
"""

import asyncio
import io
import json
import logging
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path


from .config import settings
from .database import async_session_maker
from .models.user import User as _User          # noqa: F401 – register with SQLAlchemy
from .models.project import Project as _Project  # noqa: F401
from .models.photo import Photo as _Photo        # noqa: F401
from .models.stitch_job import StitchJob
from .repositories import stitch_jobs_repository, photos_repository
from .services.redis_service import redis_service
from .services.s3_service import s3_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("stitch-worker")

# ── helpers ───────────────────────────────────────────────────────


async def _load_job(job_id: str) -> StitchJob | None:
    """Load a StitchJob from the database in a fresh session."""
    async with async_session_maker() as session:
        return await stitch_jobs_repository.get_stitch_job(session, job_id)


async def _update_job(
    job_id: str,
    *,
    status: str,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
    result_s3_key: str | None = None,
    preview_s3_key: str | None = None,
    log_s3_key: str | None = None,
    error_message: str | None = None,
    attempt: int | None = None,
) -> None:
    """Persist status changes in a dedicated session."""
    async with async_session_maker() as session:
        job = await stitch_jobs_repository.get_stitch_job(session, job_id)
        if job is None:
            return
        job.status = status
        if started_at is not None:
            job.started_at = started_at
        if finished_at is not None:
            job.finished_at = finished_at
        if result_s3_key is not None:
            job.result_s3_key = result_s3_key
        if preview_s3_key is not None:
            job.preview_s3_key = preview_s3_key
        if log_s3_key is not None:
            job.log_s3_key = log_s3_key
        if error_message is not None:
            job.error_message = error_message
        if attempt is not None:
            job.attempt = attempt
        await session.commit()


def _tail(text: str, n: int = 40) -> str:
    """Return the last *n* lines of *text*."""
    lines = text.strip().splitlines()
    return "\n".join(lines[-n:])


def _build_exposea_config_yaml(job: StitchJob) -> str:
    """
    Build the Exposea YAML config as a raw string so that
    corner_coords stays inline  [[x,y],[x,y],...]
    and save_format is quoted    'tif'
    """
    corner_coords = json.loads(job.corner_points)
    final_res = [job.final_res_height, job.final_res_width]

    # Format lists as compact JSON-style inline arrays
    corner_str = json.dumps(corner_coords, separators=(",", ",")).replace(",", ", ").replace("],", "], ")
    # fix: restore the inner separators correctly
    corner_str = "[" + ", ".join(json.dumps(pt) for pt in corner_coords) + "]"
    final_res_str = json.dumps(final_res)

    return (
        f"exp_name: {job.exp_name}\n"
        f"ref_name: {job.ref_name}\n"
        f"preset_name: {job.preset_name}\n"
        f"save_format: '{job.save_format}'\n"
        f"final_res: {final_res_str}\n"
        f"corner_coords: {corner_str}\n"
        f"relative_scale: {int(job.relative_scale)}\n"
        f"\n"
        f"metrics:\n"
        f"  calculate: True\n"
        f"\n"
        f"homog:\n"
        f'  save: "./homogs"\n'
    )


# ── preview generation ────────────────────────────────────────────

PREVIEW_MAX_PX = 2048  # longest edge of the JPEG preview


def _generate_preview(result_path: Path) -> bytes:
    """
    Convert *result_path* to a JPEG preview using ImageMagick.
    Handles formats Pillow cannot (e.g. SGILOG-compressed TIFF from Exposea).
    Runs synchronously; call via asyncio.to_thread.
    """
    import subprocess
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        subprocess.run(
            [
                "convert",
                str(result_path),
                "-gamma", "2.2",
                "-resize", f"{PREVIEW_MAX_PX}x{PREVIEW_MAX_PX}>",
                "-quality", "85",
                str(tmp_path),
            ],
            check=True,
            capture_output=True,
        )
        return tmp_path.read_bytes()
    finally:
        tmp_path.unlink(missing_ok=True)


# ── job processing ────────────────────────────────────────────────

_active_jobs: set[str] = set()  # job IDs currently being processed by this worker


async def process_job(job_id: str, msg_id: str, is_reclaim: bool = False) -> None:
    """
    Full lifecycle of a single stitch job:
      1. Load from DB
      2. Skip if canceled
      3. Mark RUNNING
      4. Download photos from S3
      5. Generate Exposea YAML config
      6. Run `python register.py -i <task_dir> -o <output_dir>` from EXPOSEA_PATH
      7. Upload result to S3
      8. Mark FINISHED or FAILED
    """
    # If the reclaim loop fires while this worker is already processing the same
    # job (Exposea is slow), skip without acking so the PEL entry stays alive.
    if is_reclaim and job_id in _active_jobs:
        logger.info("[%s] Job %s is already in progress – skipping reclaim", msg_id, job_id)
        return

    t0 = time.monotonic()
    logger.info("[%s] Processing job %s (reclaim=%s)", msg_id, job_id, is_reclaim)

    job = await _load_job(job_id)
    if job is None:
        logger.warning("[%s] Job %s not found in DB – acking and skipping", msg_id, job_id)
        await redis_service.ack(msg_id)
        return

    # Skip jobs that are no longer in a runnable state.
    if job.status not in ("queued", "running"):
        logger.info("[%s] Job %s has status '%s' – acking and skipping", msg_id, job_id, job.status)
        await redis_service.ack(msg_id)
        return

    _active_jobs.add(job_id)

    # Check max retries for reclaimed messages
    current_attempt = job.attempt + 1
    if is_reclaim and current_attempt > settings.max_retries:
        logger.warning(
            "[%s] Job %s exceeded max retries (%d) – marking FAILED",
            msg_id, job_id, settings.max_retries,
        )
        await _update_job(
            job_id,
            status="failed",
            finished_at=datetime.now(timezone.utc),
            error_message=f"Max retries exceeded ({settings.max_retries})",
            attempt=current_attempt,
        )
        await redis_service.ack(msg_id)
        return

    # ── Mark RUNNING ──────────────────────────────────────────────
    now = datetime.now(timezone.utc)
    await _update_job(job_id, status="running", started_at=now, attempt=current_attempt)

    work_root = Path(settings.work_dir) / job_id
    task_dir = work_root / "task"
    images_dir = task_dir / "images"
    output_dir = work_root / "output"

    try:
        # ── Validate Exposea path ─────────────────────────────────
        exposea_dir = Path(settings.exposea_path)
        register_py = exposea_dir / "register.py"
        if not register_py.is_file():
            raise RuntimeError(
                f"Exposea not found at {register_py}. "
                f"Set EXPOSEA_PATH env var to the correct directory."
            )

        # ── Prepare directories ───────────────────────────────────
        images_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        # ── Download photos from S3 ──────────────────────────────
        photo_ids = json.loads(job.photo_ids)
        async with async_session_maker() as session:
            for pid in photo_ids:
                photo = await photos_repository.get_photo(session, pid)
                if photo is None:
                    raise RuntimeError(f"Photo {pid} not found in DB")
                data = await s3_service.download_file(photo.s3_key)
                dest = images_dir / photo.original_name
                dest.write_bytes(data)
                logger.info("[%s] Downloaded %s (%d bytes)", msg_id, photo.original_name, len(data))

        # ── Generate Exposea YAML config ──────────────────────────
        config_yaml = _build_exposea_config_yaml(job)
        config_path = task_dir / "config.yaml"
        config_path.write_text(config_yaml)
        logger.info("[%s] Wrote config: %s", msg_id, config_path)

        # ── Run Exposea CLI ───────────────────────────────────────
        exposea_python = exposea_dir / "venv" / "bin" / "python3"
        if not exposea_python.is_file():
            exposea_python = Path("python3")  # fallback to system python
        cmd = [
            str(exposea_python), "register.py",
            "-i", str(task_dir),
            "-o", str(output_dir),
        ]
        logger.info("[%s] Running from %s: %s", msg_id, exposea_dir, " ".join(cmd))

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(exposea_dir),
        )
        stdout_b, stderr_b = await proc.communicate()
        stdout_str = stdout_b.decode(errors="replace")
        stderr_str = stderr_b.decode(errors="replace")

        if proc.returncode != 0:
            err_tail = _tail(stderr_str)
            raise RuntimeError(
                f"Exposea exited with code {proc.returncode}\n{err_tail}"
            )

        # ── Find and upload result ────────────────────────────────
        result_files = [
            f for f in output_dir.rglob("*") if f.is_file()
        ]
        if not result_files:
            raise RuntimeError("Exposea produced no output files")

        result_file = result_files[0]
        result_bytes = result_file.read_bytes()
        result_filename = f"{job.exp_name}{result_file.suffix}"
        s3_key = f"stitch-results/{job.project_id}/{job.id}/{result_filename}"
        await s3_service.upload_file(result_bytes, s3_key)
        logger.info("[%s] Uploaded result to s3://%s (%d bytes)", msg_id, s3_key, len(result_bytes))

        # ── Generate JPEG preview ─────────────────────────────────
        preview_s3_key: str | None = None
        try:
            preview_bytes = await asyncio.to_thread(_generate_preview, result_file)
            preview_s3_key = f"stitch-results/{job.project_id}/{job.id}/preview.jpg"
            await s3_service.upload_file(preview_bytes, preview_s3_key, content_type="image/jpeg")
            logger.info("[%s] Uploaded preview to s3://%s (%d bytes)", msg_id, preview_s3_key, len(preview_bytes))
        except Exception as prev_exc:
            logger.warning("[%s] Preview generation failed (non-fatal): %s", msg_id, prev_exc)

        # ── Mark FINISHED ─────────────────────────────────────────
        await _update_job(
            job_id,
            status="finished",
            finished_at=datetime.now(timezone.utc),
            result_s3_key=s3_key,
            preview_s3_key=preview_s3_key,
            error_message="",
        )
        await redis_service.ack(msg_id)
        elapsed = time.monotonic() - t0
        logger.info("[%s] Job %s FINISHED in %.1fs", msg_id, job_id, elapsed)

    except Exception as exc:
        logger.exception("[%s] Job %s FAILED: %s", msg_id, job_id, exc)
        await _update_job(
            job_id,
            status="failed",
            finished_at=datetime.now(timezone.utc),
            error_message=str(exc)[:2000],
        )
        await redis_service.ack(msg_id)

    finally:
        _active_jobs.discard(job_id)
        # Clean up working directory
        if work_root.exists():
            shutil.rmtree(work_root, ignore_errors=True)


# ── main loop ─────────────────────────────────────────────────────


async def reclaim_loop() -> None:
    """Periodically reclaim stale pending messages."""
    while True:
        await asyncio.sleep(45)  # ~30-60s cadence
        try:
            claimed = await redis_service.autoclaim_stale()
            for msg_id, fields in claimed:
                job_id = fields.get("job_id")
                if not job_id:
                    await redis_service.ack(msg_id)
                    continue
                await process_job(job_id, msg_id, is_reclaim=True)
        except Exception:
            logger.exception("Error in reclaim loop")


async def main() -> None:
    logger.info(
        "Starting worker '%s' | group='%s' | stream='%s' | exposea='%s'",
        settings.consumer_name,
        settings.consumer_group,
        settings.stream_key,
        settings.exposea_path,
    )

    # Ensure the stream and consumer group exist
    await redis_service.ensure_consumer_group()

    # Start the reclaim loop in the background
    reclaim_task = asyncio.create_task(reclaim_loop())

    try:
        while True:
            try:
                messages = await redis_service.read_messages(count=1)
                for msg_id, fields in messages:
                    job_id = fields.get("job_id")
                    if not job_id:
                        logger.warning("Message %s has no job_id – acking", msg_id)
                        await redis_service.ack(msg_id)
                        continue
                    await process_job(job_id, msg_id)
            except Exception:
                logger.exception("Error in consumer loop – retrying in 5s")
                await asyncio.sleep(5)
    finally:
        reclaim_task.cancel()
        await redis_service.close()


if __name__ == "__main__":
    asyncio.run(main())
