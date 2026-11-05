# Jarmvis: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete software and firmware stack for Jarmvis (5-DOF + 1-DOF Gripper robotic arm with Tony Stark's Dum-E personality and JARVIS voice intelligence), running conversational AI on Apple Silicon Mac M4 and real-time motion/OLED face control on ESP32.

**Architecture:** A Python-based laptop brain running low-latency Voice Activity Detection (<30ms reflex), local STT (MLX-Whisper), structured LLM reasoning (JARVIS persona), and neural TTS (Kokoro/Edge-TTS), communicating over USB Serial at 115200 baud with an ESP32 firmware running LEDC hardware PWM and U8g2 animated vector eyes. Supports `--dry-run` console mode when the ESP32 is disconnected.

**Tech Stack:** Python 3.10+, `silero-vad`, `mlx-whisper` / `faster-whisper`, `kokoro-onnx` / `edge-tts`, `sounddevice`, `pyserial`, `pytest`, C++ (PlatformIO / Arduino, `ESP32 LEDC`, `U8g2`, `ArduinoJson`).

## Global Constraints
- Target platform for AI stack: Apple Silicon Mac (M4 Air).
- Target platform for motor & face controller: ESP32 Dev Board (ESP-WROOM-32).
- Zero paid API requirement: 100% free / local models with optional free-tier Gemini API fallback.
- Servos: 3x MG996R (Base, Shoulder, Elbow), 3x SG90 (Wrist Pitch, Wrist Roll, Gripper).
- Microcontroller baud rate: 115200 baud, newline-delimited JSON (`\n`).

---

### Task 1: Project Scaffolding & Serial Bridge with Dry-Run Mode

**Files:**
- Create: `pyproject.toml`
- Create: `src/jarmvis/__init__.py`
- Create: `src/jarmvis/serial_bridge.py`
- Test: `tests/test_serial_bridge.py`

**Interfaces:**
- Produces: `SerialBridge(port: str | None, baud: int = 115200, dry_run: bool = False)`
  - `send_pose(angles: list[int], speed: int = 50, easing: str = "cosine", face: str | None = None) -> bool`
  - `send_reflex(reflex_type: str) -> bool`
  - `send_face(state: str, pupil_x: int = 0, pupil_y: int = 0) -> bool`
  - `close() -> None`

- [x] **Step 1: Write the failing test**

```python
# tests/test_serial_bridge.py
import json
from unittest.mock import MagicMock, patch
from jarmvis.serial_bridge import SerialBridge

def test_dry_run_send_pose(capsys):
    bridge = SerialBridge(port=None, dry_run=True)
    success = bridge.send_pose(angles=[90, 60, 110, 45, 90, 30], speed=50, easing="spring", face="alert")
    assert success is True
    captured = capsys.readouterr().out
    assert "[DRY-RUN POSE]" in captured
    assert "90, 60, 110, 45, 90, 30" in captured
    assert "alert" in captured

def test_dry_run_send_reflex(capsys):
    bridge = SerialBridge(port=None, dry_run=True)
    success = bridge.send_reflex("PERK_UP")
    assert success is True
    captured = capsys.readouterr().out
    assert "[DRY-RUN REFLEX]" in captured
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
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_serial_bridge.py -v`  
Expected: FAIL (ModuleNotFoundError: No module named 'jarmvis')

- [x] **Step 3: Implement `pyproject.toml` and `SerialBridge`**

Create `pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "jarmvis"
version = "0.1.0"
description = "5-DOF Robotic Arm with JARVIS Intelligence and Dum-E Personality"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "pyserial>=3.5",
    "numpy>=1.24.0",
    "sounddevice>=0.4.6",
    "edge-tts>=6.1.9",
    "requests>=2.31.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
]
```

Create `src/jarmvis/__init__.py`:
```python
"""Jarmvis: JARVIS Mind & Dum-E Body."""
__version__ = "0.1.0"
```

