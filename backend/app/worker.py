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
import math
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path


from .config import settings
from .database import async_session_maker
from .models.user import User as _User                          # noqa: F401 – register with SQLAlchemy
from .models.project import Project as _Project                  # noqa: F401
from .models.photo import Photo as _Photo                        # noqa: F401
from .models.project_member import ProjectMember as _PM          # noqa: F401
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
        if log_s3_key is not None:
            job.log_s3_key = log_s3_key
        if error_message is not None:
            job.error_message = error_message
        if attempt is not None:
            job.attempt = attempt
        await session.commit()


async def _update_job_tiles(
    job_id: str,
    *,
    tiles_s3_prefix: str,
    tiles_metadata: str,
) -> None:
    """Persist tile fields after successful tile generation."""
    async with async_session_maker() as session:
        job = await stitch_jobs_repository.get_stitch_job(session, job_id)
        if job is None:
            return
        job.tiles_s3_prefix = tiles_s3_prefix
        job.tiles_metadata = tiles_metadata
        job.tiles_ready = True
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


# ── tile generation ───────────────────────────────────────────────

TILE_SIZE = 256


def _generate_tiles_pil(src_path: Path, output_dir: Path) -> tuple[int, int, int]:
    """
    Generate a tile pyramid from *src_path* using Pillow.
    Falls back to ImageMagick for format conversion if Pillow can't open the file.
    Returns (width, height, max_zoom).
    """
    from PIL import Image
    import subprocess
    import tempfile

    # Try Pillow first; fall back to ImageMagick conversion for SGILOG TIFF etc.
    img = None
    tmp_png: Path | None = None
    try:
        img = Image.open(src_path)
        img.load()
    except Exception:
        # Convert via ImageMagick to a temporary PNG
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_png = Path(tmp.name)
        subprocess.run(
            ["convert", str(src_path), "-gamma", "2.2", str(tmp_png)],
            check=True,
            capture_output=True,
        )
        img = Image.open(tmp_png)
        img.load()

    try:
        width, height = img.size
        max_zoom = max(0, math.ceil(math.log2(max(width, height) / TILE_SIZE)))
        max_zoom = min(max_zoom, 10)  # cap at zoom 10

        for z in range(max_zoom + 1):
            scale = 2 ** (max_zoom - z)
            scaled_w = max(1, width // scale)
            scaled_h = max(1, height // scale)
            scaled = img.resize((scaled_w, scaled_h), Image.LANCZOS)
            cols = math.ceil(scaled_w / TILE_SIZE)
            rows = math.ceil(scaled_h / TILE_SIZE)
            for x in range(cols):
                for y in range(rows):
                    box = (
                        x * TILE_SIZE,
                        y * TILE_SIZE,
                        min((x + 1) * TILE_SIZE, scaled_w),
                        min((y + 1) * TILE_SIZE, scaled_h),
                    )
                    tile = Image.new("RGB", (TILE_SIZE, TILE_SIZE), (255, 255, 255))
                    cropped = scaled.crop(box)
                    tile.paste(cropped, (0, 0))
                    tile_path = output_dir / str(z) / str(x) / f"{y}.jpg"
                    tile_path.parent.mkdir(parents=True, exist_ok=True)
                    tile.save(tile_path, "JPEG", quality=85)
    finally:
        img.close()
        if tmp_png and tmp_png.exists():
            tmp_png.unlink(missing_ok=True)

    return width, height, max_zoom


# ── job processing ────────────────────────────────────────────────

_active_jobs: set[str] = set()  # job IDs currently being processed by this worker
_job_semaphore = asyncio.Semaphore(1)  # allow only 1 concurrent job per worker process


async def process_job(job_id: str, msg_id: str, is_reclaim: bool = False) -> None:
    """
Full lifecycle of a single stitch job:
      1. Load from DB
      2. Mark RUNNING
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
        _RESULT_SUFFIXES = {".tiff", ".tif", ".j2k", ".jp2"}
        result_files = [
            f for f in output_dir.rglob("*")
            if f.is_file() and f.suffix.lower() in _RESULT_SUFFIXES
        ]
        if not result_files:
            raise RuntimeError("Exposea produced no output files with expected extensions (.tiff, .tif, .j2k, .jp2)")

        result_file = result_files[0]
        result_bytes = result_file.read_bytes()
        result_filename = f"{job.exp_name}{result_file.suffix}"
        s3_key = f"stitch-results/{job.project_id}/{job.id}/{result_filename}"
        await s3_service.upload_file(result_bytes, s3_key)
        logger.info("[%s] Uploaded result to s3://%s (%d bytes)", msg_id, s3_key, len(result_bytes))

        # ── Mark FINISHED ─────────────────────────────────────────
        await _update_job(
            job_id,
            status="finished",
            finished_at=datetime.now(timezone.utc),
            result_s3_key=s3_key,
            error_message="",
        )

        # ── Generate tile pyramid ─────────────────────────────────
        try:
            tile_dir = work_root / "tiles"
            tile_dir.mkdir(parents=True, exist_ok=True)
            img_width, img_height, max_zoom = await asyncio.to_thread(
                _generate_tiles_pil, result_file, tile_dir
            )
            tiles_s3_prefix = f"stitch-tiles/{job.project_id}/{job.id}"

            # Upload all generated tile files to S3
            for tile_path in tile_dir.rglob("*.jpg"):
                rel = tile_path.relative_to(tile_dir)
                tile_s3_key = f"{tiles_s3_prefix}/{rel.as_posix()}"
                tile_bytes = tile_path.read_bytes()
                await s3_service.upload_file(tile_bytes, tile_s3_key, content_type="image/jpeg")

            # Build and upload metadata
            meta = {
                "width": img_width,
                "height": img_height,
                "tile_size": TILE_SIZE,
                "min_zoom": 0,
                "max_zoom": max_zoom,
                "tile_format": "jpg",
                "tiles_ready": True,
            }
            meta_bytes = json.dumps(meta).encode()
            await s3_service.upload_file(
                meta_bytes, f"{tiles_s3_prefix}/metadata.json", content_type="application/json"
            )

            await _update_job_tiles(
                job_id,
                tiles_s3_prefix=tiles_s3_prefix,
                tiles_metadata=json.dumps(meta),
            )
            logger.info(
                "[%s] Tile pyramid ready: %dx%d px, zoom 0-%d, prefix=%s",
                msg_id, img_width, img_height, max_zoom, tiles_s3_prefix,
            )
        except Exception as tile_exc:
            logger.warning("[%s] Tile generation failed (non-fatal): %s", msg_id, tile_exc)
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
                async with _job_semaphore:
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
                    async with _job_semaphore:
                        await process_job(job_id, msg_id)
            except Exception:
                logger.exception("Error in consumer loop – retrying in 5s")
                await asyncio.sleep(5)
    finally:
        reclaim_task.cancel()
        await redis_service.close()


if __name__ == "__main__":
    asyncio.run(main())
