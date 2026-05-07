# Author: Oleg Andriichuk, xandri07
# Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

from datetime import datetime
from pydantic import BaseModel


class PhotoOut(BaseModel):
    id: str
    original_name: str
    mime: str
    size: int
    created_at: datetime
    preview_url: str | None = None
    original_width: int | None = None
    original_height: int | None = None

    model_config = {"from_attributes": True}
