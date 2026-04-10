"""Top-level API router aggregating sub-routers."""

from fastapi import APIRouter

from app.api.avatars import router as avatars_router
from app.api.tasks import router as tasks_router

api_router = APIRouter()
api_router.include_router(avatars_router, prefix="/avatars", tags=["avatars"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
