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


def test_get_audio_play_command_mac(monkeypatch):
    from jarmvis.playback_engine import get_audio_play_command
    monkeypatch.setattr("sys.platform", "darwin")
    monkeypatch.setattr("shutil.which", lambda cmd: "/usr/bin/afplay" if cmd == "afplay" else None)
    cmd = get_audio_play_command("/tmp/test.mp3")
    assert cmd == ["afplay", "/tmp/test.mp3"]


def test_get_audio_play_command_linux(monkeypatch):
    from jarmvis.playback_engine import get_audio_play_command
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setattr("shutil.which", lambda cmd: "/usr/bin/mpv" if cmd == "mpv" else None)
    cmd = get_audio_play_command("/tmp/test.mp3")
    assert cmd == ["mpv", "--no-video", "--really-quiet", "/tmp/test.mp3"]


def test_playback_engine_with_audio_process(monkeypatch, tmp_path):
    from unittest.mock import patch
    audio_file = tmp_path / "speech.mp3"
    audio_file.write_bytes(b"dummy audio")

    bridge = MagicMock(spec=SerialBridge)
    engine = CoordinatedPlaybackEngine(bridge=bridge, fps=50)

    with patch("jarmvis.playback_engine.play_audio_process") as mock_play:
        mock_proc = MagicMock()
        mock_play.return_value = mock_proc

        engine.play_with_gestures(audio_path=str(audio_file), trajectory=[], blocking=True)

        assert mock_play.called
        assert mock_proc.wait.called


