# Author: Oleg Andriichuk, xandri07
# Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

import logging
from ..config import settings

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None

logger = logging.getLogger(__name__)


class RedisService:
    """Async Redis client for Redis Streams job queue management."""

    def __init__(self):
        self._client = None
        self._enabled = REDIS_AVAILABLE and settings.redis_enabled

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def get_client(self):
        if not self._enabled:
            return None
        if self._client is None:
            self._client = aioredis.from_url(
                settings.redis_url,
                decode_responses=True,
                ssl_cert_reqs=None,
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None

    # ── Consumer group setup ──────────────────────────────────────

    async def ensure_consumer_group(self) -> bool:
        """
        Create the stream + consumer group if they don't exist.
        Returns True if ready, False if Redis is disabled.
        """
        if not self._enabled:
            return False
        client = await self.get_client()
        try:
            await client.xgroup_create(
                settings.stream_key,
                settings.consumer_group,
                id="0",
                mkstream=True,
            )
            logger.info(
                "Created consumer group '%s' on stream '%s'",
                settings.consumer_group,
                settings.stream_key,
            )
        except Exception as e:
            # BUSYGROUP = group already exists → safe to ignore
            if "BUSYGROUP" in str(e):
                logger.debug("Consumer group '%s' already exists", settings.consumer_group)
            else:
                raise
        return True

    # ── Producer ──────────────────────────────────────────────────

    async def enqueue_stitch_job(self, job_id: str) -> str | None:
        """
        XADD a job message to the stream.
        Returns the stream message ID, or None if Redis is disabled.
        """
        if not self._enabled:
            return None
        try:
            client = await self.get_client()
            message_id = await client.xadd(
                settings.stream_key,
                {"job_id": str(job_id)},
                maxlen=10000,
                approximate=True,
            )
            logger.info("Enqueued job %s → message %s", job_id, message_id)
            return message_id
        except Exception as e:
            logger.error("Redis enqueue failed for job %s: %s", job_id, e)
            return None

    # ── Consumer ──────────────────────────────────────────────────

    async def read_messages(self, count: int = 1) -> list[tuple[str, dict]]:
        """
        XREADGROUP for new messages ('>').
        Returns list of (message_id, fields) tuples.
        """
        client = await self.get_client()
        if client is None:
            return []
        response = await client.xreadgroup(
            settings.consumer_group,
            settings.consumer_name,
            {settings.stream_key: ">"},
            count=count,
            block=settings.block_ms,
        )
        if not response:
            return []
        # response: [[stream_name, [(msg_id, fields), ...]]]
        messages = []
        for _stream_name, stream_messages in response:
            for msg_id, fields in stream_messages:
                messages.append((msg_id, fields))
        return messages

    async def ack(self, message_id: str) -> None:
        """XACK a processed message."""
        client = await self.get_client()
        if client:
            await client.xack(settings.stream_key, settings.consumer_group, message_id)

    # ── Distributed lock ──────────────────────────────────────────

    # Short TTL: the heartbeat refreshes it every 3 min while the job runs.
    # After a crash (no heartbeat) it expires on its own within this window,
    # allowing another worker to pick up the job at the next reclaim cycle.
    LOCK_TTL_SECONDS = 600  # 10 minutes

    async def acquire_job_lock(self, job_id: str) -> bool:
        """
        Acquire an exclusive lock for job_id using SET NX EX.
        Returns True if the lock was acquired, False if another worker holds it.
        If Redis is disabled, always returns True (single-worker assumption).
        """
        client = await self.get_client()
        if client is None:
            return True
        key = f"job:{job_id}:lock"
        result = await client.set(key, settings.consumer_name, nx=True, ex=self.LOCK_TTL_SECONDS)
        return result is not None

    async def refresh_job_lock(self, job_id: str) -> None:
        """
        Reset the lock TTL if this worker still owns it (atomic Lua EXPIRE).
        Called by the heartbeat loop every HEARTBEAT_INTERVAL seconds.
        """
        client = await self.get_client()
        if client is None:
            return
        lua = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("expire", KEYS[1], ARGV[2])
        else
            return 0
        end
        """
        try:
            await client.eval(
                lua, 1, f"job:{job_id}:lock", settings.consumer_name, str(self.LOCK_TTL_SECONDS)
            )
        except Exception as exc:
            logger.warning("Failed to refresh lock for job %s: %s", job_id, exc)

    async def refresh_message_claim(self, msg_id: str) -> None:
        """
        Reset the PEL idle timer by reclaiming the message to ourselves.
        Called by the heartbeat loop so XAUTOCLAIM does not reclaim a job
        that is still actively running.
        """
        client = await self.get_client()
        if client is None:
            return
        try:
            await client.xclaim(
                settings.stream_key,
                settings.consumer_group,
                settings.consumer_name,
                min_idle_time=0,  # claim regardless of idle time
                message_ids=[msg_id],
            )
        except Exception as exc:
            logger.warning("Failed to refresh claim for message %s: %s", msg_id, exc)

    async def release_job_lock(self, job_id: str) -> None:
        """
        Release the lock only if this worker owns it (atomic Lua check-and-delete).
        Safe to call even if the lock has already expired or was never acquired.
        """
        client = await self.get_client()
        if client is None:
            return
        lua = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        try:
            await client.eval(lua, 1, f"job:{job_id}:lock", settings.consumer_name)
        except Exception:
            pass  # lock expired or Redis unavailable — safe to ignore

    # ── Pending reclaim ───────────────────────────────────────────

    async def autoclaim_stale(self) -> list[tuple[str, dict]]:
        """
        Reclaim messages that have been pending longer than CLAIM_IDLE_MS.
        Uses XAUTOCLAIM if available, falls back to XPENDING + XCLAIM.
        Returns list of (message_id, fields) tuples.
        """
        client = await self.get_client()
        if client is None:
            return []
        try:
            return await self._xautoclaim(client)
        except Exception as e:
            if "unknown command" in str(e).lower() or "unknown subcommand" in str(e).lower():
                logger.info("XAUTOCLAIM not available, using XPENDING+XCLAIM fallback")
                return await self._xpending_xclaim_fallback(client)
            raise

    async def _xautoclaim(self, client) -> list[tuple[str, dict]]:
        """Use XAUTOCLAIM (Redis >= 6.2)."""
        result = await client.xautoclaim(
            settings.stream_key,
            settings.consumer_group,
            settings.consumer_name,
            min_idle_time=settings.claim_idle_ms,
            start_id="0-0",
            count=10,
        )
        # result: (next_start_id, [(msg_id, fields), ...], [deleted_ids])
        # or     (next_start_id, [(msg_id, fields), ...]) in older redis-py
        if not result:
            return []
        claimed = result[1] if len(result) >= 2 else []
        return [(msg_id, fields) for msg_id, fields in claimed if fields]

    async def _xpending_xclaim_fallback(self, client) -> list[tuple[str, dict]]:
        """Fallback: XPENDING to find stale entries, then XCLAIM them."""
        pending = await client.xpending_range(
            settings.stream_key,
            settings.consumer_group,
            min="-",
            max="+",
            count=10,
        )
        if not pending:
            return []
        stale_ids = [
            entry["message_id"]
            for entry in pending
            if entry.get("time_since_delivered", 0) >= settings.claim_idle_ms
        ]
        if not stale_ids:
            return []
        claimed = await client.xclaim(
            settings.stream_key,
            settings.consumer_group,
            settings.consumer_name,
            min_idle_time=settings.claim_idle_ms,
            message_ids=stale_ids,
        )
        return [(msg_id, fields) for msg_id, fields in claimed if fields]


redis_service = RedisService()