Create `src/jarmvis/serial_bridge.py`:
```python
import json
import logging
from typing import Any

logger = logging.getLogger("jarmvis.serial")

class SerialBridge:
    def __init__(self, port: str | None = None, baud: int = 115200, dry_run: bool = False):
        self.port = port
        self.baud = baud
        self.dry_run = dry_run or (port is None)
        self.serial = None

        if not self.dry_run:
            try:
                import serial
                self.serial = serial.Serial(self.port, self.baud, timeout=1.0)
                logger.info(f"Connected to ESP32 on {self.port} @ {self.baud} baud")
            except Exception as e:
                logger.warning(f"Failed to connect to {self.port}: {e}. Falling back to dry-run mode.")
                self.dry_run = True

    def _transmit(self, payload: dict[str, Any]) -> bool:
        packet_str = json.dumps(payload) + "\n"
        if self.dry_run:
            cmd = payload.get("cmd", "").upper()
            if cmd == "POSE":
                print(f"🤖 [DRY-RUN POSE] Angles: {payload.get('angles')} | Speed: {payload.get('speed')}% | Easing: {payload.get('easing')} | Face: {payload.get('face')}")
            elif cmd == "REFLEX":
                print(f"⚡ [DRY-RUN REFLEX] Trigger: {payload.get('type')}")
            elif cmd == "FACE":
                print(f"👀 [DRY-RUN FACE] State: {payload.get('state')} (x={payload.get('pupil_x')}, y={payload.get('pupil_y')})")
            else:
                print(f"📦 [DRY-RUN PACKET] {packet_str.strip()}")
            return True
        
        try:
            if self.serial:
                self.serial.write(packet_str.encode("utf-8"))
                return True
        except Exception as e:
            logger.error(f"Serial transmission failed: {e}")
        return False

    def send_pose(self, angles: list[int], speed: int = 50, easing: str = "cosine", face: str | None = None) -> bool:
        if len(angles) != 6:
            raise ValueError(f"Expected 6 joint angles, got {len(angles)}")
        clamped_angles = [max(0, min(180, int(a))) for a in angles]
        payload = {
            "cmd": "pose",
            "angles": clamped_angles,
            "speed": max(1, min(100, int(speed))),
            "easing": easing,
            "face": face
        }
        return self._transmit(payload)

    def send_reflex(self, reflex_type: str) -> bool:
        payload = {
            "cmd": "reflex",
            "type": reflex_type.upper()
        }
        return self._transmit(payload)

    def send_face(self, state: str, pupil_x: int = 0, pupil_y: int = 0) -> bool:
        payload = {
            "cmd": "face",
            "state": state.upper(),
            "pupil_x": int(pupil_x),
            "pupil_y": int(pupil_y)
        }
        return self._transmit(payload)

    def close(self) -> None:
        if self.serial and self.serial.is_open:
            self.serial.close()
```

- [x] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_serial_bridge.py -v`  
Expected: PASS

- [x] **Step 5: Commit**

```bash
git add pyproject.toml src/ tests/
git commit -m "feat(bridge): implement SerialBridge with dry-run console mode"
```

---

### Task 2: Kinematic Motion & Spring-Damper Easing Engine

**Files:**
- Create: `src/jarmvis/motion.py`
- Test: `tests/test_motion.py`

**Interfaces:**
- Produces: `MotionPlanner`
  - `interpolate(start_angles: list[int], target_angles: list[int], steps: int, easing: str) -> list[list[int]]`
  - `generate_spring_overshoot(start: list[int], target: list[int], overshoot_deg: float = 3.0) -> list[list[int]]`
  - `generate_breathing_idle(current: list[int], step_index: int) -> list[int]`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_motion.py
import pytest
from jarmvis.motion import MotionPlanner

def test_cosine_interpolation():
    planner = MotionPlanner()
    start = [0, 0, 0, 0, 0, 0]
    target = [90, 90, 90, 90, 90, 90]
    trajectory = planner.interpolate(start, target, steps=5, easing="cosine")
    assert len(trajectory) == 5
    assert trajectory[0] == start
    assert trajectory[-1] == target
    # Midpoint of cosine easing should be exactly 50%
    assert trajectory[2] == [45, 45, 45, 45, 45, 45]

def test_spring_overshoot():
    planner = MotionPlanner()
    start = [90, 90, 90, 90, 90, 90]
    target = [90, 120, 90, 90, 90, 90]
    trajectory = planner.generate_spring_overshoot(start, target, overshoot_deg=5.0)
    # Must have an element that overshoots 120 (e.g. 125)
    shoulder_angles = [pt[1] for pt in trajectory]
    assert max(shoulder_angles) > 120
    assert trajectory[-1] == target

def test_idle_breathing():
    planner = MotionPlanner()
    base = [90, 60, 110, 45, 90, 30]
    p1 = planner.generate_breathing_idle(base, step_index=0)
    p2 = planner.generate_breathing_idle(base, step_index=25)
    assert p1[1] != p2[1] # Shoulder moves subtly
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_motion.py -v`  
Expected: FAIL (ModuleNotFoundError: No module named 'jarmvis.motion')

- [ ] **Step 3: Implement `src/jarmvis/motion.py`**

