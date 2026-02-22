from ..config import settings

# Redis is optional - only import if available
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class RedisService:
    """Async Redis client service for job queue management. Optional - works without Redis."""

    def __init__(self):
        self._client = None
        self._enabled = REDIS_AVAILABLE and settings.redis_enabled

    async def get_client(self):
        """Get or create Redis client connection."""
        if not self._enabled:
            return None

        if self._client is None:
            self._client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password,
                decode_responses=True
            )
        return self._client

    async def close(self):
        """Close the Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None

    async def enqueue_stitch_job(self, job_id: str, project_id: str) -> str | None:
        """
        Enqueue a stitch job to Redis Streams.

        Uses XADD to add a message to the 'jobs:exposea' stream.
        Workers consume using XREADGROUP.

        Returns the message ID, or None if Redis is disabled.
        """
        if not self._enabled:
            return None

        try:
            client = await self.get_client()
            if client is None:
                return None

            message_id = await client.xadd(
                "jobs:exposea",
                {"job_id": job_id, "project_id": project_id}
            )
            return message_id
        except Exception as e:
            # Redis connection failed - log and continue
            print(f"Redis enqueue skipped (not available): {e}")
            return None


# Singleton instance
redis_service = RedisService()
