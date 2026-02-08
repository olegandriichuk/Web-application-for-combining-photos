from datetime import datetime
from pydantic import BaseModel


class PhotoOut(BaseModel):
    id: str
    original_name: str
    mime: str
    size: int
    created_at: datetime

    model_config = {"from_attributes": True}
