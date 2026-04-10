"""System tray application for MeetAvatar camera client."""

import logging
import threading
from typing import Callable

import pystray
from PIL import Image, ImageDraw

from .config import Config
from .downloader import download_loop_video, fetch_avatars
from .virtual_cam import VirtualCamera

logger = logging.getLogger(__name__)

# Icon dimensions
_ICON_SIZE = 64


def _create_icon_image(running: bool = False) -> Image.Image:
    """Create a simple tray icon.

    Green circle when camera is running, grey when idle.
    """
    img = Image.new("RGBA", (_ICON_SIZE, _ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    fill = (76, 175, 80, 255) if running else (158, 158, 158, 255)
    draw.ellipse([4, 4, 60, 60], fill=fill, outline=(255, 255, 255, 255), width=2)
    # Simple camera lens indicator
    draw.ellipse([20, 20, 44, 44], fill=(255, 255, 255, 200))
    draw.ellipse([26, 26, 38, 38], fill=(50, 50, 50, 255))
    return img


class TrayApp:
    """System tray application that manages virtual camera output."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._vcam = VirtualCamera()
        self._icon: pystray.Icon | None = None
        self._current_avatar_id: str | None = None
        self._current_avatar_name: str | None = None
        self._cached_video_path: str | None = None

    # ------------------------------------------------------------------
    # Menu construction
    # ------------------------------------------------------------------

    def _build_menu(self) -> pystray.Menu:
        """Build the context menu for the tray icon."""
        return pystray.Menu(
            pystray.MenuItem("Select Avatar", self._build_avatar_submenu()),
            pystray.MenuItem(
                lambda _: "Stop Camera" if self._vcam.is_running else "Start Camera",
                self._on_toggle_camera,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                lambda _: f"Avatar: {self._current_avatar_name or '(none)'}",
                None,
                enabled=False,
            ),
            pystray.MenuItem(
                f"Server: {self._config.server_url}",
                None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._on_quit),
        )

    def _build_avatar_submenu(self) -> Callable:
        """Return a callable that lazily builds the avatar submenu."""

        def _submenu_factory() -> list[pystray.MenuItem]:
            try:
                avatars = fetch_avatars(self._config.server_url)
            except Exception as exc:
                logger.error("Failed to fetch avatars: %s", exc)
                return [
                    pystray.MenuItem(
                        f"Error: {exc}",
                        None,
                        enabled=False,
                    )
                ]

            if not avatars:
                return [pystray.MenuItem("No avatars available", None, enabled=False)]

            items = []
            for avatar in avatars:
                avatar_id = str(avatar.get("id", ""))
                avatar_name = avatar.get("name", avatar_id)
                items.append(
                    pystray.MenuItem(
                        avatar_name,
                        self._make_avatar_handler(avatar_id, avatar_name),
                        checked=lambda item, aid=avatar_id: self._current_avatar_id == aid,
                    )
                )
            return items

        return _submenu_factory

    def _make_avatar_handler(
        self, avatar_id: str, avatar_name: str
    ) -> Callable:
        """Create a click handler for selecting a specific avatar."""

        def handler(icon: pystray.Icon, item: pystray.MenuItem) -> None:
            self._select_avatar(avatar_id, avatar_name)

        return handler

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _select_avatar(self, avatar_id: str, avatar_name: str) -> None:
        """Select an avatar and download its loop video."""
        logger.info("Selecting avatar: %s (%s)", avatar_name, avatar_id)
        self._current_avatar_id = avatar_id
        self._current_avatar_name = avatar_name

        def _download() -> None:
            try:
                path = download_loop_video(
                    self._config.server_url,
                    avatar_id,
                    self._config.cache_dir,
                )
                self._cached_video_path = path
                logger.info("Avatar video ready: %s", path)

                # If camera is running, restart with new video
                if self._vcam.is_running:
                    self._vcam.start(
                        path,
                        self._config.width,
                        self._config.height,
                        self._config.fps,
                    )
                    self._update_icon()
            except Exception as exc:
                logger.error("Download failed for avatar '%s': %s", avatar_name, exc)

        threading.Thread(target=_download, name="AvatarDownload", daemon=True).start()

    def _on_toggle_camera(
        self, icon: pystray.Icon, item: pystray.MenuItem
    ) -> None:
        """Start or stop the virtual camera."""
        if self._vcam.is_running:
            self._vcam.stop()
            self._update_icon()
            logger.info("Camera stopped by user")
        else:
            if not self._cached_video_path:
                logger.warning("No avatar video selected; cannot start camera")
                return
            self._vcam.start(
                self._cached_video_path,
                self._config.width,
                self._config.height,
                self._config.fps,
            )
            self._update_icon()
            logger.info("Camera started by user")

    def _on_quit(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Quit the application."""
        logger.info("Quit requested")
        self._vcam.stop()
        icon.stop()

    def _update_icon(self) -> None:
        """Update the tray icon to reflect current state."""
        if self._icon is not None:
            self._icon.icon = _create_icon_image(running=self._vcam.is_running)

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start the system tray application (blocks until quit)."""
        logger.info(
            "Starting MeetAvatar tray app (server=%s)", self._config.server_url
        )
        self._icon = pystray.Icon(
            name="MeetAvatar",
            icon=_create_icon_image(running=False),
            title="MeetAvatar Camera",
            menu=self._build_menu(),
        )
        self._icon.run()