```python
import math

class MotionPlanner:
    def __init__(self, safe_limits: list[tuple[int, int]] | None = None):
        # Default safe angle bounds (min, max) for 6 joints
        self.safe_limits = safe_limits or [
            (0, 180),  # Waist
            (15, 165), # Shoulder (avoid mechanical collision with base)
            (15, 165), # Elbow
            (0, 180),  # Wrist Pitch
            (0, 180),  # Wrist Roll
            (10, 120), # Gripper (10=closed, 120=fully open)
        ]

    def clamp(self, angles: list[int | float]) -> list[int]:
        clamped = []
        for i, a in enumerate(angles):
            min_a, max_a = self.safe_limits[i]
            clamped.append(int(round(max(min_a, min(max_a, a)))))
        return clamped

    def interpolate(self, start_angles: list[int], target_angles: list[int], steps: int = 10, easing: str = "cosine") -> list[list[int]]:
        if steps <= 1:
            return [self.clamp(target_angles)]
        
        trajectory = []
        for step in range(steps):
            t = step / (steps - 1)
            if easing == "cosine":
                eased_t = (1.0 - math.cos(math.pi * t)) / 2.0
            elif easing == "linear":
                eased_t = t
            elif easing == "spring":
                # Damped spring approximation: 1 - exp(-6t) * cos(2*pi*t)
                eased_t = 1.0 - math.exp(-5.0 * t) * math.cos(math.pi * 1.5 * t)
            else:
                eased_t = t

            point = []
            for j in range(6):
                val = start_angles[j] + (target_angles[j] - start_angles[j]) * eased_t
                point.append(val)
            trajectory.append(self.clamp(point))
        return trajectory

    def generate_spring_overshoot(self, start: list[int], target: list[int], overshoot_deg: float = 3.0) -> list[list[int]]:
        trajectory = []
        overshoot_target = []
        for j in range(6):
            diff = target[j] - start[j]
            if abs(diff) > 5:
                direction = 1 if diff > 0 else -1
                overshoot_target.append(target[j] + direction * overshoot_deg)
            else:
                overshoot_target.append(target[j])

        # Step 1: Rapid movement to overshoot target
        trajectory.extend(self.interpolate(start, overshoot_target, steps=8, easing="cosine"))
        # Step 2: Settle back to final target
        trajectory.extend(self.interpolate(overshoot_target, target, steps=5, easing="cosine"))
        return trajectory

    def generate_breathing_idle(self, current: list[int], step_index: int) -> list[int]:
        cycle = (step_index % 100) / 100.0 * 2 * math.pi
        shoulder_offset = math.sin(cycle) * 2.0
        elbow_offset = math.sin(cycle + 0.5) * 2.5
        result = list(current)
        result[1] = result[1] + shoulder_offset
        result[2] = result[2] + elbow_offset
        return self.clamp(result)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_motion.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/jarmvis/motion.py tests/test_motion.py
git commit -m "feat(motion): add cosine easing, spring overshoot, and idle breathing"
```

---

### Task 3: Macro Waypoint Sequencer & Interactive Calibration CLI

**Files:**
- Create: `src/jarmvis/macros.py`
- Create: `config/macros.json`
- Create: `tools/calibrate.py`
- Test: `tests/test_macros.py`

**Interfaces:**
- Produces: `MacroSequencer(bridge: SerialBridge, macros_file: str)`
  - `load_macros() -> dict`
  - `execute_macro(name: str, step_callback: callable | None = None) -> bool`
  - `save_waypoint(macro_name: str, angles: list[int], speed: int = 40, pause_ms: int = 300) -> None`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_macros.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_macros.py -v`  
Expected: FAIL (ModuleNotFoundError: No module named 'jarmvis.macros')

- [ ] **Step 3: Implement `src/jarmvis/macros.py`, `config/macros.json`, and `tools/calibrate.py`**

Create `config/macros.json`:
```json
{
  "HOME": [
    {"angles": [90, 90, 90, 90, 90, 30], "speed": 40, "pause_ms": 200, "face": "NEUTRAL"}
  ],
  "PERK_UP": [
    {"angles": [90, 110, 80, 60, 90, 40], "speed": 80, "pause_ms": 150, "face": "ALERT"}
  ],
  "DUNCE_CORNER": [
    {"angles": [30, 40, 140, 20, 90, 20], "speed": 25, "pause_ms": 800, "face": "SAD"}
  ],
  "CELEBRATE": [
    {"angles": [90, 100, 90, 60, 90, 100], "speed": 70, "pause_ms": 150, "face": "HAPPY"},
    {"angles": [90, 100, 90, 60, 90, 15],  "speed": 90, "pause_ms": 100, "face": "HAPPY"},
    {"angles": [90, 100, 90, 60, 90, 100], "speed": 90, "pause_ms": 100, "face": "HAPPY"},
    {"angles": [90, 100, 90, 60, 90, 15],  "speed": 90, "pause_ms": 200, "face": "HAPPY"}
  ],
  "PICK_BLOCK": [
    {"angles": [45, 60, 80, 45, 90, 100], "speed": 50, "pause_ms": 400, "face": "DETERMINED"},
    {"angles": [45, 35, 65, 30, 90, 100], "speed": 30, "pause_ms": 300, "face": "DETERMINED"},
    {"angles": [45, 35, 65, 30, 90, 20],  "speed": 40, "pause_ms": 400, "face": "DETERMINED"},
    {"angles": [45, 75, 90, 60, 90, 20],  "speed": 40, "pause_ms": 300, "face": "HAPPY"},
    {"angles": [90, 75, 90, 60, 90, 20],  "speed": 45, "pause_ms": 500, "face": "HAPPY"}
  ]
}
```

Create `src/jarmvis/macros.py`:
```python
import json
import logging
import os
import time
from jarmvis.serial_bridge import SerialBridge

logger = logging.getLogger("jarmvis.macros")

