"""File storage abstraction.

Currently uses local filesystem. Can be swapped to S3/MinIO later
by implementing the same interface.
"""

import cv2
from pathlib import Path

from app.config import settings


class FileService:
    """Local filesystem storage."""

    @staticmethod
    def get_abs_path(rel_path: str) -> Path:
        return settings.storage_dir / rel_path

    @staticmethod
    def avatar_dir(avatar_id: str) -> Path:
        path = settings.storage_dir / "avatars" / avatar_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def generate_thumbnail(video_path: str, avatar_id: str) -> str | None:
        """Extract first frame from video as 256x256 thumbnail."""
        try:
            cap = cv2.VideoCapture(video_path)
            ret, frame = cap.read()
            cap.release()

            if not ret:
                return None

            # Center crop to square, then resize to 256x256
            h, w = frame.shape[:2]
            size = min(h, w)
            y0 = (h - size) // 2
            x0 = (w - size) // 2
            cropped = frame[y0 : y0 + size, x0 : x0 + size]
            resized = cv2.resize(cropped, (256, 256))

            rel_path = f"avatars/{avatar_id}/thumb.jpg"
            abs_path = settings.storage_dir / rel_path
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(abs_path), resized)

            return rel_path
        except Exception:
            return None
