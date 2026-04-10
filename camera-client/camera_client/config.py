"""Configuration for the MeetAvatar camera client."""

import os
from dataclasses import dataclass, field
from pathlib import Path


def _default_cache_dir() -> str:
    return str(Path.home() / ".meetavatar" / "cache")


@dataclass
class Config:
    """Application configuration with sensible defaults."""

    server_url: str = "http://localhost:8000"
    cache_dir: str = field(default_factory=_default_cache_dir)
    width: int = 1280
    height: int = 720
    fps: int = 30

    def __post_init__(self) -> None:
        # Strip trailing slash from server URL
        self.server_url = self.server_url.rstrip("/")
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
