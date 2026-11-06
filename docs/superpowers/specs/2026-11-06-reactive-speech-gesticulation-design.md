# Reactive Speech-Driven Gesticulation Engine (Knox / Jarmvis)

**Date:** 2026-11-06  
**Status:** Approved  
**Author:** Pair programming with Antigravity  

---

## 1. Overview & Problem Statement

In conversational robotics, human hand gestures during speech are critical for conveying warmth, life, and emotional authenticity. Previously in Jarmvis:
- When Knox spoke, `self.tts.speak()` blocked synchronously while the 6-DOF robotic arm remained entirely static and frozen.
- Physical movements were limited to pre-recorded, hardcoded waypoint macros (`macros.json`) or 4 static reflexes (`PERK_UP`, `THINK`, `DROOP`, `STARTLE`).
- Fixed macros cannot scale to fluid conversations, look mechanical and repetitive, and desynchronize from dynamic speech rhythms.

This specification defines the **Additive Layered Procedural Motion Engine (ALME)** and **Reactive Gesticulator**. It brings Knox to life by synchronizing continuous, lifelike arm movements—particularly expressive **wrist roll (Joint 4)** rotations and **claw pinches (Joint 5)**—directly with spoken audio prosody and LLM emotional states in real-time.

---

## 2. High-Level Architecture

```
                 ┌────────────────────────────────┐
                 │  Knox Brain (LLM / Fallback)   │
                 └───────────────┬────────────────┘
                                 │ Text + Emotion ("CONFIDENT", etc.)
                                 ▼
                 ┌────────────────────────────────┐
                 │       TTSEngine Synthesizer    │
                 │   (ElevenLabs / Edge-TTS)      │
                 └───────────────┬────────────────┘
                                 │ Synthesized Audio (.wav/.mp3)
                                 ▼
                 ┌────────────────────────────────┐
                 │         AudioAnalyzer          │
                 │  - 50Hz RMS Energy Envelope    │
                 │  - Syllable / Beat Onsets      │
                 └───────────────┬────────────────┘
                                 │ Acoustic Features (50Hz timeline)
                                 ▼
                 ┌────────────────────────────────┐
                 │          Gesticulator          │
                 │  Layer 1: Organic Micro-Drift  │
                 │  Layer 2: Audio Prosody Beats  │
                 │  Layer 3: Expressive Flourishes│
                 │           (Wrist Roll + Pinch) │
                 │  -> Blended & Clamped Poses    │
                 └───────────────┬────────────────┘
                                 │ Trajectory: list[list[int]] (50Hz)
                                 ▼
                 ┌────────────────────────────────┐
                 │    Coordinated Playback Loop   │
                 │   Audio Playback (SoundDevice) │
                 │  + 50Hz Serial Streaming       │
                 └───────────────┬────────────────┘
                                 │ Compact JSON Packets (50Hz)
                                 ▼
                 ┌────────────────────────────────┐
                 │   ESP32 Firmware & Servos      │
                 │   6 PWM Channels @ 50Hz        │
                 └────────────────────────────────┘
```

---

## 3. Component Specifications

### 3.1. `AudioAnalyzer` (`src/jarmvis/audio_analyzer.py`)
Responsible for sub-millisecond offline feature extraction from the synthesized speech audio:
- **Audio Decoding**: Reads `.wav` or `.mp3` into mono float32 samples at 16kHz via `numpy` and lightweight decoding (e.g. `soundfile` / `miniaudio` or system tools).
- **Frame Rate**: Computes feature slices at **50Hz (20ms per frame)** matching the ESP32 control loop.
- **RMS Energy Envelope ($E_t$)**:
  $$E_t = \sqrt{\frac{1}{N} \sum_{i=0}^{N-1} x[i]^2}$$
  Smoothed using an attack-decay filter (attack: 0.8, decay: 0.3) and normalized between 0.0 and 1.0.
- **Onset / Beat Detection ($B_t$)**: Detects spectral/energy transients where $\frac{dE}{dt} > \text{threshold}$, returning a binary or float intensity beat signal indicating syllable emphasis.

### 3.2. `Gesticulator` (`src/jarmvis/gesticulator.py`)
Generates 50Hz target joint angle trajectories by additively combining 3 independent procedural layers:

$$\text{Pose}(t) = \text{Base} + L_1(t) + L_2(t) + L_3(t)$$

#### Layer 1: Biological Micro-Drift ($L_1$)
Continuous organic drift using multi-frequency harmonic oscillators to ensure the arm never freezes during pauses:
- Shoulder: $A_1 \sin(2\pi f_1 t) + A_2 \sin(2\pi f_2 t + \phi_1)$ with $f_1 \approx 0.3\text{Hz}, f_2 \approx 0.7\text{Hz}, A \approx 1.5^\circ$.
- Elbow: $B_1 \sin(2\pi f_1 t + 0.4) \cdot 1.8^\circ$.
- Wrist Roll: Subtle organic drift $\pm 2.0^\circ$.

