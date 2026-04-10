"""HTTP downloader for avatar loop videos."""

import hashlib
import logging
import os
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)

# Timeout for API requests (connect, read) in seconds
_TIMEOUT = (10, 60)
_DOWNLOAD_TIMEOUT = (10, 300)


def fetch_avatars(server_url: str) -> list[dict[str, Any]]:
    """Fetch the list of available avatars from the backend.

    Args:
        server_url: Base URL of the MeetAvatar backend.

    Returns:
        List of avatar dicts, each containing at least 'id' and 'name'.

    Raises:
        requests.RequestException: On network or HTTP errors.
    """
    url = f"{server_url.rstrip('/')}/api/avatars"
    logger.info("Fetching avatar list from %s", url)

    resp = requests.get(url, timeout=_TIMEOUT)
    resp.raise_for_status()

    data = resp.json()
    avatars = data.get("avatars", data) if isinstance(data, dict) else data
    logger.info("Found %d avatar(s)", len(avatars))
    return avatars


def download_loop_video(
    server_url: str,
    avatar_id: str,
    cache_dir: str,
) -> str:
    """Download a loop video for the given avatar, with caching.

    If the file already exists in *cache_dir* it is returned immediately
    unless the server reports a different content-length (simple staleness
    check).

    Args:
        server_url: Base URL of the MeetAvatar backend.
        avatar_id: Identifier of the avatar whose loop video to download.
        cache_dir: Local directory for cached video files.

    Returns:
        Absolute path to the downloaded (or cached) video file.

    Raises:
        requests.RequestException: On network or HTTP errors.
    """
    url = f"{server_url.rstrip('/')}/api/avatars/{avatar_id}/loop-video"
    safe_id = hashlib.sha256(avatar_id.encode()).hexdigest()[:16]
    dest = os.path.join(cache_dir, f"{safe_id}_loop.mp4")

    # Check if cached file is still valid
    if os.path.isfile(dest):
        try:
            head = requests.head(url, timeout=_TIMEOUT)
            head.raise_for_status()
            remote_size = int(head.headers.get("content-length", 0))
            local_size = os.path.getsize(dest)
            if remote_size > 0 and remote_size == local_size:
                logger.info("Using cached video: %s", dest)
                return dest
        except requests.RequestException:
            logger.debug("HEAD check failed; re-downloading %s", avatar_id)

    logger.info("Downloading loop video for avatar '%s' ...", avatar_id)

    os.makedirs(cache_dir, exist_ok=True)

    resp = requests.get(url, stream=True, timeout=_DOWNLOAD_TIMEOUT)
    resp.raise_for_status()

    tmp_dest = dest + ".tmp"
    bytes_written = 0
    try:
        with open(tmp_dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1 << 16):
                f.write(chunk)
                bytes_written += len(chunk)
        # Atomic-ish rename
        if os.path.exists(dest):
            os.remove(dest)
        os.rename(tmp_dest, dest)
    except Exception:
        # Clean up partial file on failure
        if os.path.isfile(tmp_dest):
            os.remove(tmp_dest)
        raise

    logger.info(
        "Downloaded %s (%.1f MB)",
        dest,
        bytes_written / (1024 * 1024),
    )
    return dest
