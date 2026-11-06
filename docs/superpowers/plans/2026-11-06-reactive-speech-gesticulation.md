# Reactive Speech-Driven Gesticulation Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reactive, co-speech gesticulation system for Knox that translates spoken audio prosody (RMS volume, beats) and LLM emotion into continuous, organic 50Hz robotic arm movements featuring wrist rolls and claw pinches.

**Architecture:** An offline `AudioAnalyzer` extracts 50Hz RMS intensity and syllable beat transients from synthesized speech audio. A multi-layer `Gesticulator` blends Layer 1 (organic micro-drift), Layer 2 (audio prosody & syllable pulses), and Layer 3 (expressive wrist roll flourishes & precision claw pinches) into safe, clamped 6-DOF joint trajectories. A `CoordinatedPlaybackEngine` plays audio asynchronously while streaming 50Hz pose packets over USB serial to the ESP32 in lockstep.

**Tech Stack:** Python 3.11+, NumPy, SoundDevice / miniaudio / wave, PyTest, ESP32 Serial protocol.

## Global Constraints
- Joint limit clamping strictly enforced on all frames: Waist [0, 180], Shoulder [15, 165], Elbow [15, 165], Wrist Pitch [0, 180], Wrist Roll [0, 180], Claw [10, 120].
- ESP32 motion control packet rate: 50Hz (20ms step interval).
- Zero external unmanaged binary dependencies; graceful fallback in dry-run mode or when audio devices are unavailable.
- Audio synthesis remains decoupled from blocking playback.

---

### Task 1: Audio Feature Analyzer (`AudioAnalyzer`)

**Files:**
- Create: `src/jarmvis/audio_analyzer.py`
- Test: `tests/test_audio_analyzer.py`

**Interfaces:**
- Consumes: Audio file path (`.wav`, `.mp3`) or raw `np.ndarray` float32 audio.
- Produces: `AudioFeatures` dataclass with `rms_envelope: np.ndarray`, `beat_onsets: np.ndarray`, `duration_sec: float`, `fps: int` (default 50).

- [ ] **Step 1: Write the failing test for `AudioAnalyzer`**

```python
import numpy as np
import pytest
from jarmvis.audio_analyzer import AudioAnalyzer, AudioFeatures

def test_audio_analyzer_synthetic_signal():
    # 1.0 second 440Hz tone with silence in middle
    sr = 16000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    signal = 0.8 * np.sin(2 * np.pi * 440 * t)
    signal[int(0.4 * sr):int(0.7 * sr)] = 0.0  # silence gap

    analyzer = AudioAnalyzer(fps=50)
    features = analyzer.extract_features_from_array(signal, sample_rate=sr)

    assert isinstance(features, AudioFeatures)
    assert features.fps == 50
    assert 48 <= len(features.rms_envelope) <= 52
    assert features.duration_sec == pytest.approx(1.0, abs=0.05)
    # Silence period should have significantly lower RMS than tone period
    tone_rms = np.mean(features.rms_envelope[5:15])
    silent_rms = np.mean(features.rms_envelope[25:30])
    assert tone_rms > silent_rms * 5.0
    assert len(features.beat_onsets) == len(features.rms_envelope)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_audio_analyzer.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'jarmvis.audio_analyzer'`

- [ ] **Step 3: Implement `AudioAnalyzer`**

Implement `src/jarmvis/audio_analyzer.py`:
- Support loading from `np.ndarray` and audio files via wave or soundfile/subprocess.
- Divide audio into `hop_size = sample_rate // fps` windows.
- Compute frame RMS: $\sqrt{\text{mean}(x^2)}$.
- Smooth with attack-decay exponential moving average.
- Onset beat detection via rectified derivative of energy: $\max(0, E_t - E_{t-1})$ with adaptive thresholding.

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/test_audio_analyzer.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/jarmvis/audio_analyzer.py tests/test_audio_analyzer.py
git commit -m "feat: add AudioAnalyzer for 50Hz speech prosody and onset extraction"
```

---

### Task 2: Multi-Layer Procedural Gesticulation Engine (`Gesticulator`)

**Files:**
- Create: `src/jarmvis/gesticulator.py`
- Test: `tests/test_gesticulator.py`

**Interfaces:**
- Consumes: `AudioFeatures` from Task 1, `emotion: str`, `base_pose: list[int]`.
- Produces: `generate_trajectory(...) -> list[list[int]]` (list of 6-DOF clamped angles at 50Hz).

- [ ] **Step 1: Write the failing test for `Gesticulator`**

```python
import numpy as np
import pytest
from jarmvis.audio_analyzer import AudioFeatures
from jarmvis.gesticulator import Gesticulator

