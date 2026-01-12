from pydantic import BaseModel, Field
from datetime import datetime


class ProjectCreate(BaseModel):
    """Schema for creating a new project"""
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)


class ProjectUpdate(BaseModel):
    """Schema for updating a project"""
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)


class ProjectOut(BaseModel):
    """Schema for project output"""
    id: str
    user_id: str
    name: str
    description: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectWithPhotoCount(BaseModel):
    """Schema for project with photo count"""
    id: str
    user_id: str
    name: str
    description: str | None
    created_at: datetime
    photo_count: int

    class Config:
        from_attributes = True