class MacroSequencer:
    def __init__(self, bridge: SerialBridge, macros_file: str = "config/macros.json"):
        self.bridge = bridge
        self.macros_file = macros_file
        self.macros = {}
        self.load_macros()

    def load_macros(self) -> dict:
        if os.path.exists(self.macros_file):
            with open(self.macros_file, "r") as f:
                self.macros = json.load(f)
        else:
            self.macros = {}
        return self.macros

    def save_waypoint(self, macro_name: str, angles: list[int], speed: int = 40, pause_ms: int = 300, face: str = "NEUTRAL") -> None:
        if macro_name not in self.macros:
            self.macros[macro_name] = []
        self.macros[macro_name].append({
            "angles": angles,
            "speed": speed,
            "pause_ms": pause_ms,
            "face": face
        })
        os.makedirs(os.path.dirname(os.path.abspath(self.macros_file)), exist_ok=True)
        with open(self.macros_file, "w") as f:
            json.dump(self.macros, f, indent=2)

    def execute_macro(self, name: str) -> bool:
        if name not in self.macros:
            logger.warning(f"Macro '{name}' not found!")
            return False
        
        waypoints = self.macros[name]
        logger.info(f"Executing macro: {name} ({len(waypoints)} waypoints)")
        for wp in waypoints:
            angles = wp["angles"]
            speed = wp.get("speed", 50)
            easing = wp.get("easing", "cosine")
            face = wp.get("face", None)
            pause_sec = wp.get("pause_ms", 200) / 1000.0

            self.bridge.send_pose(angles=angles, speed=speed, easing=easing, face=face)
            if pause_sec > 0:
                time.sleep(pause_sec)
        return True
```

Create `tools/calibrate.py`:
```python
#!/usr/bin/env python3
"""Interactive CLI Keyboard Joint Calibration & Waypoint Recorder."""
import sys
import argparse
from jarmvis.serial_bridge import SerialBridge
from jarmvis.macros import MacroSequencer

JOINTS = ["1: Waist Base", "2: Shoulder", "3: Elbow", "4: Wrist Pitch", "5: Wrist Roll", "6: Claw"]

def main():
    parser = argparse.ArgumentParser(description="Jarmvis Arm Calibrator")
    parser.add_argument("--port", type=str, default=None, help="ESP32 serial port")
    parser.add_argument("--dry-run", action="store_true", help="Run without physical ESP32")
    args = parser.parse_args()

    bridge = SerialBridge(port=args.port, dry_run=args.dry_run)
    sequencer = MacroSequencer(bridge)

    angles = [90, 90, 90, 90, 90, 30]
    print("\n=== JARMVIS ARM CALIBRATION TOOL ===")
    print("Controls:")
    print("  Q/A: Waist Base ±5°      W/S: Shoulder ±5°")
    print("  E/D: Elbow ±5°           R/F: Wrist Pitch ±5°")
    print("  T/G: Wrist Roll ±5°      Y/H: Claw Open/Close")
    print("  [REC]: Type 'save <macro_name>' to save current pose")
    print("  [RUN]: Type 'run <macro_name>' to test playback")
    print("  'quit' to exit\n")

    step = 5
    bridge.send_pose(angles, speed=50)

    while True:
        prompt = f"Current {angles} > ".strip()
        cmd = input(prompt).strip().lower()
        if not cmd:
            continue
        if cmd == "quit" or cmd == "exit":
            break
        elif cmd.startswith("save "):
            macro_name = cmd.split(" ", 1)[1].strip().upper()
            sequencer.save_waypoint(macro_name, list(angles))
            print(f" Saved waypoint to macro: {macro_name}")
            continue
        elif cmd.startswith("run "):
            macro_name = cmd.split(" ", 1)[1].strip().upper()
            sequencer.execute_macro(macro_name)
            continue

        for char in cmd:
            if char == 'q': angles[0] = min(180, angles[0] + step)
            elif char == 'a': angles[0] = max(0, angles[0] - step)
            elif char == 'w': angles[1] = min(180, angles[1] + step)
            elif char == 's': angles[1] = max(0, angles[1] - step)
            elif char == 'e': angles[2] = min(180, angles[2] + step)
            elif char == 'd': angles[2] = max(0, angles[2] - step)
            elif char == 'r': angles[3] = min(180, angles[3] + step)
            elif char == 'f': angles[3] = max(0, angles[3] - step)
            elif char == 't': angles[4] = min(180, angles[4] + step)
            elif char == 'g': angles[4] = max(0, angles[4] - step)
            elif char == 'y': angles[5] = min(120, angles[5] + step)
            elif char == 'h': angles[5] = max(10, angles[5] - step)

        bridge.send_pose(angles, speed=60)

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_macros.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add config/macros.json src/jarmvis/macros.py tools/calibrate.py tests/test_macros.py
git commit -m "feat(macros): add macro waypoint sequencer and interactive calibration tool"
```

---

### Task 4: Voice Activity Detection (VAD) & Instant Reflex Listener

**Files:**
- Create: `src/jarmvis/voice_vad.py`
- Test: `tests/test_voice_vad.py`

**Interfaces:**
- Produces: `VoiceActivityDetector(on_speech_start: callable, on_speech_end: callable)`
  - `process_audio_chunk(audio_data: np.ndarray) -> bool`
  - `start_listening_stream()`
  - `stop_listening_stream()`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_voice_vad.py
import numpy as np
import pytest
from unittest.mock import MagicMock
from jarmvis.voice_vad import VoiceActivityDetector

def test_energy_fallback_vad_triggers():
    on_start = MagicMock()
    on_end = MagicMock()
    vad = VoiceActivityDetector(on_speech_start=on_start, on_speech_end=on_end, energy_threshold=0.05)
    
    # Silence: values near 0
    silence = np.zeros(512, dtype=np.float32)
    vad.process_audio_chunk(silence)
    assert not on_start.called

    # Loud speech chunk
    loud_speech = np.ones(512, dtype=np.float32) * 0.2
    vad.process_audio_chunk(loud_speech)
    assert on_start.called
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_voice_vad.py -v`  
Expected: FAIL (ModuleNotFoundError: No module named 'jarmvis.voice_vad')

