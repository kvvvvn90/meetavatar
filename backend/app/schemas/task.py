"""Task request/response schemas."""

from datetime import datetime
from pydantic import BaseModel


class TaskResponse(BaseModel):
    task_id: str
    avatar_id: str
    status: str
    progress: int
    message: str | None = None
    error: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}
