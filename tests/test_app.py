import pytest
from unittest.mock import MagicMock
from jarmvis.app import JarmvisApp
from jarmvis.serial_bridge import SerialBridge

def test_app_voice_interaction_flow(capsys):
    bridge = SerialBridge(dry_run=True)
    app = JarmvisApp(bridge=bridge, use_mock_ai=True)
    app.handle_voice_prompt("Knox, pick up that block")
    captured = capsys.readouterr().out
    assert "picks up a block" in captured
    assert "[dry-run:pose]" in captured
    assert "[dry-run:reflex] trigger=THINK" in captured

def test_app_scolding_flow(capsys):
    bridge = SerialBridge(dry_run=True)
    app = JarmvisApp(bridge=bridge, use_mock_ai=True)
    app.handle_voice_prompt("Dummy, go to the dunce corner!")
    captured = capsys.readouterr().out
    assert "dunce corner" in captured
    assert "[dry-run:face] state=SAD" in captured

def test_app_custom_brain_injection():
    mock_brain = MagicMock()
    mock_brain.think.return_value = {
        "speech": "Testing custom injection.",
        "emotion": "CURIOUS",
        "face": "CURIOUS",
        "macro": None
    }
    mock_bridge = MagicMock()
    app = JarmvisApp(bridge=mock_bridge, brain=mock_brain, use_mock_ai=True)
    app.handle_voice_prompt("Any message")

    assert mock_bridge.send_reflex.called
    assert mock_bridge.send_face.called
    assert mock_bridge.send_face.call_args[0][0] == "CURIOUS"

def test_app_direct_command_execution():
    mock_bridge = MagicMock()
    app = JarmvisApp(bridge=mock_bridge, use_mock_ai=True)
    
    # Test shortcut helper methods
    app.perk_up()
    assert mock_bridge.send_reflex.called
    assert mock_bridge.send_reflex.call_args[0][0] == "PERK_UP"

def test_app_vad_threshold_retention():
    mock_bridge = MagicMock()
    app = JarmvisApp(bridge=mock_bridge, use_mock_ai=True, vad_threshold=0.0003, api_key="test_key")
    assert app.vad_threshold == 0.0003
    assert app.vad.energy_threshold == 0.0003
    assert app.stt.api_key == "test_key"


def test_app_handle_voice_prompt_gesticulation_fallback():
    mock_bridge = MagicMock()
    app = JarmvisApp(bridge=mock_bridge, use_mock_ai=True)
    # Force audio analyzer to raise wave.Error to simulate corrupt audio file
    import wave
    app.audio_analyzer.extract_features_from_file = MagicMock(side_effect=wave.Error("file does not start with RIFF id"))
    app.playback.play_with_gestures = MagicMock()

    # Must complete gracefully without raising an exception
    app.handle_voice_prompt("Hello Knox, are you there?")
    assert app.playback.play_with_gestures.called