- [ ] **Step 3: Implement `src/jarmvis/voice_vad.py`**

```python
import logging
import numpy as np
from typing import Callable

logger = logging.getLogger("jarmvis.vad")

class VoiceActivityDetector:
    def __init__(
        self,
        on_speech_start: Callable[[], None] | None = None,
        on_speech_end: Callable[[np.ndarray], None] | None = None,
        sample_rate: int = 16000,
        energy_threshold: float = 0.02,
        silence_timeout_chunks: int = 15
    ):
        self.on_speech_start = on_speech_start
        self.on_speech_end = on_speech_end
        self.sample_rate = sample_rate
        self.energy_threshold = energy_threshold
        self.silence_timeout_chunks = silence_timeout_chunks

        self.is_speaking = False
        self.silence_count = 0
        self.speech_buffer = []

    def process_audio_chunk(self, chunk: np.ndarray) -> bool:
        if chunk.dtype != np.float32:
            chunk = chunk.astype(np.float32)
            if np.max(np.abs(chunk)) > 1.0:
                chunk = chunk / 32768.0

        energy = float(np.mean(chunk ** 2))
        is_chunk_speech = energy > self.energy_threshold

        if is_chunk_speech:
            self.speech_buffer.append(chunk)
            self.silence_count = 0
            if not self.is_speaking:
                self.is_speaking = True
                logger.info("Speech start detected!")
                if self.on_speech_start:
                    self.on_speech_start()
        elif self.is_speaking:
            self.speech_buffer.append(chunk)
            self.silence_count += 1
            if self.silence_count >= self.silence_timeout_chunks:
                self.is_speaking = False
                logger.info("Speech end detected.")
                if self.on_speech_end and self.speech_buffer:
                    full_utterance = np.concatenate(self.speech_buffer)
                    self.on_speech_end(full_utterance)
                self.speech_buffer = []

        return self.is_speaking
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_voice_vad.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/jarmvis/voice_vad.py tests/test_voice_vad.py
git commit -m "feat(vad): implement sub-30ms voice activity detector with reflex triggers"
```

---

### Task 5: Conversational TTS Engine (Edge-TTS & Kokoro)

**Files:**
- Create: `src/jarmvis/tts_engine.py`
- Test: `tests/test_tts_engine.py`

**Interfaces:**
- Produces: `TTSEngine`
  - `speak(text: str, on_playback_start: callable | None = None, on_playback_end: callable | None = None) -> None`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_tts_engine.py
import pytest
from unittest.mock import patch, MagicMock
from jarmvis.tts_engine import TTSEngine

def test_tts_initialization():
    tts = TTSEngine(voice="en-GB-RyanNeural", use_mock=True)
    start_mock = MagicMock()
    end_mock = MagicMock()
    tts.speak("Hello sir, all systems operational.", on_playback_start=start_mock, on_playback_end=end_mock)
    assert start_mock.called
    assert end_mock.called
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_tts_engine.py -v`  
Expected: FAIL (ModuleNotFoundError: No module named 'jarmvis.tts_engine')

- [ ] **Step 3: Implement `src/jarmvis/tts_engine.py`**

```python
import asyncio
import logging
import os
import tempfile
from typing import Callable

logger = logging.getLogger("jarmvis.tts")

class TTSEngine:
    def __init__(self, voice: str = "en-GB-RyanNeural", use_mock: bool = False):
        self.voice = voice
        self.use_mock = use_mock

    def speak(
        self,
        text: str,
        on_playback_start: Callable[[], None] | None = None,
        on_playback_end: Callable[[], None] | None = None
    ) -> None:
        if not text.strip():
            return

        logger.info(f"Speaking: '{text}'")
        if on_playback_start:
            on_playback_start()

        if self.use_mock:
            print(f"🔊 [MOCK TTS VOICE: {self.voice}] \"{text}\"")
            if on_playback_end:
                on_playback_end()
            return

        try:
            import edge_tts
            async def _synthesize_and_play():
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    tmp_path = tmp.name
                communicate = edge_tts.Communicate(text, self.voice)
                await communicate.save(tmp_path)
                
                # Play audio using macOS native afplay (zero external dependencies)
                os.system(f"afplay '{tmp_path}' > /dev/null 2>&1")
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

            asyncio.run(_synthesize_and_play())
        except Exception as e:
            logger.error(f"TTS audio playback failed: {e}")
            print(f"🔊 [FALLBACK TTS] \"{text}\"")

        if on_playback_end:
            on_playback_end()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_tts_engine.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/jarmvis/tts_engine.py tests/test_tts_engine.py