#### Layer 2: Audio Prosody & Beats ($L_2$)
Directly maps speech energy ($E_t$) and syllable beats ($B_t$) to physical joints:
- **Elbow / Shoulder Bounce**: Emphatic words elevate the elbow by $+ (E_t \times 6^\circ + B_t \times 4^\circ)$.
- **Wrist Pitch Cadence**: Nods with syllable stress by $- (B_t \times 5^\circ)$.
- **Claw Micro-Flex**: Modulates gripper openness proportional to loudness: $\text{claw} = \text{rest} + E_t \times 12^\circ$.

#### Layer 3: Expressive End-Effector Motifs & Emotion Modulation ($L_3$)
Generates conversational flourishes parameterized by the LLM emotion (`CONFIDENT`, `SARCASTIC`, `EXCITED`, `HAPPY`, `ANGRY`, `NEUTRAL`):
1. **Tony Stark "Palm Flourish" (Supination/Pronation)**:
   - When explaining or boasting, Wrist Roll rotates smoothly from $90^\circ \rightarrow 135^\circ \rightarrow 75^\circ \rightarrow 90^\circ$ over a smooth Gaussian/Cosine bell curve ($t \approx 1.2\text{s}$).
2. **The "Precision Pinch" (Claw Joint 5)**:
   - Clamps the gripper down towards $15^\circ$ (tight two-finger pinch) on key argumentative emphasis, paired with a downward wrist pitch flick.
3. **Sarcastic Shrug**:
   - Asymmetric wrist roll tilt ($45^\circ$) with an inquisitive wrist pitch lift.
4. **Expansive Flourish**:
   - Claw opens wide ($80^\circ–95^\circ$) with elevated shoulder and elbow.

#### Safety Clamping & Damping
All angles are strictly constrained within hardware limits:
- Joint 0 (Waist): $[0^\circ, 180^\circ]$
- Joint 1 (Shoulder): $[15^\circ, 165^\circ]$
- Joint 2 (Elbow): $[15^\circ, 165^\circ]$
- Joint 3 (Wrist Pitch): $[0^\circ, 180^\circ]$
- Joint 4 (Wrist Roll): $[0^\circ, 180^\circ]$
- Joint 5 (Claw): $[10^\circ, 120^\circ]$

### 3.3. `CoordinatedPlaybackEngine`
Manages synchronous lockstep execution between audio and serial motor streaming:
- Decouples playback from blocking system calls using non-blocking audio streaming (`sounddevice` / PyAudio / threaded playback).
- A 50Hz precision timer thread reads the trajectory buffer frame-by-frame and dispatches `send_pose(angles, speed=65, easing="linear")` to `SerialBridge`.
- If an interruption or error occurs, the playback and gesticulation loop terminate cleanly, gently returning the arm to resting pose.

### 3.4. Updates to `TTSEngine` and `JarmvisApp`
- `TTSEngine.synthesize_to_file(text, emotion)`: Exposed method that produces the cached audio file and returns its path and duration without immediately triggering blocking playback.
- `JarmvisApp.handle_voice_prompt()`: Replaces the blocking `self.tts.speak()` call with the non-blocking coordinated playback and gesticulator streaming pipeline.

---

## 4. Hardware & Serial Communication Budget

- **Baud Rate**: 115200 baud ($\approx 11,520 \text{ bytes/sec}$).
- **Packet Format**: `{"cmd":"pose","angles":[w,s,e,wp,wr,g],"speed":60}\n` ($\approx 55 \text{ bytes}$).
- **Bandwidth Consumption at 50Hz**:
  $$50 \times 55 = 2,750 \text{ bytes/sec} \approx 23.8\% \text{ of available serial bandwidth}$$
  Leaves ample headroom for face OLED display packets and reflex triggers.

---

## 5. Verification & Testing Strategy

1. **Unit Tests (`tests/test_audio_analyzer.py`)**:
   - Verify synthetic sine wave and silent audio decoding.
   - Assert normalized RMS output $[0.0, 1.0]$.
   - Assert beat detection triggers on volume step transients.
2. **Unit Tests (`tests/test_gesticulator.py`)**:
   - Verify $L_1 + L_2 + L_3$ mathematical blending.
   - Assert all 6 joints strictly stay within `[ANGLE_MIN, ANGLE_MAX]` across thousands of randomized frame inputs.
   - Assert claw pinch activation triggers on emphasis and wrist roll rotates naturally during flourishes.
3. **End-to-End Simulation Test (`tests/test_speech_gestures_flow.py`)**:
   - Run end-to-end cycle in dry-run mode with mock audio.
   - Verify that serial bridge receives sequential 50Hz pose packets matching the audio duration.
   - Verify post-speech macro execution succeeds after gesture playback completes.

