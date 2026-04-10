"""LivePortrait inference wrapper.

Migrated from: funtion testing/src/generator/liveportrait.py
Changes:
  - Paths configurable via app.config.settings (env vars)
  - print() → logging
  - Added progress_callback parameter
"""

import os
import sys
import glob
import shutil
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Callable

from app.config import settings

logger = logging.getLogger(__name__)

LIVEPORTRAIT_DIR = settings.liveportrait_dir
PRETRAINED_DIR = settings.pretrained_weights_dir


def check_liveportrait_installed() -> bool:
    """Check if LivePortrait is installed."""
    return LIVEPORTRAIT_DIR.exists() and (LIVEPORTRAIT_DIR / "src").exists()


def setup_liveportrait():
    """Clone and configure LivePortrait."""
    third_party = LIVEPORTRAIT_DIR.parent
    third_party.mkdir(parents=True, exist_ok=True)

    if not LIVEPORTRAIT_DIR.exists():
        logger.info("Downloading LivePortrait...")
        subprocess.run(
            ["git", "clone", "https://github.com/KwaiVGI/LivePortrait.git",
             str(LIVEPORTRAIT_DIR)],
            check=True,
        )
        logger.info("LivePortrait download complete")

    if not PRETRAINED_DIR.exists():
        logger.info("Downloading pretrained model weights...")
        subprocess.run(
            [
                sys.executable, "-c",
                "from huggingface_hub import snapshot_download; "
                f"snapshot_download('KwaiVGI/LivePortrait', local_dir=r'{PRETRAINED_DIR}')"
            ],
            check=True,
        )
        logger.info("Model weights download complete")


def generate_avatar_video(
    source_image: str,
    driving_video: str,
    output_path: str,
    device: str = "cuda",
    progress_callback: Callable[[int, str], None] | None = None,
) -> str:
    """Generate avatar video via LivePortrait subprocess.

    Args:
        source_image: Path to front-facing source photo
        driving_video: Path to driving video
        output_path: Output video path
        device: "cuda" or "cpu"
        progress_callback: Optional callback(progress_pct, message)

    Returns:
        Actual output video path
    """
    if not check_liveportrait_installed():
        raise RuntimeError("LivePortrait not installed. Run setup first.")

    source_path = Path(source_image).resolve()
    driving_path = Path(driving_video).resolve()
    output_dir = Path(output_path).resolve().parent
    output_dir.mkdir(parents=True, exist_ok=True)

    if not source_path.exists():
        raise FileNotFoundError(f"Source photo not found: {source_image}")
    if not driving_path.exists():
        raise FileNotFoundError(f"Driving video not found: {driving_video}")

    if progress_callback:
        progress_callback(10, "Preparing LivePortrait inference...")

    logger.info(f"Source photo: {source_path}")
    logger.info(f"Driving video: {driving_path}")
    logger.info(f"Output dir: {output_dir}")

    # Copy inputs to ASCII temp path (OpenCV Chinese path workaround)
    tmp_dir = Path(tempfile.gettempdir()) / "meeting_avatar"
    tmp_dir.mkdir(exist_ok=True)
    tmp_source = tmp_dir / "source.jpg"
    tmp_driving = tmp_dir / ("driving" + driving_path.suffix)
    tmp_output_dir = tmp_dir / "output"
    tmp_output_dir.mkdir(exist_ok=True)

    shutil.copy2(source_path, tmp_source)
    shutil.copy2(driving_path, tmp_driving)

    # Copy LivePortrait resources to temp dir (Chinese path workaround)
    resources_src = LIVEPORTRAIT_DIR / "src" / "utils" / "resources"
    resources_dst = tmp_dir / "resources"
    if resources_src.exists() and not resources_dst.exists():
        shutil.copytree(resources_src, resources_dst)

    if progress_callback:
        progress_callback(20, "Running inference...")

    # Create patch script for inference
    patch_script = tmp_dir / "run_inference.py"
    patch_script.write_text(f'''
import sys, os, cv2, numpy as np
sys.path.insert(0, r"{LIVEPORTRAIT_DIR}")

# Read mask via numpy (bypass OpenCV Chinese path issue)
mask_path = r"{resources_dst / 'mask_template.png'}"
with open(mask_path, "rb") as f:
    mask_data = np.frombuffer(f.read(), np.uint8)
    mask_img = cv2.imdecode(mask_data, cv2.IMREAD_COLOR)

# Patch InferenceConfig mask_crop default
from src.config.inference_config import InferenceConfig
original_init = InferenceConfig.__init__
def patched_init(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    if self.mask_crop is None:
        self.mask_crop = mask_img
InferenceConfig.__init__ = patched_init
InferenceConfig.__dataclass_fields__["mask_crop"].default_factory = lambda: mask_img

# Run original inference
exec(open(r"{LIVEPORTRAIT_DIR / 'inference.py'}").read())
''', encoding="utf-8")

    # Build command
    cmd = [
        sys.executable,
        str(patch_script),
        "-s", str(tmp_source),
        "-d", str(tmp_driving),
        "-o", str(tmp_output_dir),
    ]

    if device == "cpu":
        cmd.append("--flag_force_cpu")

    # Set up environment
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONLEGACYWINDOWSSTDIO"] = "0"

    try:
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = str(Path(ffmpeg_path).parent)
        env["PATH"] = ffmpeg_dir + os.pathsep + env.get("PATH", "")

        ffmpeg_shim = Path(ffmpeg_dir) / "ffmpeg.exe"
        if not ffmpeg_shim.exists():
            shutil.copy2(ffmpeg_path, ffmpeg_shim)
    except Exception as e:
        logger.warning(f"Could not configure ffmpeg path: {e}")

    # Run inference subprocess
    result = subprocess.run(
        cmd,
        cwd=str(LIVEPORTRAIT_DIR),
        capture_output=False,
        env=env,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"LivePortrait inference failed (exit code {result.returncode})"
        )

    if progress_callback:
        progress_callback(60, "Inference complete, processing output...")

    # Find generated file and move to final path
    output_files = sorted(
        glob.glob(str(tmp_output_dir / "*.mp4")),
        key=os.path.getmtime,
        reverse=True,
    )

    if not output_files:
        raise RuntimeError(f"No video files found in {tmp_output_dir}")

    shutil.move(output_files[0], output_path)

    # Cleanup temp files
    shutil.rmtree(tmp_dir, ignore_errors=True)

    logger.info(f"Generation complete: {output_path}")
    return output_path
