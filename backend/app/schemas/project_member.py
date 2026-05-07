# Author: Oleg Andriichuk, xandri07
# Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

from pydantic import BaseModel


class ProjectMemberOut(BaseModel):
    user_id: str
    user_name: str
    user_email: str
    role: str

    class Config:
        from_attributes = True


class AddMemberRequest(BaseModel):
    email: str
    role: str  # validated in router: must be "editor" | "viewer"


class UpdateMemberRoleRequest(BaseModel):
    role: str  # validated in router: must be "editor" | "viewer"
