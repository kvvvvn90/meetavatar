"""Application configuration via environment variables."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Run mode: "local" (SQLite, in-process worker) or "production" (Postgres + Redis + ARQ)
    mode: str = "local"

    # Database — default is SQLite for local dev, no external service needed
    database_url: str = "sqlite+aiosqlite:///./storage/meetavatar.db"

    # Redis — only needed in production mode
    redis_url: str = "redis://localhost:6379"

    # File storage
    storage_dir: Path = Path("storage")

    # LivePortrait
    liveportrait_dir: Path = Path("../third_party/LivePortrait")
    pretrained_dir: Path | None = None  # defaults to liveportrait_dir / pretrained_weights

    # Server
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Generation defaults
    default_device: str = "cuda"
    default_loop_method: str = "palindrome"
    default_blend_frames: int = 15

    model_config = {"env_prefix": "MEETAVATAR_", "env_file": ".env"}

    @property
    def is_local(self) -> bool:
        return self.mode == "local"

    @property
    def pretrained_weights_dir(self) -> Path:
        if self.pretrained_dir:
            return self.pretrained_dir
        return self.liveportrait_dir / "pretrained_weights"


settings = Settings()
