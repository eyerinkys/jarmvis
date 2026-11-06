# tests/test_serial_bridge.py
import json
from unittest.mock import MagicMock, patch
from jarmvis.serial_bridge import SerialBridge

def test_dry_run_send_pose(capsys):
    bridge = SerialBridge(port=None, dry_run=True)
    success = bridge.send_pose(angles=[90, 60, 110, 45, 90, 30], speed=50, easing="spring", face="alert")
    assert success is True
    captured = capsys.readouterr().out
    assert "[dry-run:pose]" in captured
    assert "90, 60, 110, 45, 90, 30" in captured
    assert "alert" in captured

def test_dry_run_send_reflex(capsys):
    bridge = SerialBridge(port=None, dry_run=True)
    success = bridge.send_reflex("PERK_UP")
    assert success is True
    captured = capsys.readouterr().out
    assert "[dry-run:reflex]" in captured
    assert "PERK_UP" in captured

def test_serial_connected_sends_json():
    mock_serial = MagicMock()
    with patch("serial.Serial", return_value=mock_serial):
        bridge = SerialBridge(port="/dev/cu.usbserial-test", dry_run=False)
        bridge.send_pose(angles=[90, 90, 90, 90, 90, 90], speed=40)
        assert mock_serial.write.called
        written_data = mock_serial.write.call_args[0][0].decode("utf-8")
        packet = json.loads(written_data.strip())
        assert packet["cmd"] == "pose"
        assert packet["angles"] == [90, 90, 90, 90, 90, 90]
        assert packet["speed"] == 40

