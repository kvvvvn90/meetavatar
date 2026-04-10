"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables (dev only; use alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Ensure storage directory exists
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    (settings.storage_dir / "avatars").mkdir(parents=True, exist_ok=True)

    yield

    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="MeetAvatar API",
    version="0.1.0",
    description="Digital avatar generation service for virtual meetings",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for avatar assets
app.mount(
    "/api/files",
    StaticFiles(directory=str(settings.storage_dir)),
    name="files",
)

# Register API routers
from app.api.router import api_router  # noqa: E402

app.include_router(api_router, prefix="/api")