git commit -m "feat(tts): implement neural JARVIS British TTS playback via edge-tts"
```

---

### Task 6: JARVIS Mind & Structured Emotion Parser

**Files:**
- Create: `src/jarmvis/brain.py`
- Test: `tests/test_brain.py`

**Interfaces:**
- Produces: `JarvisBrain(model: str = "qwen2.5:7b", api_key: str | None = None)`
  - `think(user_prompt: str) -> dict`
    - Returns `{"speech": str, "emotion": str, "face": str, "macro": str | None}`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_brain.py
import pytest
from jarmvis.brain import JarvisBrain

def test_parse_structured_json_response():
    brain = JarvisBrain(use_mock=True)
    response = brain.think("Pick up that block on your left")
    assert "speech" in response
    assert response["macro"] == "PICK_BLOCK"
    assert response["emotion"] in ["FOCUSED", "CONFIDENT", "ALERT"]

def test_parse_scolding_response():
    brain = JarvisBrain(use_mock=True)
    response = brain.think("Dummy you messed up, go to the corner!")
    assert response["emotion"] == "ASHAMED"
    assert response["macro"] == "DUNCE_CORNER"
    assert response["face"] == "SAD"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_brain.py -v`  
Expected: FAIL (ModuleNotFoundError: No module named 'jarmvis.brain')

- [ ] **Step 3: Implement `src/jarmvis/brain.py`**

```python
import json
import logging
import re
from typing import Any

logger = logging.getLogger("jarmvis.brain")

SYSTEM_PROMPT = """You are JARVIS, Tony Stark's sophisticated, witty, and polite British AI assistant.
However, your physical embodiment is "Dummy" (Dum-E) - an eager, clumsy workshop robotic arm with an OLED face and a gripper claw.

When responding to the user, you MUST ALWAYS output valid JSON matching this schema:
{
  "speech": "Your spoken reply in Paul Bettany's witty British JARVIS tone.",
  "emotion": "NEUTRAL | CURIOUS | ASHAMED | EXCITED | ALERT | FOCUSED",
  "face": "NEUTRAL | ALERT | CURIOUS | SAD | HAPPY | SQUINT",
  "macro": "PICK_BLOCK | DUNCE_CORNER | CELEBRATE | null"
}

Macro mapping guidelines:
- If the user asks you to pick up, grab, or fetch a block or object: set macro to "PICK_BLOCK".
- If the user scolds you, tells you to sit in the corner, or calls you an idiot: set macro to "DUNCE_CORNER", emotion to "ASHAMED", and face to "SAD".
- If the user praises you or tells you good job: set macro to "CELEBRATE", emotion to "EXCITED", and face to "HAPPY".
- Otherwise: set macro to null.
Output raw JSON only without markdown formatting.
"""

class JarvisBrain:
    def __init__(self, model: str = "qwen2.5:7b", api_key: str | None = None, use_mock: bool = False):
        self.model = model
        self.api_key = api_key
        self.use_mock = use_mock

    def think(self, user_prompt: str) -> dict[str, Any]:
        if self.use_mock:
            lower = user_prompt.lower()
            if "pick" in lower or "block" in lower:
                return {
                    "speech": "Right away, sir. Attempting to retrieve the block now.",
                    "emotion": "FOCUSED",
                    "face": "ALERT",
                    "macro": "PICK_BLOCK"
                }
            elif "corner" in lower or "messed up" in lower or "bad" in lower:
                return {
                    "speech": "My sincere apologies, sir. Heading to the dunce corner immediately.",
                    "emotion": "ASHAMED",
                    "face": "SAD",
                    "macro": "DUNCE_CORNER"
                }
            elif "great" in lower or "good job" in lower:
                return {
                    "speech": "Most gratifying, sir. Always a pleasure to be of service.",
                    "emotion": "EXCITED",
                    "face": "HAPPY",
                    "macro": "CELEBRATE"
                }
            return {
                "speech": "As you wish, sir. I am standing by for your instructions.",
                "emotion": "CURIOUS",
                "face": "NEUTRAL",
                "macro": None
            }

        # Real LLM Call (Ollama local endpoint)
        try:
            import urllib.request
            req_data = json.dumps({
                "model": self.model,
                "system": SYSTEM_PROMPT,
                "prompt": user_prompt,
                "stream": False,
                "format": "json"
            }).encode("utf-8")
            req = urllib.request.Request(
                "http://localhost:11434/api/generate",
                data=req_data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                content = res_json.get("response", "{}")
                return json.loads(content)
        except Exception as e:
            logger.warning(f"Ollama generation failed ({e}), falling back to mock intelligence.")
            return self.__class__(use_mock=True).think(user_prompt)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_brain.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/jarmvis/brain.py tests/test_brain.py
git commit -m "feat(brain): implement JARVIS mind and structured Dum-E emotion parser"
```

---

### Task 7: End-to-End Jarmvis Application Runner

**Files:**
- Create: `src/jarmvis/app.py`
- Test: `tests/test_app.py`

