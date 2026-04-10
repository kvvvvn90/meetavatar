"""Virtual camera output via pyvirtualcam.

Frame streaming design:
- Reads one frame at a time from disk via cv2.VideoCapture (no full preload).
- Memory usage: ~3 frames in flight at any time (~7 MB for 1280×720).
- Loop: when EOF is reached, seeks back to frame 0.
- Encryption hook: subclass FrameSource to add AES decryption in the future.
"""

import logging
import queue
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path

import cv2
import numpy as np
import pyvirtualcam

logger = logging.getLogger(__name__)

# Number of preprocessed frames to buffer ahead (memory: N × W × H × 3 bytes)
_PREFETCH = 8


# ---------------------------------------------------------------------------
# Frame source abstraction (swap in encrypted source later without touching
# VirtualCamera)
# ---------------------------------------------------------------------------

class FrameSource(ABC):
    """Abstract source that yields raw BGR frames and loops indefinitely."""

    @abstractmethod
    def open(self) -> None: ...

    @abstractmethod
    def read(self) -> np.ndarray | None:
        """Return next BGR frame, or None on unrecoverable error."""
        ...

    @abstractmethod
    def close(self) -> None: ...


class FileFrameSource(FrameSource):
    """Plain MP4 / video file source using cv2.VideoCapture."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._cap: cv2.VideoCapture | None = None

    @property
    def fps(self) -> float:
        if self._cap and self._cap.isOpened():
            return self._cap.get(cv2.CAP_PROP_FPS) or 30.0
        return 30.0

    def open(self) -> None:
        self._cap = cv2.VideoCapture(self._path)
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open video: {self._path}")
        logger.info(
            "Opened video: %s  (%.1f fps, %d frames)",
            self._path,
            self.fps,
            int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        )

    def read(self) -> np.ndarray | None:
        if self._cap is None:
            return None
        ret, frame = self._cap.read()
        if not ret:
            # Reached EOF — loop back to start
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self._cap.read()
        return frame if ret else None

    def close(self) -> None:
        if self._cap:
            self._cap.release()
            self._cap = None


# ---------------------------------------------------------------------------
# Frame preprocessing
# ---------------------------------------------------------------------------

def _preprocess(frame: np.ndarray, width: int, height: int) -> np.ndarray:
    """Letterbox-resize frame to (width, height) and convert BGR → RGB."""
    src_h, src_w = frame.shape[:2]
    scale = min(width / src_w, height / src_h)
    new_w = int(src_w * scale)
    new_h = int(src_h * scale)
    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    x0 = (width - new_w) // 2
    y0 = (height - new_h) // 2
    canvas[y0 : y0 + new_h, x0 : x0 + new_w] = resized
    return cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)


# ---------------------------------------------------------------------------
# Virtual camera
# ---------------------------------------------------------------------------

class VirtualCamera:
    """Streams a looping video into a virtual camera device frame-by-frame."""

    def __init__(self) -> None:
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._source: FrameSource | None = None
        self._width = 1280
        self._height = 720
        self._fps = 30

    @property
    def is_running(self) -> bool:
        return self._running

    def start(
        self,
        video_path: str,
        width: int = 1280,
        height: int = 720,
        fps: int = 30,
        source: FrameSource | None = None,
    ) -> None:
        """Start streaming video into the virtual camera.

        Args:
            video_path: Path to the loop video (used when *source* is None).
            width: Output width in pixels.
            height: Output height in pixels.
            fps: Target frames per second.
            source: Optional custom FrameSource (e.g. encrypted). When None,
                    a plain FileFrameSource is created from *video_path*.
        """
        with self._lock:
            if self._running:
                self._stop_internal()

            self._source = source or FileFrameSource(video_path)
            self._width = width
            self._height = height
            self._fps = fps
            self._running = True

            self._thread = threading.Thread(
                target=self._loop,
                name="VirtualCameraLoop",
                daemon=True,
            )
            self._thread.start()
            logger.info(
                "Virtual camera started: %dx%d @ %d fps", width, height, fps
            )

    def stop(self) -> None:
        with self._lock:
            self._stop_internal()

    def _stop_internal(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None
        logger.info("Virtual camera stopped")

    # ------------------------------------------------------------------
    # Internal streaming loop
    # ------------------------------------------------------------------

    def _loop(self) -> None:
        source = self._source
        width, height, fps = self._width, self._height, self._fps

        try:
            source.open()
        except Exception:
            logger.exception("Failed to open frame source")
            self._running = False
            return

        # Small prefetch queue: producer reads & preprocesses, consumer sends.
        # This decouples disk I/O latency from camera timing without loading
        # the whole video.
        buf: queue.Queue[np.ndarray | None] = queue.Queue(maxsize=_PREFETCH)

        def _producer() -> None:
            try:
                while self._running:
                    frame = source.read()
                    if frame is None:
                        buf.put(None)
                        return
                    processed = _preprocess(frame, width, height)
                    # Block if buffer full — back-pressure keeps memory bounded
                    buf.put(processed)
            except Exception:
                logger.exception("Frame producer crashed")
                buf.put(None)
            finally:
                source.close()

        producer = threading.Thread(target=_producer, name="FrameProducer", daemon=True)
        producer.start()

        try:
            with pyvirtualcam.Camera(
                width=width,
                height=height,
                fps=fps,
                fmt=pyvirtualcam.PixelFormat.RGB,
            ) as cam:
                logger.info("Virtual camera device: %s", cam.device)
                while self._running:
                    try:
                        frame = buf.get(timeout=2.0)
                    except queue.Empty:
                        logger.warning("Frame buffer starved — disk too slow?")
                        continue
                    if frame is None:
                        logger.error("Frame source returned None — stopping")
                        break
                    cam.send(frame)
                    cam.sleep_until_next_frame()
        except Exception:
            logger.exception("Virtual camera loop crashed")
        finally:
            self._running = False
            producer.join(timeout=3.0)
