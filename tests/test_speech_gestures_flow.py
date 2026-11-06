import pytest
from jarmvis.app import JarmvisApp
from jarmvis.serial_bridge import SerialBridge


def test_full_speech_gestures_flow_in_app(monkeypatch):
    bridge = SerialBridge(dry_run=True)
    poses_sent = []

    def mock_send_pose(angles, speed=50, easing="cosine", face=None):
        poses_sent.append(angles)
        return True

    monkeypatch.setattr(bridge, "send_pose", mock_send_pose)

    app = JarmvisApp(bridge=bridge, use_mock_ai=True)
    app.handle_voice_prompt("Hey Knox, tell me something cool, genius")

    # Knox speaks and generates gesticulations
    assert len(poses_sent) > 0

    # Ensure every single pose is 6 joints and clamped to physical bounds
    for p in poses_sent:
        assert len(p) == 6
        assert 0 <= p[0] <= 180   # Waist
        assert 15 <= p[1] <= 165  # Shoulder
        assert 15 <= p[2] <= 165  # Elbow
        assert 0 <= p[3] <= 180   # Wrist Pitch
        assert 0 <= p[4] <= 180   # Wrist Roll
        assert 10 <= p[5] <= 120  # Claw

    # Assert that wrist roll actually modulated and moved during speech
    wrist_rolls = [p[4] for p in poses_sent]
    assert max(wrist_rolls) != min(wrist_rolls)

