from sqlalchemy import String, Text, DateTime, Integer, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base
import uuid


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    region: Mapped[str | None] = mapped_column(String(200), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    document_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    institution: Mapped[str | None] = mapped_column(String(200), nullable=True)
    collection: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_private: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="projects")
    photos = relationship(
        "Photo",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    members = relationship(
        "ProjectMember",
        back_populates="project",
        cascade="all, delete-orphan"
    )
