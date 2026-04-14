"""Avatar gallery widget — grid of avatar cards with thumbnails."""

import logging
import os

from PyQt6.QtCore import QSize, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..config import Config
from ..downloader import download_loop_video, download_thumbnail, fetch_avatars

logger = logging.getLogger(__name__)

_CARD_STYLE = """
QListWidget {
    background-color: #181825;
    border: none;
    outline: none;
}
QListWidget::item {
    background-color: #313244;
    border-radius: 8px;
    margin: 4px;
    padding: 4px;
}
QListWidget::item:selected {
    background-color: #45475a;
    border: 1px solid #89b4fa;
}
QListWidget::item:hover {
    background-color: #45475a;
}
QPushButton {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: none;
    border-radius: 6px;
    padding: 6px 16px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton:hover { background-color: #74c7ec; }
QPushButton:pressed { background-color: #89dceb; }
QPushButton:disabled { background-color: #45475a; color: #6c7086; }
QLabel { color: #cdd6f4; }
"""


class _DownloadWorker(QThread):
    """Background thread for downloading avatar video + thumbnail."""

    finished = pyqtSignal(str, str, str, str)  # avatar_id, name, video_path, thumb_path
    error = pyqtSignal(str, str)  # avatar_id, error message

    def __init__(self, server_url: str, avatar_id: str, avatar_name: str, cache_dir: str):
        super().__init__()
        self._server_url = server_url
        self._avatar_id = avatar_id
        self._avatar_name = avatar_name
        self._cache_dir = cache_dir

    def run(self):
        try:
            video_path = download_loop_video(
                self._server_url, self._avatar_id, self._cache_dir
            )
            thumb_path = download_thumbnail(
                self._server_url, self._avatar_id, self._cache_dir
            )
            self.finished.emit(
                self._avatar_id, self._avatar_name, video_path, thumb_path
            )
        except Exception as exc:
            logger.exception("Download failed for %s", self._avatar_id)
            self.error.emit(self._avatar_id, str(exc))


class _FetchWorker(QThread):
    """Background thread for fetching avatar list from backend."""

    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, server_url: str):
        super().__init__()
        self._server_url = server_url

    def run(self):
        try:
            avatars = fetch_avatars(self._server_url)
            self.finished.emit(avatars)
        except Exception as exc:
            logger.exception("Failed to fetch avatars")
            self.error.emit(str(exc))


