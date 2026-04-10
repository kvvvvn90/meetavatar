"""Seamless loop video generator.

Migrated from: funtion testing/src/generator/loop_maker.py
Changes: updated import path only.
"""

import logging

import cv2
import numpy as np

from app.core.video_utils import read_video_frames, write_video

logger = logging.getLogger(__name__)


def make_palindrome_loop(
    frames: list[np.ndarray],
    blend_frames: int = 15,
) -> list[np.ndarray]:
    """Palindrome loop: forward + backward with smooth blending at turning points."""
    if len(frames) < blend_frames * 2 + 10:
        raise ValueError(
            f"Video has too few frames ({len(frames)}), need at least {blend_frames * 2 + 10}"
        )

    forward = frames
    backward = frames[::-1]

    result = []

    # Forward part (minus last blend_frames)
    result.extend(forward[:-blend_frames])

    # Forward→backward blend
    for i in range(blend_frames):
        alpha = i / blend_frames
        blended = cv2.addWeighted(
            forward[-(blend_frames - i)], 1 - alpha,
            backward[i], alpha, 0,
        )
        result.append(blended)

    # Backward part (minus first and last blend_frames)
    result.extend(backward[blend_frames:-blend_frames])

    # Backward→forward blend
    for i in range(blend_frames):
        alpha = i / blend_frames
        blended = cv2.addWeighted(
            backward[-(blend_frames - i)], 1 - alpha,
            forward[i], alpha, 0,
        )
        result.append(blended)

    return result


def make_crossfade_loop(
    frames: list[np.ndarray],
    crossfade_frames: int = 30,
) -> list[np.ndarray]:
    """Head-tail crossfade loop."""
    n = len(frames)
    if n < crossfade_frames * 2:
        raise ValueError(
            f"Video has too few frames ({n}), need at least {crossfade_frames * 2}"
        )

    result = list(frames[crossfade_frames:])

    for i in range(crossfade_frames):
        alpha = i / crossfade_frames
        blended = cv2.addWeighted(
            frames[-(crossfade_frames - i)], 1 - alpha,
            frames[i], alpha, 0,
        )
        result.append(blended)

    return result


def create_loop_video(
    input_path: str,
    output_path: str,
    method: str = "palindrome",
    blend_frames: int = 15,
):
    """Create a seamless loop video from input video."""
    frames, fps = read_video_frames(input_path)
    logger.info(f"Read {len(frames)} frames, {fps} fps")

    if method == "palindrome":
        loop_frames = make_palindrome_loop(frames, blend_frames)
    elif method == "crossfade":
        loop_frames = make_crossfade_loop(frames, blend_frames)
    else:
        raise ValueError(f"Unknown method: {method}")

    logger.info(f"Generated loop video: {len(loop_frames)} frames")
    write_video(loop_frames, output_path, fps)
    logger.info(f"Saved: {output_path}")
