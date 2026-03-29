import os
import socket

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_consumer_name() -> str:
    return f"{socket.gethostname()}-{os.getpid()}"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # JWT Configuration
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # AWS S3 Configuration
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str = "eu-north-1"
    s3_bucket_name: str

    # Optional: for local development with localstack
    aws_endpoint_url: str | None = None

    # Database
    database_url: str = "sqlite+aiosqlite:///./app.db"

    # Redis Configuration (optional - set redis_enabled=true to use)
    redis_enabled: bool = False
    redis_url: str = "redis://localhost:6379/0"

    # Exposea
    exposea_path: str = "/home/makaroni/Exposea"

    # Redis Streams / Worker Configuration
    stream_key: str = "stitch:jobs"
    consumer_group: str = "stitch-workers"
    consumer_name: str = Field(default_factory=_default_consumer_name)
    block_ms: int = 5000
    claim_idle_ms: int = 900000   # 15 minutes (heartbeat resets PEL idle timer every 3 min)
    max_retries: int = 3
    work_dir: str = "/tmp/stitch_worker"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
