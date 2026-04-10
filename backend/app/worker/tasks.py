"""ARQ task definitions and worker configuration."""

import logging
from arq import create_pool
from arq.connections import RedisSettings

from app.config import settings

logger = logging.getLogger(__name__)

# Parse redis URL for ARQ settings
_redis_url = settings.redis_url
_host = _redis_url.split("://")[-1].split(":")[0] if "://" in _redis_url else "localhost"
_port = int(_redis_url.split(":")[-1].split("/")[0]) if _redis_url.count(":") >= 2 else 6379

REDIS_SETTINGS = RedisSettings(host=_host, port=_port)


async def enqueue_generation(task_id: str):
    """Enqueue a generation task to the ARQ worker."""
    redis = await create_pool(REDIS_SETTINGS)
    await redis.enqueue_job("run_generation", task_id)
    logger.info(f"Enqueued generation task: {task_id}")


async def run_generation(ctx: dict, task_id: str):
    """ARQ worker function — runs LivePortrait inference + loop making."""
    from app.worker.generate import execute_generation

    await execute_generation(task_id)


class WorkerSettings:
    """ARQ worker settings."""

    functions = [run_generation]
    redis_settings = REDIS_SETTINGS
    max_jobs = 1  # One GPU job at a time
    job_timeout = 600  # 10 minutes max per job
