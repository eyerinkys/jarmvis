import io
import pytest
from rich.console import Console
from jarmvis.tui import TerminalUI

def test_tui_banner():
    buffer = io.StringIO()
    test_console = Console(file=buffer, color_system=None, width=100)
    tui = TerminalUI(console_instance=test_console)
    tui.play_hud_boot(skip=True)
    tui.print_banner()
    output = buffer.getvalue()
    assert "KNOX" in output
    # Zero emojis
    assert not any(ord(char) > 0x1F000 for char in output)

def test_tui_audio_capsule():
    tui = TerminalUI()
    capsule_quiet = tui.create_audio_capsule(is_speaking=False, rms_level=0.0)
    assert capsule_quiet is not None

    capsule_speaking = tui.create_audio_capsule(is_speaking=True, rms_level=0.05)
    assert capsule_speaking is not None

def test_tui_transcribing_capsule():
    tui = TerminalUI()
    capsule = tui.create_transcribing_capsule()
    assert capsule is not None

def test_tui_print_dialogue():
    buffer = io.StringIO()
    test_console = Console(file=buffer, color_system=None)
    tui = TerminalUI(console_instance=test_console)
    tui.print_dialogue(
        user_text="Pick up the screwdriver",
        response_text="Right away.",
        face="ALERT",
        macro="PICK_BLOCK"
    )
    output = buffer.getvalue()
    assert "Pick up the screwdriver" in output
    assert "Right away." in output
    assert "Knox" in output
    assert "alert" in output
    assert "pick_block" in output

def test_tui_print_status():
    buffer = io.StringIO()
    test_console = Console(file=buffer, color_system=None)
    tui = TerminalUI(console_instance=test_console)
    tui.print_status("System ready.")
    output = buffer.getvalue()
    assert "System ready." in output
