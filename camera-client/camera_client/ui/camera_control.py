"""Camera control panel — start/stop virtual camera + status."""

import logging

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import (
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..config import Config
from ..virtual_cam import VirtualCamera

logger = logging.getLogger(__name__)

_STYLE = """
QPushButton#startBtn {
    font-size: 18px;
    font-weight: bold;
    padding: 14px 32px;
    border-radius: 10px;
}
QPushButton#startBtn[running="false"] {
    background-color: #a6e3a1;
    color: #1e1e2e;
}
QPushButton#startBtn[running="false"]:hover {
    background-color: #94e2d5;
}
QPushButton#startBtn[running="true"] {
    background-color: #f38ba8;
    color: #1e1e2e;
}
QPushButton#startBtn[running="true"]:hover {
    background-color: #eba0ac;
}
QPushButton#startBtn:disabled {
    background-color: #45475a;
    color: #6c7086;
}
QLabel#hint {
    color: #6c7086;
    font-size: 12px;
}
QLabel#avatarLabel {
    color: #cdd6f4;
    font-size: 14px;
}
QLabel#statusLabel {
    font-size: 13px;
}
"""


class _StatusDot(QWidget):
    """Small colored circle indicator."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._color = QColor(158, 158, 158)
        self.setFixedSize(14, 14)

    def set_active(self, active: bool):
        self._color = QColor(76, 175, 80) if active else QColor(158, 158, 158)
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(self._color)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(1, 1, 12, 12)


class CameraControl(QWidget):
    """Panel for controlling the virtual camera."""

    camera_toggled = pyqtSignal(bool)  # True = running

    def __init__(self, config: Config, vcam: VirtualCamera) -> None:
        super().__init__()
        self._config = config
        self._vcam = vcam
        self._video_path: str | None = None
        self._avatar_name: str = ""

        self.setStyleSheet(_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 24, 20, 24)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Current avatar label
        self._avatar_label = QLabel("No avatar selected")
        self._avatar_label.setObjectName("avatarLabel")
        self._avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._avatar_label)

        layout.addSpacing(20)

        # Start / Stop button
        self._start_btn = QPushButton("Start Camera")
        self._start_btn.setObjectName("startBtn")
        self._start_btn.setProperty("running", False)
        self._start_btn.setEnabled(False)
        self._start_btn.setFixedWidth(220)
        self._start_btn.clicked.connect(self.toggle_camera)
        layout.addWidget(self._start_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(16)

        # Status indicator
        status_row = QWidget()
        status_layout = QVBoxLayout(status_row)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        dot_row = QWidget()
        from PyQt6.QtWidgets import QHBoxLayout
        dot_layout = QHBoxLayout(dot_row)
        dot_layout.setContentsMargins(0, 0, 0, 0)
        dot_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._dot = _StatusDot()
        dot_layout.addWidget(self._dot)

        self._status_label = QLabel("Camera: Off")
        self._status_label.setObjectName("statusLabel")
        self._status_label.setStyleSheet("color: #a6adc8;")
        dot_layout.addWidget(self._status_label)

        status_layout.addWidget(dot_row)
        layout.addWidget(status_row)

        layout.addSpacing(24)

        # Hint
        hint = QLabel(
            'Select "OBS Virtual Camera" in your\n'
            "meeting software's camera list."
        )
        hint.setObjectName("hint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        layout.addStretch()

    @property
    def current_avatar_name(self) -> str:
        return self._avatar_name

    def set_video(self, video_path: str, avatar_name: str):
        """Set the video to be played into the virtual camera."""
        self._video_path = video_path
        self._avatar_name = avatar_name
        self._avatar_label.setText(f"Avatar: {avatar_name}")
        self._start_btn.setEnabled(True)

    def toggle_camera(self):
        if self._vcam.is_running:
            self._vcam.stop()
            self._update_ui(False)
        else:
            if not self._video_path:
                return
            self._vcam.start(
                self._video_path,
                self._config.width,
                self._config.height,
                self._config.fps,
            )
            self._update_ui(True)

    def _update_ui(self, running: bool):
        self._start_btn.setText("Stop Camera" if running else "Start Camera")
        self._start_btn.setProperty("running", running)
        self._start_btn.style().unpolish(self._start_btn)
        self._start_btn.style().polish(self._start_btn)
        self._dot.set_active(running)
        self._status_label.setText(f"Camera: {'On' if running else 'Off'}")
        self._status_label.setStyleSheet(
            "color: #a6e3a1;" if running else "color: #a6adc8;"
        )
        self.camera_toggled.emit(running)
