import pytest
from unittest.mock import MagicMock
from jarmvis.app import JarmvisApp
from jarmvis.serial_bridge import SerialBridge

def test_app_voice_interaction_flow(capsys):
    bridge = SerialBridge(dry_run=True)
    app = JarmvisApp(bridge=bridge, use_mock_ai=True)
    app.handle_voice_prompt("Jarvis, pick up that block")
    captured = capsys.readouterr().out
    assert "Attempting to retrieve the block" in captured
    assert "[DRY-RUN POSE]" in captured
    assert "[DRY-RUN REFLEX] Trigger: THINK" in captured

def test_app_scolding_flow(capsys):
    bridge = SerialBridge(dry_run=True)
    app = JarmvisApp(bridge=bridge, use_mock_ai=True)
    app.handle_voice_prompt("Dummy, go to the dunce corner!")
    captured = capsys.readouterr().out
    assert "dunce corner" in captured
    assert "[DRY-RUN FACE] State: SAD" in captured

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
