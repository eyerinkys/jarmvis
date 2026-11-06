import logging
import os
import subprocess
import threading
import time
from typing import Callable
from jarmvis.serial_bridge import SerialBridge

logger = logging.getLogger("jarmvis.playback")


class CoordinatedPlaybackEngine:
    """Synchronizes audio playback with 50Hz robotic arm gesticulation trajectories."""

    def __init__(self, bridge: SerialBridge, fps: int = 50):
        self.bridge = bridge
        self.fps = fps
        self.frame_interval = 1.0 / float(fps)

    def _execute_sync_loop(
        self,
        audio_path: str | None,
        trajectory: list[list[int]],
        speed: int = 65,
        on_start: Callable[[], None] | None = None,
        on_end: Callable[[], None] | None = None,
    ) -> None:
        if on_start:
            on_start()

        audio_proc = None
        if audio_path and os.path.exists(audio_path):
            try:
                # Use macOS afplay for native, zero-latency, non-blocking playback
                audio_proc = subprocess.Popen(
                    ["afplay", audio_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception as e:
                logger.warning(f"Failed to start audio playback via afplay: {e}")

        try:
            if trajectory:
                start_time = time.time()
                for i, pose in enumerate(trajectory):
                    self.bridge.send_pose(angles=pose, speed=speed, easing="linear")
                    target_time = start_time + (i + 1) * self.frame_interval
                    remaining = target_time - time.time()
                    if remaining > 0.001:
                        time.sleep(remaining)

            # If audio is longer than trajectory, wait for audio playback to finish
            if audio_proc is not None:
                audio_proc.wait(timeout=10.0)
        except Exception as e:
            logger.error(f"Playback synchronization error: {e}")
            if audio_proc is not None:
                try:
                    audio_proc.terminate()
                except Exception:
                    pass
        finally:
            if on_end:
                on_end()

    def play_with_gestures(
        self,
        audio_path: str | None,
        trajectory: list[list[int]],
        speed: int = 65,
        blocking: bool = True,
        on_start: Callable[[], None] | None = None,
        on_end: Callable[[], None] | None = None,
    ) -> threading.Thread | None:
        """Starts coordinated audio playback and arm gesticulation streaming."""
        if not blocking:
            thread = threading.Thread(
                target=self._execute_sync_loop,
                args=(audio_path, trajectory, speed, on_start, on_end),
                daemon=True,
            )
            thread.start()
            return thread
        else:
            self._execute_sync_loop(
                audio_path=audio_path,
                trajectory=trajectory,
                speed=speed,
                on_start=on_start,
                on_end=on_end,
            )
            return None