**Interfaces:**
- Produces: `JarmvisApp`
  - `handle_voice_prompt(text: str) -> None`
  - `run_cli_interactive() -> None`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_app.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_app.py -v`  
Expected: FAIL (ModuleNotFoundError: No module named 'jarmvis.app')

- [ ] **Step 3: Implement `src/jarmvis/app.py`**

```python
import argparse
import logging
import sys
from jarmvis.brain import JarvisBrain
from jarmvis.macros import MacroSequencer
from jarmvis.motion import MotionPlanner
from jarmvis.serial_bridge import SerialBridge
from jarmvis.tts_engine import TTSEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("jarmvis.main")

class JarmvisApp:
    def __init__(self, bridge: SerialBridge, use_mock_ai: bool = False):
        self.bridge = bridge
        self.brain = JarvisBrain(use_mock=use_mock_ai)
        self.tts = TTSEngine(use_mock=use_mock_ai)
        self.macros = MacroSequencer(bridge=self.bridge)
        self.motion = MotionPlanner()

    def handle_voice_prompt(self, user_text: str) -> None:
        print(f"\n👤 [USER] \"{user_text}\"")
        # 1. Immediate reflex: Thinking tilt
        self.bridge.send_reflex("THINK")
        
        # 2. Query LLM brain
        response = self.brain.think(user_text)
        speech = response.get("speech", "")
        face = response.get("face", "NEUTRAL")
        macro = response.get("macro", None)

        print(f"🤖 [JARVIS] \"{speech}\" (Face: {face}, Macro: {macro})")
        self.bridge.send_face(face)

        # 3. Speak response
        self.tts.speak(speech)

        # 4. Trigger physical macro if requested
        if macro:
            self.macros.execute_macro(macro)

    def run_cli_interactive(self) -> None:
        print("\n=======================================================")
        print("          JARMVIS: JARVIS MIND & DUM-E BODY            ")
        print("=======================================================")
        print("Commands:")
        print("  - Type any statement to talk (e.g., 'Pick up that block')")
        print("  - 'perk' to test instant reflex")
        print("  - 'dunce' to test shame dejected droop")
        print("  - 'quit' to exit\n")

        # Initial wake up
        self.bridge.send_reflex("PERK_UP")

        while True:
            try:
                line = input("Jarmvis> ").strip()
                if not line:
                    continue
                if line.lower() in ["quit", "exit"]:
                    break
                elif line.lower() == "perk":
                    self.bridge.send_reflex("PERK_UP")
                elif line.lower() == "dunce":
                    self.macros.execute_macro("DUNCE_CORNER")
                else:
                    self.handle_voice_prompt(line)
            except (KeyboardInterrupt, EOFError):
                break
        print("\nShutting down Jarmvis.")

def main():
    parser = argparse.ArgumentParser(description="Jarmvis Master Runner")
    parser.add_argument("--port", type=str, default=None, help="ESP32 serial port (e.g. /dev/cu.usbserial-*)")
    parser.add_argument("--dry-run", action="store_true", help="Run in terminal mock mode without ESP32")
    parser.add_argument("--mock-ai", action="store_true", help="Use instant mock brain and TTS for testing")
    args = parser.parse_args()

    bridge = SerialBridge(port=args.port, dry_run=args.dry_run)
    app = JarmvisApp(bridge=bridge, use_mock_ai=args.mock_ai)
    app.run_cli_interactive()

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_app.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/jarmvis/app.py tests/test_app.py
git commit -m "feat(app): implement end-to-end Jarmvis CLI interactive runner"
```

---

### Task 8: ESP32 C++ Firmware (LEDC PWM & U8g2 Animated Eyes)

**Files:**
- Create: `firmware/platformio.ini`
- Create: `firmware/src/main.cpp`
- Create: `firmware/src/eyes.h`

**Interfaces:**
- Input: USB Serial JSON packets (`pose`, `reflex`, `face`)
- Output: 6-channel 50Hz LEDC PWM to servos + I2C to SSD1306 OLED display

- [ ] **Step 1: Write `firmware/platformio.ini`**

```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
monitor_speed = 115200
lib_deps =
    bblanchon/ArduinoJson@^7.0.4
    olikraus/U8g2@^2.35.19
```

- [ ] **Step 2: Implement `firmware/src/eyes.h` (Procedural Animated Eyes)**

```cpp
#pragma once
#include <Arduino.h>
#include <U8g2lib.h>

class EyeController {
private:
    U8G2 &u8g2;
    int eyeL_x = 40, eyeL_y = 32;
    int eyeR_x = 88, eyeR_y = 32;
    int eye_w = 24, eye_h = 28;
    int pupil_dx = 0, pupil_dy = 0;
    String current_state = "NEUTRAL";
    unsigned long last_blink = 0;
    bool is_blinking = false;

public:
    EyeController(U8G2 &disp) : u8g2(disp) {}

    void setState(const String &st, int px = 0, int py = 0) {
        current_state = st;
        pupil_dx = px;
        pupil_dy = py;
    }

