import time
from unittest.mock import MagicMock
import pytest
from jarmvis.playback_engine import CoordinatedPlaybackEngine
from jarmvis.serial_bridge import SerialBridge


def test_playback_engine_streams_trajectory_timing():
    bridge = MagicMock(spec=SerialBridge)
    engine = CoordinatedPlaybackEngine(bridge=bridge, fps=50)

    # 10 frames at 50fps = 0.20s total trajectory
    trajectory = [[90, 90, 90, 90, 90, 30] for _ in range(10)]
    start = time.time()
    engine.play_with_gestures(audio_path=None, trajectory=trajectory, blocking=True)
    elapsed = time.time() - start

    assert bridge.send_pose.call_count == 10
    # Must take at least 0.15s (verifying real 50Hz clock timing, not zero-delay burst)
    assert elapsed >= 0.15


def test_playback_engine_empty_trajectory():
    bridge = MagicMock(spec=SerialBridge)
    engine = CoordinatedPlaybackEngine(bridge=bridge, fps=50)
    engine.play_with_gestures(audio_path=None, trajectory=[], blocking=True)
    assert bridge.send_pose.call_count == 0


def test_playback_engine_non_blocking_thread():
    bridge = MagicMock(spec=SerialBridge)
    engine = CoordinatedPlaybackEngine(bridge=bridge, fps=50)

    # 15 frames = 0.30s
    trajectory = [[90, 90, 90, 90, 90, 30] for _ in range(15)]
    start = time.time()
    thread = engine.play_with_gestures(audio_path=None, trajectory=trajectory, blocking=False)
    immediate_elapsed = time.time() - start

    # Should return immediately
    assert immediate_elapsed < 0.10
    assert thread is not None
    thread.join(timeout=1.0)
    assert bridge.send_pose.call_count == 15

