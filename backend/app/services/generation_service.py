"""Generation task orchestration — enqueue and track async tasks.

Supports two modes:
- local: runs generation directly in a background asyncio task (no Redis needed)
- production: enqueues to ARQ worker via Redis
"""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.avatar import Avatar
from app.models.task import GenerationTask
from app.schemas.avatar import GenerateRequest

logger = logging.getLogger(__name__)


class GenerationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def enqueue(self, avatar: Avatar, req: GenerateRequest) -> GenerationTask:
        """Create a generation task and dispatch it."""
        # Update avatar status
        avatar.status = "generating"
        await self.db.commit()

        # Create task record
        task = GenerationTask(
            avatar_id=avatar.id,
            status="queued",
            device=req.device,
            loop_method=req.loop_method,
            blend_frames=req.blend_frames,
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        if settings.is_local:
            # Local mode: run directly in background asyncio task
            logger.info(f"Local mode: launching generation in background for task {task.id}")
            asyncio.create_task(self._run_local(task.id))
        else:
            # Production mode: enqueue to ARQ worker via Redis
            from app.worker.tasks import enqueue_generation
            await enqueue_generation(task.id)

        return task

    async def _run_local(self, task_id: str):
        """Run generation directly in-process (local dev mode, no Redis/ARQ)."""
        from app.worker.generate import execute_generation

        try:
            await execute_generation(task_id)
        except Exception as e:
            logger.exception(f"Local generation failed for task {task_id}: {e}")

    async def get_task(self, task_id: str) -> GenerationTask | None:
        return await self.db.get(GenerationTask, task_id)

    async def update_progress(
        self,
        task_id: str,
        progress: int,
        message: str | None = None,
        status: str = "running",
    ):
        task = await self.db.get(GenerationTask, task_id)
        if task:
            task.status = status
            task.progress = progress
            task.message = message
            if status == "running" and not task.started_at:
                task.started_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def complete_task(self, task_id: str):
        task = await self.db.get(GenerationTask, task_id)
        if task:
            task.status = "completed"
            task.progress = 100
            task.message = "Generation complete"
            task.completed_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def fail_task(self, task_id: str, error: str):
        task = await self.db.get(GenerationTask, task_id)
        if task:
            task.status = "failed"
            task.error = error
            task.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