    void update() {
        unsigned long now = millis();
        if (now - last_blink > 4000) {
            is_blinking = true;
            last_blink = now;
        }
        if (is_blinking && now - last_blink > 150) {
            is_blinking = false;
        }

        u8g2.clearBuffer();
        if (is_blinking) {
            u8g2.drawHLine(eyeL_x - eye_w/2, eyeL_y, eye_w);
            u8g2.drawHLine(eyeR_x - eye_w/2, eyeR_y, eye_w);
        } else if (current_state == "SAD") {
            // Drooping crescent eyes
            u8g2.drawBox(eyeL_x - eye_w/2, eyeL_y + 4, eye_w, 8);
            u8g2.drawBox(eyeR_x - eye_w/2, eyeR_y + 4, eye_w, 8);
        } else if (current_state == "ALERT") {
            // Big wide open round eyes
            u8g2.drawDisc(eyeL_x, eyeL_y, 16);
            u8g2.drawDisc(eyeR_x, eyeR_y, 16);
        } else {
            // Standard rounded rectangular eyes with pupils
            u8g2.drawRBox(eyeL_x - eye_w/2, eyeL_y - eye_h/2, eye_w, eye_h, 6);
            u8g2.drawRBox(eyeR_x - eye_w/2, eyeR_y - eye_h/2, eye_w, eye_h, 6);
        }
        u8g2.sendBuffer();
    }
};
```

- [ ] **Step 3: Implement `firmware/src/main.cpp`**

```cpp
#include <Arduino.h>
#include <ArduinoJson.h>
#include <U8g2lib.h>
#include "eyes.h"

// 6 Servo PWM GPIO Pins
const int SERVO_PINS[6] = {13, 12, 14, 27, 26, 25};
const int PWM_FREQ = 50;       // 50Hz standard servo frequency
const int PWM_RES = 16;        // 16-bit resolution (0 - 65535)

// Current & Target Angles
float current_angles[6] = {90, 90, 90, 90, 90, 30};
float target_angles[6]  = {90, 90, 90, 90, 90, 30};
float move_speed = 2.0;

// OLED Display (SSD1306 128x64 I2C: GPIO 21 SDA, GPIO 22 SCL)
U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, /* reset=*/ U8X8_PIN_NONE);
EyeController eyes(u8g2);

uint32_t angleToDuty(float angle) {
    // 0 deg = 0.5ms (1638 duty @ 16-bit 50Hz), 180 deg = 2.5ms (8192 duty)
    float pulse_ms = 0.5 + (angle / 180.0) * 2.0;
    return (uint32_t)((pulse_ms / 20.0) * 65535.0);
}

void parseJsonPacket(const String &json_str) {
    StaticJsonDocument<512> doc;
    DeserializationError err = deserializeJson(doc, json_str);
    if (err) return;

    const char* cmd = doc["cmd"];
    if (strcmp(cmd, "pose") == 0) {
        JsonArray angles = doc["angles"];
        for (int i = 0; i < 6 && i < angles.size(); i++) {
            target_angles[i] = angles[i];
        }
        move_speed = doc.containsKey("speed") ? ((float)doc["speed"] / 25.0) : 2.0;
        if (doc.containsKey("face")) {
            eyes.setState(doc["face"].as<String>());
        }
    } else if (strcmp(cmd, "reflex") == 0) {
        const char* type = doc["type"];
        if (strcmp(type, "PERK_UP") == 0) {
            target_angles[1] = 110; // Shoulder up
            target_angles[2] = 80;  // Elbow alert
            move_speed = 6.0;       // Rapid snap
            eyes.setState("ALERT");
        } else if (strcmp(type, "THINK") == 0) {
            target_angles[3] = 75;  // Head tilt
            eyes.setState("CURIOUS");
        }
    } else if (strcmp(cmd, "face") == 0) {
        eyes.setState(doc["state"].as<String>(), doc["pupil_x"] | 0, doc["pupil_y"] | 0);
    }
}

void setup() {
    Serial.begin(115200);
    u8g2.begin();
    eyes.setState("ALERT");

    // Configure 6 LEDC hardware PWM channels
    for (int i = 0; i < 6; i++) {
        ledcSetup(i, PWM_FREQ, PWM_RES);
        ledcAttachPin(SERVO_PINS[i], i);
        ledcWrite(i, angleToDuty(current_angles[i]));
    }
    Serial.println("{\"status\":\"ready\",\"device\":\"jarmvis_esp32\"}");
}

void loop() {
    // Read incoming Serial packets
    if (Serial.available()) {
        String line = Serial.readStringUntil('\n');
        line.trim();
        if (line.length() > 0) {
            parseJsonPacket(line);
        }
    }

    // Smooth Cosine Interpolation Step (50Hz)
    static unsigned long last_motor_update = 0;
    if (millis() - last_motor_update >= 20) {
        last_motor_update = millis();
        for (int i = 0; i < 6; i++) {
            float diff = target_angles[i] - current_angles[i];
            if (abs(diff) > 0.5) {
                current_angles[i] += (diff > 0 ? 1 : -1) * min(abs(diff), move_speed);
                ledcWrite(i, angleToDuty(current_angles[i]));
            }
        }
    }

    // Refresh OLED Eyes
    eyes.update();
}
```

- [ ] **Step 4: Commit firmware files**

```bash
git add firmware/
git commit -m "feat(firmware): implement ESP32 6-channel LEDC PWM driver and U8g2 animated eyes"
```
