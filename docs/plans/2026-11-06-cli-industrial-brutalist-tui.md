# Jarmvis Minimalist Terminal User Interface

> **Execution:** Follow this plan task-by-task. Built with clean, premium design engineering (`ui-ux-pro-max` + `karpathy-guidelines`): zero emojis, zero pseudo-hacker fluff, zero sci-fi clutter. Pure, elegant typography, generous whitespace, sharp hairline borders, and an in-place live acoustic audio bubble.

**Goal:** Build a sleek, minimalist CLI interface for `./jarmvis` with an in-place transient audio recording capsule (live decibel level meter) and clean typographic conversation layout.

**Architecture:** A standalone renderer module `src/jarmvis/tui.py` leveraging `rich` for non-flickering, non-scrolling terminal output. Live audio RMS energy dynamically drives an in-place volume capsule during speech that cleanly disappears once transcribed, printing a clean, beautiful dialogue exchange into the terminal.

**Tech Stack:** Python 3.10+, `rich>=13.7.0`, `numpy`, `pytest`, `sounddevice`.

---

## Visual Design System & Aesthetics
- **Zero Emojis:** Strictly banned.
- **Zero Pseudo-Hacker Gimmicks:** No fake protocols, no `///`, no `>>>`, no raw matrix/scrolling text dumps.
- **Palette (Subtle OLED Dark):**
  - Background: Terminal default / Deep OLED Dark (`#0F172A`)
  - Accent / Prompts: Crisp Cyan (`#38BDF8`)
  - Response Text: High-contrast Off-White (`#F8FAFC`)
  - Metadata / Details: Muted Slate (`#64748B`)
  - Success / Active: Calm Emerald (`#34D399`)
- **The In-Place Audio Capsule:**
  Rendered using `rich.live.Live` with `transient=True`. It never scrolls your terminal window:
  ```
  ╭──────────────────────────────────────────────╮
  │  Listening    ·····••••••••······   -18 dB   │
  ╰──────────────────────────────────────────────╯
  ```
  When transcribing:
  ```
  ╭──────────────────────────────────────────────╮
  │  Transcribing speech...                      │
  ╰──────────────────────────────────────────────╯
  ```
- **Post-Transcription Dialogue Layout:**
  Clean, balanced, hairline-bordered message blocks:
  ```
  ┌ User ──────────────────────────────────────────────────────────────┐
  │ Pick up that block                                                 │
  └────────────────────────────────────────────────────────────────────┘
  ┌ Knox ─────────────────────────────────────── [ALERT / PICK_BLOCK] ─┐
  │ On it. Watch and learn how a real bot picks up a block.            │
  └────────────────────────────────────────────────────────────────────┘
  ```

---

## Tasks Overview

- [ ] **Task 1: Add `rich` dependency and build `src/jarmvis/tui.py` layout engine**
- [ ] **Task 2: Implement the in-place transient Audio Capsule & Decibel Meter**
- [ ] **Task 3: Integrate `tui.py` into `JarmvisApp` (`src/jarmvis/app.py`) for live voice and interactive CLI**

---

### Task 1: Minimalist Terminal UI Engine (`src/jarmvis/tui.py`)

**Files:**
- Modify: `pyproject.toml` (add `rich>=13.7.0`)
- Create: `src/jarmvis/tui.py`
- Test: `tests/test_tui.py`

**Step 1: Write the failing test**

```python
# tests/test_tui.py
import pytest
from jarmvis.tui import TerminalUI

def test_tui_render_banner():
    tui = TerminalUI()
    banner = tui.get_header_banner()
    assert "JARMVIS" in banner
    # Zero emojis
    assert not any(ord(char) > 0x1F000 for char in banner)
    # Zero pseudo-hacker clutter
    assert "///" not in banner
    assert ">>>" not in banner
    assert "PROTOCOL" not in banner

def test_tui_format_dialogue():
    tui = TerminalUI()
    dialogue = tui.format_dialogue(
        user_text="Pick up that block",
        response_text="On it. Watch and learn.",
        face="ALERT",
        macro="PICK_BLOCK"
    )
    assert "Pick up that block" in dialogue
    assert "On it. Watch and learn." in dialogue
    assert "PICK_BLOCK" in dialogue
    assert "ALERT" in dialogue
    # Enforce zero emojis
    assert not any(ord(char) > 0x1F000 for char in dialogue)
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_tui.py -v`  
Expected: FAIL (ModuleNotFoundError: No module named 'jarmvis.tui')

**Step 3: Implement minimal code in `src/jarmvis/tui.py`**
- Create `TerminalUI` wrapping `rich.console.Console`.
- Implement `get_header_banner()` with a clean, centered title and subtle metadata.
- Implement `format_dialogue(user_text, response_text, face, macro)` using clean hairline box-drawing (`┌─┐│└─┘`).

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_tui.py -v`  
Expected: PASS

**Step 5: Commit**
`git commit -am "feat(tui): implement minimalist terminal UI layout engine"`

---

### Task 2: In-Place Audio Capsule & Live Decibel Meter

**Files:**
- Modify: `src/jarmvis/tui.py`
- Test: `tests/test_tui.py`

**Step 1: Write failing test**

```python
# tests/test_tui.py (append)
def test_audio_capsule_silent():
    tui = TerminalUI()
    panel = tui.render_audio_capsule(is_speaking=False, rms_level=0.0001)
    assert "Listening" in panel

def test_audio_capsule_active():
    tui = TerminalUI()
    panel = tui.render_audio_capsule(is_speaking=True, rms_level=0.05)
    assert "Recording" in panel
    assert "dB" in panel
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_tui.py -k test_audio_capsule -v`  
Expected: FAIL

**Step 3: Implement the live audio capsule**
- Implement `calculate_db(rms)` with numerical protection.
- Render dynamic acoustic dot meter (`···••••···`) matching the voice volume.
- Implement `AudioCapsuleContext` using `rich.live.Live(transient=True)` so that it renders in-place without scrolling terminal lines and vanishes cleanly when speech ends.

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_tui.py -v`  
Expected: PASS

**Step 5: Commit**
`git commit -am "feat(tui): add in-place transient audio recording capsule"`

---

### Task 3: Integrate TUI into `JarmvisApp`

**Files:**
- Modify: `src/jarmvis/app.py`
- Test: `tests/test_app.py`

**Step 1: Write failing test**

```python
# tests/test_app.py (append)
def test_app_minimalist_tui(capsys):
    from jarmvis.app import JarmvisApp
    from jarmvis.serial_bridge import SerialBridge
    bridge = SerialBridge(dry_run=True)
    app = JarmvisApp(bridge=bridge, use_mock_ai=True)
    app.handle_voice_prompt("Pick up the block")
    out = capsys.readouterr().out
    assert "Pick up the block" in out
    assert not any(ord(char) > 0x1F000 for char in out)
    assert "///" not in out
```

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_app.py -k test_app_minimalist_tui -v`  
Expected: FAIL

**Step 3: Wire TUI into `app.py`**
- Initialize `TerminalUI` in `JarmvisApp`.
- Print header banner on startup.
- In `_audio_callback`, feed live RMS energy into the audio capsule.
- In `handle_voice_prompt`, render the clean dialogue panel instead of raw print logs.
- Handle `Ctrl+C` with clean cursor restoration.

**Step 4: Run full test suite to verify 100% pass**
Run: `pytest tests/ -v`  
Expected: 100% PASS across all tests.

**Step 5: Final Commit & Push**
`git commit -am "feat(cli): integrate aesthetic minimalist TUI and live audio capsule"`  
`git push origin main`