def test_gesticulator_layer_safety_and_shapes():
    fps = 50
    num_frames = 100  # 2 seconds
    rms = np.linspace(0.1, 0.9, num_frames)
    beats = np.zeros(num_frames)
    beats[20] = 1.0
    beats[60] = 1.0
    features = AudioFeatures(
        rms_envelope=rms,
        beat_onsets=beats,
        duration_sec=2.0,
        fps=fps
    )

    gesticulator = Gesticulator(safe_limits=[
        (0, 180), (15, 165), (15, 165), (0, 180), (0, 180), (10, 120)
    ])
    trajectory = gesticulator.generate_trajectory(
        features=features,
        emotion="SARCASTIC",
        base_pose=[90, 90, 90, 90, 90, 30]
    )

    assert len(trajectory) == num_frames
    for frame in trajectory:
        assert len(frame) == 6
        assert 0 <= frame[0] <= 180
        assert 15 <= frame[1] <= 165
        assert 15 <= frame[2] <= 165
        assert 0 <= frame[3] <= 180
        assert 0 <= frame[4] <= 180
        assert 10 <= frame[5] <= 120  # Claw limits

    # Verify wrist roll and claw pinch activity during speech
    wrist_rolls = [f[4] for f in trajectory]
    claws = [f[5] for f in trajectory]
    assert max(wrist_rolls) != min(wrist_rolls)  # Dynamic wrist roll
    assert min(claws) < 30  # Claw pinches tighter on emphasis
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_gesticulator.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'jarmvis.gesticulator'`

- [ ] **Step 3: Implement `Gesticulator`**

Implement `src/jarmvis/gesticulator.py`:
- Layer 1 (`_compute_micro_drift`): Multi-frequency sine oscillators ($0.3\text{Hz}, 0.7\text{Hz}$) for lifelike sway.
- Layer 2 (`_compute_prosody_layer`): Map RMS and beat onsets to elbow/shoulder elevations and syllable nods.
- Layer 3 (`_compute_expressive_motifs`): Parametric wrist roll rotation (supination/pronation flourishes) and claw pinching depending on emotion (`CONFIDENT`, `SARCASTIC`, `HAPPY`, `EXCITED`, `ANGRY`, `NEUTRAL`).
- Clamp every frame through safe limits.

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/test_gesticulator.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/jarmvis/gesticulator.py tests/test_gesticulator.py
git commit -m "feat: add multi-layer procedural Gesticulator with wrist roll and claw pinches"
```

---

### Task 3: Decoupled TTS Synthesis & Coordinated Playback Engine

**Files:**
- Modify: `src/jarmvis/tts_engine.py`
- Create: `src/jarmvis/playback_engine.py`
- Test: `tests/test_playback_engine.py`

**Interfaces:**
- Consumes: Audio file path, `trajectory: list[list[int]]`, `SerialBridge`.
- Produces: Non-blocking audio playback while streaming 50Hz serial pose packets.

- [ ] **Step 1: Write the failing test for `CoordinatedPlaybackEngine`**

```python
import time
import pytest
from unittest.mock import MagicMock
from jarmvis.playback_engine import CoordinatedPlaybackEngine
from jarmvis.serial_bridge import SerialBridge

def test_playback_engine_streams_trajectory():
    bridge = MagicMock(spec=SerialBridge)
    engine = CoordinatedPlaybackEngine(bridge=bridge, fps=50)

    # 10 frames = 0.2s trajectory
    trajectory = [[90, 90, 90, 90, 90, 30] for _ in range(10)]
    start = time.time()
    # Mock audio playback that finishes in 0.2s
    engine.play_with_gestures(audio_path=None, trajectory=trajectory, blocking=True)
    elapsed = time.time() - start

    assert bridge.send_pose.call_count == 10
    assert elapsed >= 0.15  # Verified proper pacing
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_playback_engine.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'jarmvis.playback_engine'`

- [ ] **Step 3: Implement `CoordinatedPlaybackEngine` and update `TTSEngine`**

1. In `src/jarmvis/tts_engine.py`:
   - Add `synthesize_to_file(self, text: str, emotion: str | None = None) -> str` which synthesizes via ElevenLabs or Edge-TTS and returns the temporary file path without blocking playback.
2. In `src/jarmvis/playback_engine.py`:
   - Implement `CoordinatedPlaybackEngine` with `play_with_gestures(audio_path, trajectory, blocking=True)`.
   - Uses non-blocking audio play (or threaded `afplay`/`sounddevice`) while precision 50Hz loop dispatches serial `send_pose`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=src pytest tests/test_playback_engine.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/jarmvis/tts_engine.py src/jarmvis/playback_engine.py tests/test_playback_engine.py
git commit -m "feat: add CoordinatedPlaybackEngine and decouple TTS synthesis from playback"
```

---

### Task 4: End-to-End App Integration & Simulation Verification

**Files:**
- Modify: `src/jarmvis/app.py`
- Test: `tests/test_speech_gestures_flow.py`

**Interfaces:**
- Connects `AudioAnalyzer`, `Gesticulator`, `CoordinatedPlaybackEngine`, and `JarmvisApp.handle_voice_prompt`.

- [ ] **Step 1: Write the failing end-to-end integration test**

```python
import pytest
from unittest.mock import MagicMock
from jarmvis.app import JarmvisApp
from jarmvis.serial_bridge import SerialBridge

def test_full_speech_gestures_flow_in_app(monkeypatch):
    bridge = SerialBridge(dry_run=True)
    poses_sent = []
    monkeypatch.setattr(bridge, "send_pose", lambda angles, speed=50, easing="cosine", face=None: poses_sent.append(angles))

    app = JarmvisApp(bridge=bridge, use_mock_ai=True)
    app.handle_voice_prompt("Tell me something cool, genius")

    # Knox speaks and generates gesticulations
    assert len(poses_sent) > 0
    # Every pose clamped and 6 joints
    for p in poses_sent:
        assert len(p) == 6
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_speech_gestures_flow.py -v`  
Expected: FAIL

- [ ] **Step 3: Update `src/jarmvis/app.py`**

- Initialize `AudioAnalyzer`, `Gesticulator`, and `CoordinatedPlaybackEngine` in `JarmvisApp.__init__`.
- In `handle_voice_prompt`, synthesize speech to audio file, extract features, generate 50Hz trajectory, and trigger `play_with_gestures`.
- If a macro was requested (e.g. `PICK_BLOCK`, `CELEBRATE`), execute it immediately following speech.

- [ ] **Step 4: Run the full test suite**

Run: `PYTHONPATH=src pytest -v`  
Expected: ALL tests PASS (existing 46 + all new tests).

- [ ] **Step 5: Commit**

```bash
git add src/jarmvis/app.py tests/test_speech_gestures_flow.py
git commit -m "feat: integrate reactive speech gesticulation engine into JarmvisApp"
```

