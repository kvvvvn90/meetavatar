"""Generation worker — wraps LivePortrait inference + loop maker."""

import asyncio
import logging
from pathlib import Path

from app.config import settings
from app.database import async_session
from app.models.avatar import Avatar
from app.models.task import GenerationTask
from app.services.generation_service import GenerationService
from app.services.avatar_service import AvatarService
from app.services.file_service import FileService
from app.core.liveportrait import generate_avatar_video
from app.core.loop_maker import create_loop_video
from app.core.video_utils import (
    extract_first_frame,
    preprocess_driving_video,
    crop_face_from_video,
    composite_face_on_background,
    read_video_frames,
    write_video,
    reencode_to_h264,
)

logger = logging.getLogger(__name__)


async def execute_generation(task_id: str):
    """Execute the full generation pipeline for a task."""

    async with async_session() as db:
        gen_service = GenerationService(db)
        avatar_service = AvatarService(db)

        # Load task and avatar
        task = await gen_service.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return

        avatar = await avatar_service.get(task.avatar_id)
        if not avatar:
            logger.error(f"Avatar {task.avatar_id} not found")
            await gen_service.fail_task(task_id, "Avatar not found")
            return

        try:
            # --- Phase 1: LivePortrait inference (0% → 70%) ---
            await gen_service.update_progress(task_id, 5, "Preprocessing driving video...")

            driving_path = str(settings.storage_dir / avatar.driving_video_path)
            avatar_dir = FileService.avatar_dir(avatar.id)
            raw_output = str(avatar_dir / "raw.mp4")

            # Step 1a: Force re-encode to 30fps mp4
            fixed_driving = str(avatar_dir / "driving_fixed.mp4")
            driving_path = await asyncio.to_thread(
                preprocess_driving_video, driving_path, fixed_driving, 30.0
            )

            await gen_service.update_progress(task_id, 8, "Detecting face & cropping...")

            # Step 1b: Detect face, crop 512×512, keep background
            cropped_driving = str(avatar_dir / "driving_cropped.mp4")
            driving_cropped, crop_info, background = await asyncio.to_thread(
                crop_face_from_video, driving_path, cropped_driving, 512, 0.7
            )

            # Step 1c: Extract first frame of cropped video as source face
            source_path = str(avatar_dir / "source_frame.jpg")
            await asyncio.to_thread(extract_first_frame, driving_cropped, source_path)

            await gen_service.update_progress(task_id, 12, "Running LivePortrait inference...")

            # Step 1d: Run LivePortrait (512×512 face only)
            # Simulate progress during the long blocking inference call (typically 30-120s)
            async def _simulate_inference_progress():
                for pct in range(14, 58, 2):
                    await asyncio.sleep(3)
                    await gen_service.update_progress(task_id, pct, f"Running LivePortrait inference... {pct}%")

            raw_face_output = str(avatar_dir / "raw_face.mp4")
            sim_task = asyncio.create_task(_simulate_inference_progress())
            try:
                await asyncio.to_thread(
                    generate_avatar_video,
                    source_image=source_path,
                    driving_video=driving_cropped,
                    output_path=raw_face_output,
                    device=task.device,
                )
            finally:
                sim_task.cancel()
                try:
                    await sim_task
                except asyncio.CancelledError:
                    pass

            await gen_service.update_progress(task_id, 62, "Compositing face onto background...")

            # Step 1e: Composite face frames onto background scene
            face_frames, fps = await asyncio.to_thread(
                read_video_frames, raw_face_output
            )
            composite_frames = await asyncio.to_thread(
                composite_face_on_background,
                face_frames, background, crop_info, 512
            )
            await asyncio.to_thread(
                write_video, composite_frames, raw_output, fps
            )

            # Update avatar with raw video path
            avatar.raw_video_path = f"avatars/{avatar.id}/raw.mp4"
            await db.commit()

            await gen_service.update_progress(task_id, 70, "LivePortrait inference complete")

            # --- Phase 2: Loop video creation (70% → 95%) ---
            await gen_service.update_progress(task_id, 75, "Creating seamless loop video...")

            loop_raw = str(avatar_dir / "loop_raw.mp4")
            loop_output = str(avatar_dir / "loop.mp4")

            await asyncio.to_thread(
                create_loop_video,
                input_path=raw_output,
                output_path=loop_raw,
                method=task.loop_method,
                blend_frames=task.blend_frames,
            )

            await gen_service.update_progress(task_id, 88, "Encoding for web playback...")

            # Re-encode to browser-compatible H.264 (OpenCV writes mp4v which browsers can't play)
            await asyncio.to_thread(reencode_to_h264, loop_raw, loop_output)

            await gen_service.update_progress(task_id, 95, "Generating thumbnail...")

            # --- Phase 3: Thumbnail (95% → 100%) ---
            thumb_rel = FileService.generate_thumbnail(loop_output, avatar.id)
            if thumb_rel:
                await avatar_service.set_thumbnail(avatar, thumb_rel)

            # Finalize
            await avatar_service.set_loop_video(avatar, f"avatars/{avatar.id}/loop.mp4")
            await gen_service.complete_task(task_id)

            logger.info(f"Generation complete for avatar {avatar.id}")

        except Exception as e:
            logger.exception(f"Generation failed for task {task_id}")
            await gen_service.fail_task(task_id, str(e))
            await avatar_service.set_status(avatar, "error", str(e))
