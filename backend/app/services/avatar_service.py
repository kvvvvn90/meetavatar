"""Avatar business logic layer."""

import shutil
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.avatar import Avatar
from app.schemas.avatar import AvatarUpdate


class AvatarService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self) -> list[Avatar]:
        result = await self.db.execute(
            select(Avatar).order_by(Avatar.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, avatar_id: str) -> Avatar | None:
        return await self.db.get(Avatar, avatar_id)

    async def create(self, name: str) -> Avatar:
        avatar = Avatar(name=name)
        self.db.add(avatar)
        await self.db.commit()
        await self.db.refresh(avatar)

        # Create avatar directory
        avatar_dir = settings.storage_dir / "avatars" / avatar.id
        avatar_dir.mkdir(parents=True, exist_ok=True)

        return avatar

    async def update(self, avatar: Avatar, data: AvatarUpdate) -> Avatar:
        if data.name is not None:
            avatar.name = data.name
        await self.db.commit()
        await self.db.refresh(avatar)
        return avatar

    async def delete(self, avatar: Avatar):
        # Delete files
        avatar_dir = settings.storage_dir / "avatars" / avatar.id
        if avatar_dir.exists():
            shutil.rmtree(avatar_dir, ignore_errors=True)

        await self.db.delete(avatar)
        await self.db.commit()

    async def set_source_photo(self, avatar: Avatar, rel_path: str) -> Avatar:
        avatar.source_photo_path = rel_path
        await self.db.commit()
        await self.db.refresh(avatar)
        return avatar

    async def set_driving_video(self, avatar: Avatar, rel_path: str) -> Avatar:
        avatar.driving_video_path = rel_path
        await self.db.commit()
        await self.db.refresh(avatar)
        return avatar

    async def set_loop_video(self, avatar: Avatar, rel_path: str) -> Avatar:
        avatar.loop_video_path = rel_path
        avatar.status = "ready"
        await self.db.commit()
        await self.db.refresh(avatar)
        return avatar

    async def set_thumbnail(self, avatar: Avatar, rel_path: str) -> Avatar:
        avatar.thumbnail_path = rel_path
        await self.db.commit()
        await self.db.refresh(avatar)
        return avatar

    async def set_status(self, avatar: Avatar, status: str, error: str | None = None) -> Avatar:
        avatar.status = status
        avatar.error_message = error
        await self.db.commit()
        await self.db.refresh(avatar)
        return avatar
