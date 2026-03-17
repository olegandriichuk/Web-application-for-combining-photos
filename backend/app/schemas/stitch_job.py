from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Any
from datetime import datetime
from typing import Literal
from enum import Enum


class PresetName(str, Enum):
    """Allowed preset configuration names."""
    DEBUG = "debug"
    DEFAULT = "default"
    P_100MPX = "p_100mpx"
    P_200MPX = "p_200mpx"
    P_400MPX = "p_400mpx"
    P_NORMAL = "p_normal"


class SaveFormat(str, Enum):
    """Allowed output image formats."""
    JP2 = "jp2"
    J2K = "j2k"
    TIFF = "tiff"
    TIF = "tif"


class JobStatus(str, Enum):
    """Job status values."""
    QUEUED = "queued"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
    CANCELED = "canceled"


class StitchJobCreate(BaseModel):
    """Schema for creating a new stitch job."""

    photo_ids: list[str] = Field(
        ...,
        min_length=1,
        description="Array of photo IDs to include in the stitch"
    )
    exp_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name under which the output result will be stored"
    )
    ref_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the reference image file in the project images folder"
    )
    preset_name: PresetName = Field(
        ...,
        description="Name of the preset configuration (without .yaml extension)"
    )
    final_res: list[int] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Target resolution [height, width] in pixels"
    )
    save_format: SaveFormat = Field(
        ...,
        description="Output image format"
    )
    corner_points: list[list[int]] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="List of 4 corner points [[w,h], ...]"
    )
    relative_scale: float = Field(
        ...,
        gt=0,
        description="Scale multiplier for image fragments relative to reference"
    )

    @field_validator("final_res")
    @classmethod
    def validate_final_res(cls, v: list[int]) -> list[int]:
        if len(v) != 2:
            raise ValueError("final_res must contain exactly 2 integers [height, width]")
        if any(x <= 0 for x in v):
            raise ValueError("Resolution values must be positive integers")
        return v

    @field_validator("corner_points")
    @classmethod
    def validate_corner_points(cls, v: list[list[int]]) -> list[list[int]]:
        if len(v) != 4:
            raise ValueError("corner_points must contain exactly 4 points")
        for point in v:
            if len(point) != 2:
                raise ValueError("Each corner point must contain exactly 2 integers [width, height]")
        return v


class StitchJobOut(BaseModel):
    """Schema for stitch job output."""

    id: str
    project_id: str
    status: JobStatus
    exp_name: str
    ref_name: str
    preset_name: str
    final_res: list[int] = Field(description="[height, width]")
    save_format: str
    corner_points: list[list[int]]
    relative_scale: float
    photo_ids: list[str]
    attempt: int = 0
    created_at: datetime
    queued_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    ref_photo_id: str | None = None
    result_s3_key: str | None = None
    error_message: str | None = None
    tiles_s3_prefix: str | None = None
    tiles_metadata: str | None = None
    tiles_ready: bool = False

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def _from_orm(cls, data: Any) -> Any:
        """Handle ORM→schema field name differences when reading from attributes."""
        import json as _json
        if not isinstance(data, dict):
            # ORM object — extract the fields that differ
            return {
                "id": data.id,
                "project_id": data.project_id,
                "status": data.status,
                "exp_name": data.exp_name,
                "ref_name": data.ref_name,
                "preset_name": data.preset_name,
                "final_res": [data.final_res_height, data.final_res_width],
                "save_format": data.save_format,
                "corner_points": _json.loads(data.corner_points),
                "relative_scale": data.relative_scale,
                "photo_ids": _json.loads(data.photo_ids),
                "attempt": data.attempt,
                "created_at": data.created_at,
                "queued_at": data.queued_at,
                "started_at": data.started_at,
                "finished_at": data.finished_at,
                "ref_photo_id": data.ref_photo_id,
                "result_s3_key": data.result_s3_key,
                "error_message": data.error_message,
                "tiles_s3_prefix": data.tiles_s3_prefix,
                "tiles_metadata": data.tiles_metadata,
                "tiles_ready": data.tiles_ready,
            }
        return data


class TileMetadataOut(BaseModel):
    """Metadata for the Leaflet tile viewer."""

    width: int
    height: int
    tile_size: int
    min_zoom: int
    max_zoom: int
    tile_format: str
    tiles_ready: bool


class StitchJobListQuery(BaseModel):
    """Query parameters for listing stitch jobs."""

    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(20, ge=1, le=100, description="Items per page")
    status: JobStatus | None = Field(None, description="Filter by status")
    from_date: datetime | None = Field(None, alias="from", description="Filter by start date (from)")
    to_date: datetime | None = Field(None, alias="to", description="Filter by start date (to)")
    sort: Literal["startDateDesc", "startDateAsc"] = Field(
        "startDateDesc",
        description="Sort order"
    )


class StitchJobListResponse(BaseModel):
    """Paginated response for stitch job list."""

    items: list[StitchJobOut]
    total: int
    page: int
    limit: int
    pages: int
