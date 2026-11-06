import json
import pytest
from jarmvis.macros import MacroSequencer
from jarmvis.serial_bridge import SerialBridge

def test_load_and_run_macro(tmp_path):
    macros_path = tmp_path / "macros.json"
    dummy_data = {
        "TEST_MACRO": [
            {"angles": [90, 60, 110, 45, 90, 30], "speed": 50, "pause_ms": 10},
            {"angles": [90, 90, 90, 90, 90, 90], "speed": 40, "pause_ms": 10}
        ]
    }
    macros_path.write_text(json.dumps(dummy_data))
    
    bridge = SerialBridge(dry_run=True)
    sequencer = MacroSequencer(bridge=bridge, macros_file=str(macros_path))
    assert "TEST_MACRO" in sequencer.macros
    success = sequencer.execute_macro("TEST_MACRO")
    assert success is True

def test_save_new_waypoint(tmp_path):
    macros_path = tmp_path / "macros.json"
    macros_path.write_text(json.dumps({}))
    bridge = SerialBridge(dry_run=True)
    sequencer = MacroSequencer(bridge=bridge, macros_file=str(macros_path))
    sequencer.save_waypoint("PICK_BLOCK", angles=[45, 60, 80, 45, 90, 100], speed=50, pause_ms=200)
    
    reloaded = MacroSequencer(bridge=bridge, macros_file=str(macros_path))
    assert "PICK_BLOCK" in reloaded.macros
    assert reloaded.macros["PICK_BLOCK"][0]["angles"] == [45, 60, 80, 45, 90, 100]

def test_execute_nonexistent_macro(tmp_path):
    macros_path = tmp_path / "macros.json"
    macros_path.write_text(json.dumps({}))
    bridge = SerialBridge(dry_run=True)
    sequencer = MacroSequencer(bridge=bridge, macros_file=str(macros_path))
    assert sequencer.execute_macro("NONEXISTENT") is False

def test_execute_macro_with_step_callback(tmp_path):
    macros_path = tmp_path / "macros.json"
    dummy_data = {
        "TEST": [
            {"angles": [90, 90, 90, 90, 90, 90], "speed": 50, "pause_ms": 0}
        ]
    }
    macros_path.write_text(json.dumps(dummy_data))
    bridge = SerialBridge(dry_run=True)
    sequencer = MacroSequencer(bridge=bridge, macros_file=str(macros_path))
    called = []
    sequencer.execute_macro("TEST", step_callback=lambda wp: called.append(wp))
    assert len(called) == 1

def test_load_corrupted_json(tmp_path):
    macros_path = tmp_path / "macros.json"
    macros_path.write_text("{ this is invalid json content")
    bridge = SerialBridge(dry_run=True)
    sequencer = MacroSequencer(bridge=bridge, macros_file=str(macros_path))
    assert sequencer.macros == {}

def test_load_nonexistent_file(tmp_path):
    macros_path = tmp_path / "does_not_exist.json"
    bridge = SerialBridge(dry_run=True)
    sequencer = MacroSequencer(bridge=bridge, macros_file=str(macros_path))
    assert sequencer.macros == {}
