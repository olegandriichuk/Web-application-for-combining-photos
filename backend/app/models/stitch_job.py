# Author: Oleg Andriichuk, xandri07
# Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class StitchJob(Base):
    """
    Represents a stitching job for Exposea.

    Status lifecycle: queued -> running -> finished | failed | canceled
    """
    __tablename__ = "stitch_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False
    )

    # Job status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="queued",
        index=True
    )

    # Retry tracking
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Stitching parameters
    exp_name: Mapped[str] = mapped_column(String(255), nullable=False)
    ref_name: Mapped[str] = mapped_column(String(255), nullable=False)
    preset_name: Mapped[str] = mapped_column(String(50), nullable=False)
    final_res_height: Mapped[int] = mapped_column(Integer, nullable=False)
    final_res_width: Mapped[int] = mapped_column(Integer, nullable=False)
    save_format: Mapped[str] = mapped_column(String(10), nullable=False)
    corner_points: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    relative_scale: Mapped[float] = mapped_column(Float, nullable=False)

    # Photo IDs (JSON array of photo IDs)
    photo_ids: Mapped[str] = mapped_column(Text, nullable=False)

    # Timestamps
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    queued_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    started_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    finished_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Reference photo ID (the photo used as the stitching reference)
    ref_photo_id: Mapped[str] = mapped_column(String(36), nullable=True)

    # Result storage
    result_s3_key: Mapped[str] = mapped_column(String(500), nullable=True)
    log_s3_key: Mapped[str] = mapped_column(String(500), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    # Tile pyramid (for Leaflet viewer)
    tiles_s3_prefix: Mapped[str] = mapped_column(String(500), nullable=True)
    tiles_metadata: Mapped[str] = mapped_column(Text, nullable=True)  # JSON string
    tiles_ready: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")

    # Relationships
    user = relationship("User")
    project = relationship("Project")
