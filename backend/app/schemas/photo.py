from pydantic import BaseModel

class PhotoOut(BaseModel):
    id: str
    original_name: str
    mime: str
    size: int
    created_at: str

    class Config:
        from_attributes = True
