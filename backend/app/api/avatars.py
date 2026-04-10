"""Avatar CRUD + file upload + generation trigger endpoints."""

import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas.avatar import (
    AvatarCreate,
    AvatarUpdate,
    AvatarResponse,
    AvatarListResponse,
    GenerateRequest,
    GenerateResponse,
)
from app.services.avatar_service import AvatarService
from app.services.generation_service import GenerationService

router = APIRouter()


def _to_response(avatar) -> AvatarResponse:
    """Convert ORM Avatar to response schema with URLs."""
    base = "/api/files"
    return AvatarResponse(
        id=avatar.id,
        name=avatar.name,
        status=avatar.status,
        source_photo_url=f"{base}/{avatar.source_photo_path}" if avatar.source_photo_path else None,
        driving_video_url=f"{base}/{avatar.driving_video_path}" if avatar.driving_video_path else None,
        loop_video_url=f"{base}/{avatar.loop_video_path}" if avatar.loop_video_path else None,
        thumbnail_url=f"{base}/{avatar.thumbnail_path}" if avatar.thumbnail_path else None,
        error_message=avatar.error_message,
        created_at=avatar.created_at,
        updated_at=avatar.updated_at,
    )


@router.get("", response_model=AvatarListResponse)
async def list_avatars(db: AsyncSession = Depends(get_db)):
    service = AvatarService(db)
    avatars = await service.list_all()
    return AvatarListResponse(avatars=[_to_response(a) for a in avatars])


@router.post("", response_model=AvatarResponse, status_code=201)
async def create_avatar(data: AvatarCreate, db: AsyncSession = Depends(get_db)):
    service = AvatarService(db)
    avatar = await service.create(data.name)
    return _to_response(avatar)


@router.get("/{avatar_id}", response_model=AvatarResponse)
async def get_avatar(avatar_id: str, db: AsyncSession = Depends(get_db)):
    service = AvatarService(db)
    avatar = await service.get(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return _to_response(avatar)


@router.patch("/{avatar_id}", response_model=AvatarResponse)
async def update_avatar(
    avatar_id: str, data: AvatarUpdate, db: AsyncSession = Depends(get_db)
):
    service = AvatarService(db)
    avatar = await service.get(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    avatar = await service.update(avatar, data)
    return _to_response(avatar)


@router.delete("/{avatar_id}", status_code=204)
async def delete_avatar(avatar_id: str, db: AsyncSession = Depends(get_db)):
    service = AvatarService(db)
    avatar = await service.get(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    await service.delete(avatar)


@router.post("/{avatar_id}/source-photo")
async def upload_source_photo(
    avatar_id: str,
    photo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    service = AvatarService(db)
    avatar = await service.get(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")

    # Save uploaded file
    suffix = Path(photo.filename).suffix or ".jpg"
    rel_path = f"avatars/{avatar_id}/source{suffix}"
    abs_path = settings.storage_dir / rel_path
    abs_path.parent.mkdir(parents=True, exist_ok=True)

    with open(abs_path, "wb") as f:
        shutil.copyfileobj(photo.file, f)

    avatar = await service.set_source_photo(avatar, rel_path)
    return {"source_photo_url": f"/api/files/{rel_path}"}


@router.post("/{avatar_id}/driving-video")
async def upload_driving_video(
    avatar_id: str,
    video: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    service = AvatarService(db)
    avatar = await service.get(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")

    suffix = Path(video.filename).suffix or ".mp4"
    rel_path = f"avatars/{avatar_id}/driving{suffix}"
    abs_path = settings.storage_dir / rel_path
    abs_path.parent.mkdir(parents=True, exist_ok=True)

    with open(abs_path, "wb") as f:
        shutil.copyfileobj(video.file, f)

    avatar = await service.set_driving_video(avatar, rel_path)
    return {"driving_video_url": f"/api/files/{rel_path}"}


@router.post("/{avatar_id}/generate", response_model=GenerateResponse, status_code=202)
async def start_generation(
    avatar_id: str,
    data: GenerateRequest = GenerateRequest(),
    db: AsyncSession = Depends(get_db),
):
    service = AvatarService(db)
    avatar = await service.get(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    if not avatar.driving_video_path:
        raise HTTPException(status_code=400, detail="Driving video not uploaded")

    gen_service = GenerationService(db)
    task = await gen_service.enqueue(avatar, data)
    return GenerateResponse(task_id=task.id, status=task.status)


@router.get("/{avatar_id}/loop-video")
async def download_loop_video(avatar_id: str, db: AsyncSession = Depends(get_db)):
    service = AvatarService(db)
    avatar = await service.get(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    if not avatar.loop_video_path:
        raise HTTPException(status_code=404, detail="Loop video not generated yet")

    abs_path = settings.storage_dir / avatar.loop_video_path
    if not abs_path.exists():
        raise HTTPException(status_code=404, detail="Loop video file not found")

    return FileResponse(
        path=str(abs_path),
        media_type="video/mp4",
        filename=f"{avatar.name}_loop.mp4",
    )
