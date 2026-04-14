"""Video read/write utilities.

Migrated from: funtion testing/src/utils/video.py
"""

import cv2
import numpy as np
from pathlib import Path


def read_video_frames(video_path: str) -> tuple[list[np.ndarray], float]:
    """Read all frames and FPS from a video file.

    Returns:
        (frames, fps) tuple
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    return frames, fps


def write_video(frames: list[np.ndarray], output_path: str, fps: float = 30.0):
    """Write a list of frames to an MP4 video file."""
    if not frames:
        raise ValueError("Frame list is empty")

    h, w = frames[0].shape[:2]
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    for frame in frames:
        writer.write(frame)
    writer.release()


def resize_frame(frame: np.ndarray, width: int, height: int) -> np.ndarray:
    """Resize frame to target dimensions."""
    return cv2.resize(frame, (width, height), interpolation=cv2.INTER_LANCZOS4)


def extract_first_frame(video_path: str, output_path: str) -> str:
    """Extract first frame from video and save as JPEG image.

    Returns:
        output_path
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {video_path}")
    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise RuntimeError(f"Cannot read first frame from {video_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(output_path, frame)
    return output_path


def preprocess_driving_video(
    input_path: str,
    output_path: str,
    target_fps: float = 30.0,
) -> str:
    """Re-encode driving video to mp4 with forced fixed FPS.

    Always converts to {target_fps}fps mp4 regardless of input format/FPS.
    This guarantees consistent frame rate for LivePortrait inference.

    Returns:
        Path to the converted driving video (output_path).
    """
    import subprocess

    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        ffmpeg_exe = "ffmpeg"

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", input_path,
        "-r", str(target_fps),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-an",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg driving video conversion failed: {result.stderr.decode(errors='replace')}"
        )

    return output_path


def reencode_to_h264(input_path: str, output_path: str) -> str:
    """Re-encode a video to H.264 mp4 so browsers can play it inline.

    OpenCV's VideoWriter uses mp4v codec by default, which most browsers
    cannot decode. This function re-encodes to libx264 + yuv420p.
    """
    import subprocess

    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        ffmpeg_exe = "ffmpeg"

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg_exe, "-y",
        "-i", input_path,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",  # required for browser compatibility
        "-movflags", "+faststart",  # enables progressive download
        "-an",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg H.264 re-encode failed: {result.stderr.decode(errors='replace')}"
        )
    return output_path


def detect_face_bbox(frame: np.ndarray) -> tuple[int, int, int, int] | None:
    """Detect the largest face in a frame using OpenCV Haar cascade.

    Returns:
        (x, y, w, h) bounding box of the largest face, or None.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    faces = cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50)
    )
    if len(faces) == 0:
        return None
    # Return the largest face
    return tuple(max(faces, key=lambda f: f[2] * f[3]))


def crop_face_from_video(
    input_path: str,
    output_path: str,
    target_size: int = 512,
    padding: float = 0.7,
) -> tuple[str, tuple[int, int, int], np.ndarray]:
    """Crop driving video around the detected face using ffmpeg.

    Detects face in the first frame, calculates a square crop region
    with padding, then uses ffmpeg to efficiently crop + scale the
    entire video to target_size × target_size.

    Args:
        input_path: Path to the preprocessed driving video (mp4)
        output_path: Path for the cropped output video
        target_size: Output square size (default 512)
        padding: Extra padding around face as fraction of face size

    Returns:
        (output_path, (crop_x, crop_y, crop_size), background_frame)
        background_frame is the first frame at original resolution.
    """
    import subprocess

    # Read first frame for face detection
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {input_path}")
    ret, first_frame = cap.read()
    fh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    cap.release()

    if not ret:
        raise RuntimeError(f"Cannot read first frame from {input_path}")

    background = first_frame.copy()

    # Detect face
    bbox = detect_face_bbox(first_frame)
    if bbox is None:
        # Fallback: center crop using the shorter dimension
        size = min(fh, fw)
        x1 = (fw - size) // 2
        y1 = (fh - size) // 2
        crop_size = size
    else:
        x, y, w, h = bbox
        cx, cy = x + w // 2, y + h // 2
        crop_size = int(max(w, h) * (1 + padding))

        # Center the crop on the face
        half = crop_size // 2
        x1 = cx - half
        y1 = cy - half

        # Clamp to frame bounds
        x1 = max(0, min(x1, fw - crop_size))
        y1 = max(0, min(y1, fh - crop_size))
        crop_size = min(crop_size, fw - x1, fh - y1)

    crop_info = (x1, y1, crop_size)

    # Use ffmpeg to crop and scale
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        ffmpeg_exe = "ffmpeg"

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg_exe, "-y",
        "-i", input_path,
        "-vf", f"crop={crop_size}:{crop_size}:{x1}:{y1},scale={target_size}:{target_size}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-an",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg face crop failed: {result.stderr.decode(errors='replace')}"
        )

    return output_path, crop_info, background


def composite_face_on_background(
    face_frames: list[np.ndarray],
    background: np.ndarray,
    crop_info: tuple[int, int, int],
    target_height: int = 512,
) -> list[np.ndarray]:
    """Paste 512×512 face frames onto a background at the original face position.

    Creates a feathered (soft-edge) blend so the face merges naturally
    into the background instead of showing a hard square border.

    Args:
        face_frames: List of 512×512 face frames from LivePortrait
        background: Original full-resolution first frame (used for dimensions + crop coords)
        crop_info: (crop_x, crop_y, crop_size) from crop_face_from_video
        target_height: Final video height (default 512)

    Returns:
        List of composite frames at (proportional_width × target_height)
    """
    bg_h, bg_w = background.shape[:2]
    scale = target_height / bg_h
    new_w = int(bg_w * scale)

    bg_resized = cv2.resize(background, (new_w, target_height))

    crop_x, crop_y, crop_size = crop_info
    sx = int(crop_x * scale)
    sy = int(crop_y * scale)
    s_size = int(crop_size * scale)

    # Build feather mask (soft edges for blending)
    feather = max(1, s_size // 15)
    mask = np.ones((s_size, s_size), dtype=np.float32)
    for i in range(feather):
        alpha = i / feather
        mask[i, :] *= alpha
        mask[-(i + 1), :] *= alpha
        mask[:, i] *= alpha
        mask[:, -(i + 1)] *= alpha
    mask_3ch = mask[:, :, np.newaxis]  # (s_size, s_size, 1) for broadcasting

    composites = []
    for face in face_frames:
        frame = bg_resized.copy()
        face_resized = cv2.resize(face, (s_size, s_size))

        # Clamp paste region to frame bounds
        py1 = max(0, sy)
        px1 = max(0, sx)
        py2 = min(target_height, sy + s_size)
        px2 = min(new_w, sx + s_size)

        fy1 = py1 - sy
        fx1 = px1 - sx
        fy2 = fy1 + (py2 - py1)
        fx2 = fx1 + (px2 - px1)

        # Feathered blend
        face_region = face_resized[fy1:fy2, fx1:fx2].astype(np.float32)
        bg_region = frame[py1:py2, px1:px2].astype(np.float32)
        m = mask_3ch[fy1:fy2, fx1:fx2]

        blended = (face_region * m + bg_region * (1.0 - m)).astype(np.uint8)
        frame[py1:py2, px1:px2] = blended

        composites.append(frame)

    return composites


def get_video_info(video_path: str) -> dict:
    """Get basic video metadata."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {video_path}")

    info = {
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
    }
    info["duration"] = info["frame_count"] / info["fps"] if info["fps"] > 0 else 0
    cap.release()
    return info
