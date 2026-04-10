"""Avatar request/response schemas."""

from datetime import datetime
from pydantic import BaseModel


class AvatarCreate(BaseModel):
    name: str


class AvatarUpdate(BaseModel):
    name: str | None = None


class AvatarResponse(BaseModel):
    id: str
    name: str
    status: str
    source_photo_url: str | None = None
    driving_video_url: str | None = None
    loop_video_url: str | None = None
    thumbnail_url: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AvatarListResponse(BaseModel):
    avatars: list[AvatarResponse]


class GenerateRequest(BaseModel):
    device: str = "cuda"
    loop_method: str = "palindrome"
    blend_frames: int = 15


class GenerateResponse(BaseModel):
    task_id: str
    status: str
