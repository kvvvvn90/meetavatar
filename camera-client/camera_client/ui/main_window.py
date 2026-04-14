"""Main window with system tray integration."""

import logging
import queue

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QSplitter,
    QStatusBar,
    QSystemTrayIcon,
    QWidget,
)

from ..config import Config
from ..virtual_cam import VirtualCamera
from .avatar_gallery import AvatarGallery
from .camera_control import CameraControl

logger = logging.getLogger(__name__)

# Catppuccin Mocha palette
_STYLE = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI", sans-serif;
}
QSplitter::handle { background-color: #313244; width: 1px; }
QStatusBar { background-color: #181825; color: #a6adc8; font-size: 12px; }
QStatusBar::item { border: none; }
"""


def _make_tray_icon(running: bool = False) -> QIcon:
    """Create a 64x64 tray icon — green when running, grey when idle."""
    pix = QPixmap(64, 64)
    pix.fill(QColor(0, 0, 0, 0))
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    fill = QColor(76, 175, 80) if running else QColor(158, 158, 158)
    p.setBrush(fill)
    p.setPen(QColor(255, 255, 255))
    p.drawEllipse(4, 4, 56, 56)
    p.setBrush(QColor(255, 255, 255, 200))
    p.drawEllipse(20, 20, 24, 24)
    p.setBrush(QColor(50, 50, 50))
    p.drawEllipse(26, 26, 12, 12)
    p.end()
    return QIcon(pix)


class MainWindow(QMainWindow):
    """Main application window with avatar gallery + camera control."""

    def __init__(self, config: Config, msg_queue: queue.Queue) -> None:
        super().__init__()
        self._config = config
        self._msg_queue = msg_queue
        self._vcam = VirtualCamera()
        self._really_quit = False

        self.setWindowTitle("MeetAvatar Camera")
        self.setMinimumSize(720, 480)
        self.resize(900, 560)
        self.setStyleSheet(_STYLE)

        # --- Central layout: gallery (left) + control (right) ---
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._gallery = AvatarGallery(config)
        self._control = CameraControl(config, self._vcam)

        splitter.addWidget(self._gallery)
        splitter.addWidget(self._control)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        self.setCentralWidget(splitter)

        # --- Status bar ---
        self._status_server = QLabel(f"Server: {config.server_url}")
        self._status_cam = QLabel("Camera: Off")
        status_bar = QStatusBar()
        status_bar.addWidget(self._status_server, 1)
        status_bar.addPermanentWidget(self._status_cam)
        self.setStatusBar(status_bar)

        # --- System tray ---
        self._tray = QSystemTrayIcon(_make_tray_icon(False), self)
        self._tray.setToolTip("MeetAvatar Camera")
        self._tray.activated.connect(self._on_tray_activated)

        tray_menu = QMenu()
        show_action = QAction("Show Window", self)
        show_action.triggered.connect(self._show_from_tray)
        tray_menu.addAction(show_action)

        self._toggle_action = QAction("Start Camera", self)
        self._toggle_action.triggered.connect(self._control.toggle_camera)
        tray_menu.addAction(self._toggle_action)

        tray_menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit)
        tray_menu.addAction(quit_action)

        self._tray.setContextMenu(tray_menu)
        self._tray.show()

        # --- Signals ---
        self._gallery.avatar_selected.connect(self._on_avatar_selected)
        self._control.camera_toggled.connect(self._on_camera_toggled)

        # --- Poll message queue from local API ---
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_messages)
        self._poll_timer.start(200)

    # ----- slots -----

    def _on_avatar_selected(self, avatar_id: str, avatar_name: str, video_path: str):
        """Gallery selected an avatar — hand video to camera control."""
        self._control.set_video(video_path, avatar_name)
        self._status_cam.setText(f"Avatar: {avatar_name}")

    def _on_camera_toggled(self, running: bool):
        self._tray.setIcon(_make_tray_icon(running))
        self._toggle_action.setText("Stop Camera" if running else "Start Camera")
        self._status_cam.setText(
            f"Camera: {'On' if running else 'Off'}"
        )

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_from_tray()

    def _show_from_tray(self):
        self.showNormal()
        self.activateWindow()

    def _quit(self):
        self._really_quit = True
        self._vcam.stop()
        self.close()

    # ----- message queue from local API -----

    def _poll_messages(self):
        while not self._msg_queue.empty():
            try:
                msg = self._msg_queue.get_nowait()
            except queue.Empty:
                break
            action = msg.get("action")
            if action == "import":
                avatar_id = msg.get("avatar_id", "")
                server_url = msg.get("server_url", self._config.server_url)
                logger.info("Local API import request: %s", avatar_id)
                self._gallery.import_avatar(avatar_id, server_url)
            elif action == "select":
                avatar_id = msg.get("avatar_id", "")
                self._gallery.select_avatar_by_id(avatar_id)

    # ----- overrides -----

    def closeEvent(self, event):
        if self._really_quit:
            event.accept()
        else:
            event.ignore()
            self.hide()
            self._tray.showMessage(
                "MeetAvatar Camera",
                "Running in background. Double-click tray icon to restore.",
                QSystemTrayIcon.MessageIcon.Information,
                2000,
            )

    # ----- public API for local_api to query state -----

    def get_status(self) -> dict:
        return {
            "running": self._vcam.is_running,
            "avatar": self._control.current_avatar_name,
            "version": "1.0.0",
        }
