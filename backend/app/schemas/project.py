# Author: Oleg Andriichuk, xandri07
# Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal


DocumentType = Literal["Map", "Aerial photo", "Technical drawing", "Plan", "Other"]


class ProjectCreate(BaseModel):
    """Schema for creating a new project"""
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    region: str | None = Field(None, max_length=200)
    year: int | None = None
    document_type: DocumentType | None = None
    institution: str | None = Field(None, max_length=200)
    collection: str | None = Field(None, max_length=200)
    is_private: bool = False


class ProjectUpdate(BaseModel):
    """Schema for updating a project"""
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    region: str | None = Field(None, max_length=200)
    year: int | None = None
    document_type: DocumentType | None = None
    institution: str | None = Field(None, max_length=200)
    collection: str | None = Field(None, max_length=200)
    is_private: bool | None = None


class ProjectOut(BaseModel):
    """Schema for project output"""
    id: str
    user_id: str
    name: str
    description: str | None
    region: str | None
    year: int | None
    document_type: str | None
    institution: str | None
    collection: str | None
    is_private: bool
    created_at: datetime
    role: str

    class Config:
        from_attributes = True


class ProjectWithPhotoCount(BaseModel):
    """Schema for project with photo count"""
    id: str
    user_id: str
    name: str
    description: str | None
    region: str | None
    year: int | None
    document_type: str | None
    institution: str | None
    collection: str | None
    is_private: bool
    created_at: datetime
    photo_count: int
    role: str

    class Config:
        from_attributes = True