class AvatarGallery(QWidget):
    """Displays avatars from the backend in a list with download + select."""

    avatar_selected = pyqtSignal(str, str, str)  # id, name, video_path

    def __init__(self, config: Config) -> None:
        super().__init__()
        self._config = config
        self._workers: list[QThread] = []
        # avatar_id -> {name, video_path, thumb_path}
        self._local_avatars: dict[str, dict] = {}

        self.setStyleSheet(_CARD_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Avatars")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.setFixedWidth(80)
        self._refresh_btn.clicked.connect(self.refresh)
        header.addWidget(self._refresh_btn)

        layout.addLayout(header)

        # Avatar list
        self._list = QListWidget()
        self._list.setIconSize(QSize(80, 80))
        self._list.setSpacing(4)
        self._list.setWordWrap(True)
        self._list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self._list)

        # Use button
        self._use_btn = QPushButton("Use Selected")
        self._use_btn.setEnabled(False)
        self._use_btn.clicked.connect(self._on_use_clicked)
        layout.addWidget(self._use_btn)

        self._list.currentItemChanged.connect(self._on_selection_changed)

        # Initial fetch
        self.refresh()

    def refresh(self):
        """Fetch avatar list from backend."""
        self._refresh_btn.setEnabled(False)
        self._refresh_btn.setText("Loading...")
        worker = _FetchWorker(self._config.server_url)
        worker.finished.connect(self._on_avatars_fetched)
        worker.error.connect(self._on_fetch_error)
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        worker.error.connect(lambda: self._cleanup_worker(worker))
        self._workers.append(worker)
        worker.start()

    def _on_avatars_fetched(self, avatars: list):
        self._refresh_btn.setEnabled(True)
        self._refresh_btn.setText("Refresh")
        self._list.clear()

        for av in avatars:
            status = av.get("status", "")
            if status != "ready":
                continue
            avatar_id = str(av.get("id", ""))
            name = av.get("name", avatar_id)
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, avatar_id)
            item.setData(Qt.ItemDataRole.UserRole + 1, name)
            item.setSizeHint(QSize(0, 72))

            # Load cached thumbnail if available
            cached = self._local_avatars.get(avatar_id, {})
            thumb = cached.get("thumb_path", "")
            if thumb and os.path.isfile(thumb):
                pix = QPixmap(thumb).scaled(
                    64, 64,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                if not pix.isNull():
                    item.setIcon(QIcon(pix))

            self._list.addItem(item)

        logger.info("Gallery refreshed: %d ready avatar(s)", self._list.count())

    def _on_fetch_error(self, error: str):
        self._refresh_btn.setEnabled(True)
        self._refresh_btn.setText("Refresh")
        logger.error("Fetch error: %s", error)

    def _on_selection_changed(self, current, _previous):
        has_selection = current is not None
        if has_selection:
            avatar_id = current.data(Qt.ItemDataRole.UserRole)
            cached = self._local_avatars.get(avatar_id, {})
            self._use_btn.setEnabled(bool(cached.get("video_path")))
            if not cached.get("video_path"):
                self._use_btn.setText("Download & Use")
            else:
                self._use_btn.setText("Use Selected")
        else:
            self._use_btn.setEnabled(False)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        self._on_use_clicked()

    def _on_use_clicked(self):
        item = self._list.currentItem()
        if not item:
            return
        avatar_id = item.data(Qt.ItemDataRole.UserRole)
        avatar_name = item.data(Qt.ItemDataRole.UserRole + 1)

        cached = self._local_avatars.get(avatar_id, {})
        if cached.get("video_path") and os.path.isfile(cached["video_path"]):
            self.avatar_selected.emit(avatar_id, avatar_name, cached["video_path"])
            return

        # Need to download first
        self._use_btn.setEnabled(False)
        self._use_btn.setText("Downloading...")
        self._download_avatar(avatar_id, avatar_name, self._config.server_url)

    def _download_avatar(self, avatar_id: str, avatar_name: str, server_url: str):
        worker = _DownloadWorker(server_url, avatar_id, avatar_name, self._config.cache_dir)
        worker.finished.connect(self._on_download_finished)
        worker.error.connect(self._on_download_error)
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        worker.error.connect(lambda: self._cleanup_worker(worker))
        self._workers.append(worker)
        worker.start()

    def _on_download_finished(self, avatar_id: str, name: str, video_path: str, thumb_path: str):
        self._local_avatars[avatar_id] = {
            "name": name,
            "video_path": video_path,
            "thumb_path": thumb_path,
        }
        self._use_btn.setEnabled(True)
        self._use_btn.setText("Use Selected")

        # Update thumbnail in list
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == avatar_id:
                if thumb_path and os.path.isfile(thumb_path):
                    pix = QPixmap(thumb_path).scaled(
                        64, 64,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    if not pix.isNull():
                        item.setIcon(QIcon(pix))
                break

        self.avatar_selected.emit(avatar_id, name, video_path)
        logger.info("Avatar ready: %s (%s)", name, video_path)

    def _on_download_error(self, avatar_id: str, error: str):
        self._use_btn.setEnabled(True)
        self._use_btn.setText("Use Selected")
        logger.error("Download failed for %s: %s", avatar_id, error)

    def _cleanup_worker(self, worker: QThread):
        if worker in self._workers:
            self._workers.remove(worker)

    # ----- Public API for local_api messages -----

    def import_avatar(self, avatar_id: str, server_url: str):
        """Download an avatar pushed from the web frontend."""
        self._download_avatar(avatar_id, avatar_id, server_url)

    def select_avatar_by_id(self, avatar_id: str):
        """Select an already-cached avatar by ID."""
        cached = self._local_avatars.get(avatar_id, {})
        if cached.get("video_path"):
            self.avatar_selected.emit(
                avatar_id, cached.get("name", avatar_id), cached["video_path"]
            )
