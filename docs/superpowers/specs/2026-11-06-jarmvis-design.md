# Jarmvis: 5-DOF Robotic Arm with JARVIS Intelligence & Dum-E Persona
## Software-First Architectural Design Specification

**Date:** 2026-11-06  
**Target Hardware:** Apple Silicon Mac M4 Air (Brain) + ESP32 (Motion Controller)  
**Actuation:** 6 Servos (3x MG996R, 3x SG90) + SSD1306 128x64 OLED Face  
**Methodology:** Software-First Development (Virtual Simulator before Physical Hardware)

---

## 1. Executive Summary & Goals

**Jarmvis** merges the articulate, British wit of Marvel's **JARVIS** with the clumsy, eager, puppy-like physical comedy of Tony Stark's workshop arm, **Dum-E**.

Because physical 3D printing and electronic component delivery occur later in the project schedule, this specification adopts a strict **Software-First Strategy**:
1. All AI conversational pipelines (VAD, STT, LLM, TTS), emotion state machines, macro executors, and calibration tools are built and verified on the **MacBook Air M4** first.
2. A **Virtual Arm & Face Emulator** mimics the ESP32 over a local virtual serial port (PTY / loopback), rendering real-time joint positions and animated OLED eye states on-screen.
3. The **ESP32 firmware** is written as a direct drop-in drop-and-flash replacement conforming to the exact same JSON serial protocol.
4. Physical assembly, wiring, and desk calibration happen seamlessly once parts arrive.

---

## 2. System Architecture

```
                                 ┌────────────────────────────────────────────────────────┐
                                 │                 MACBOOK AIR M4 (BRAIN)                 │
                                 │                                                        │
    User Audio (Laptop Mic) ────►│  • Silero VAD (Sub-30ms instant speech trigger)        │
                                 │  • MLX-Whisper (Metal-accelerated local STT, <100ms)   │
                                 │  • Brain: Qwen2.5-7B (Ollama / MLX) or Gemini 2.0      │
                                 │  • TTS: Kokoro-82M (Local Neural) / Edge-TTS (JARVIS)  │
                                 │  • Motion & Emotion Choreography Engine                │
                                 │  • Macro Trajectory Sequencer (macros.json)            │
                                 └───────────────────────────┬────────────────────────────┘
                                                             │
                                                             ▼ (Serial JSON Protocol @ 115200)
                                            ┌────────────────┴────────────────┐
                                            │                                 │
                                    (During Development)              (When Parts Arrive)
                                            │                                 │
                                            ▼                                 ▼
                         ┌──────────────────────────────────────┐  ┌─────────────────────────────────────┐
                         │      VIRTUAL HARDWARE EMULATOR       │  │           ESP32 CONTROLLER          │
                         │  • Terminal / 2D ASCII Arm Renderer  │  │  • 6x LEDC Hardware PWM Channels    │
                         │  • Pygame / Matplotlib Joint Angles  │  │  • S-Curve + Spring Easing Engine   │
                         │  • Virtual 128x64 OLED Face Window   │  │  • FreeRTOS Dual Core (OLED + PWM)  │
                         └──────────────────────────────────────┘  │  • SSD1306 128x64 I2C OLED Display │
                                                                   └──────────────────┬──────────────────┘
                                                                                      │
                                                                                      ▼
                                                                   ┌─────────────────────────────────────┐
                                                                   │           PHYSICAL ARM (6 DOF)      │
                                                                   │  • 3x MG996R (Base, Shoulder, Elbow)│
                                                                   │  • 3x SG90 (Wrist P, Wrist R, Claw) │
                                                                   │  • External 5V 5A Power Supply      │
                                                                   └─────────────────────────────────────┘
```

---

## 3. Communication Protocol (The Hardware/Software Contract)

The laptop and microcontroller communicate over USB Serial (115200 baud, 8N1) via newline-delimited JSON strings (`\n`).

### 3.1 Commands (Laptop $\rightarrow$ Controller / Emulator)

#### A. Pose Command (Move Joints)
```json
{
  "cmd": "pose",
  "angles": [90, 65, 110, 45, 90, 30],
  "speed": 50,
  "easing": "spring",
  "face": "curious"
}
```
* `angles`: Array of 6 integers $[0, 180]$ mapping to:
  * `[0]` Waist Base (MG996R)
  * `[1]` Shoulder (MG996R)
  * `[2]` Elbow (MG996R)
  * `[3]` Wrist Pitch (SG90)
  * `[4]` Wrist Roll (SG90)
  * `[5]` Gripper Claw (SG90, $0 = \text{closed}, 100 = \text{wide open}$)
* `speed`: $1–100$ (percentage of max rotational speed).
* `easing`: `"linear"`, `"cosine"`, or `"spring"` (overshoot bounce).
* `face`: Eye expression state (optional override).

#### B. Reflex Command (Instant Low-Latency Reaction)
```json
{
  "cmd": "reflex",
  "type": "PERK_UP"
}
```
* Types: `"PERK_UP"`, `"STARTLE"`, `"THINK"`, `"DROOP"`, `"WOBBLE"`.
* Priority interrupt: Preempts current slow movements to immediately respond to voice onset.

#### C. Face Command (Direct OLED Update)
```json
{
  "cmd": "face",
  "state": "ALERT",
  "pupil_x": 10,
  "pupil_y": -5
}
```
* States: `"NEUTRAL"`, `"ALERT"`, `"CURIOUS"`, `"SAD"`, `"HAPPY"`, `"SQUINT"`, `"LOOK_AROUND"`.

---

## 4. Mac M4 AI & Audio Pipeline

### 4.1 Instant Reflex Loop (Sub-30ms)
* **VAD:** `silero-vad` continuously processes 512-sample (32ms) audio chunks from the laptop microphone.
* **On Speech Start:** Fires `{"cmd":"reflex","type":"PERK_UP"}` over Serial immediately. The arm begins snapping erect before the user even finishes speaking.

### 4.2 Speech Recognition (STT)
* **Engine:** `mlx-whisper` using `whisper-base.en` or `whisper-small.en`.
* **Execution:** Metal GPU-accelerated on Apple Silicon M4.
* **Latency:** ~60ms to 90ms for typical 2-4 second phrases.

### 4.3 LLM Reasoning & Personality Engine
* **Model:** `qwen2.5:7b-instruct` (via Ollama or MLX-LM) with fallback to Google Gemini 2.0 Flash.
* **Personality Prompt:** Witty, cultured British butler (JARVIS) controlling an excitable, clumsy physical body (Dum-E).
* **Structured Output Schema:**
```json
{
  "speech": "Right away, sir. Commencing block retrieval sequence.",
  "emotion": "FOCUSED",
  "face": "DETERMINED",
  "macro": "PICK_BLOCK_LEFT"
}
```

### 4.4 Conversational Neural TTS
* **Primary (Local):** `Kokoro-82M` (82M parameter neural TTS).
  * Extremely natural human prosody, breath sounds, and zero metallic artifacts.
  * Voice: British English (`bm_george` or `bm_fable`).
* **Alternative (Cloud):** `edge-tts` (`en-GB-RyanNeural`).
* **Speech-Motion Synchronization:** While audio streams out the laptop speakers, an audio envelope tracker modulates minor wrist and neck bobbing at syllable boundaries.

---

## 5. Dum-E Emotion & Macro Motion Engine

### 5.1 Procedural Motion Mechanics
1. **Cosine & S-Curve Smoothing:** Servos do not teleport to target angles; position is interpolated at 50Hz using:
   $$\theta(t) = \theta_{\text{start}} + (\theta_{\text{target}} - \theta_{\text{start}}) \cdot \frac{1 - \cos(\pi \cdot t)}{2}$$
2. **Spring Overshoot Easing:** When perking up or reacting, the movement overshoots the target by $3^\circ–5^\circ$ and oscillates once before settling, creating a believable illusion of mechanical mass.
3. **Idle Ambient Life:** If no commands arrive for >3 seconds, the arm enters subtle sine-wave "breathing" and occasional curious glances.

### 5.2 Pre-Calibrated Hardcoded Macros (`macros.json`)
Without computer vision, physical tasks are executed via coordinated multi-point waypoints:

* `PICK_BLOCK_LEFT`:
  1. Approach hover: `[45, 60, 80, 45, 90, 100]` (Claw open)
  2. Descend: `[45, 35, 65, 30, 90, 100]`
  3. Clamp: `[45, 35, 65, 30, 90, 20]` (Claw tight)
  4. Lift vertical: `[45, 75, 90, 60, 90, 20]`
  5. Present to user: `[90, 70, 80, 50, 90, 20]` + Happy eyes
* `DUNCE_CORNER`: Head hangs down to the desk, turns away, sad drooping eyes.
* `HIGH_FIVE`: Arm reaches out at $45^\circ$, waits 1.5 seconds, gives a friendly claw tap, and celebrates.
* `CELEBRATE`: Double claw-snap, bouncy neck oscillation, upward crescent eyes.

### 5.3 Interactive Calibration CLI (`tools/calibrate.py`)
A keyboard-driven tool:
* `Q / W`: Joint 1 (Base) $\pm 5^\circ$
* `E / R`: Joint 2 (Shoulder) $\pm 5^\circ$
* `T / Y`: Joint 3 (Elbow) $\pm 5^\circ$
* `U / I`: Joint 4 (Wrist Pitch) $\pm 5^\circ$
* `O / P`: Joint 5 (Wrist Roll) $\pm 5^\circ$
* `[ / ]`: Joint 6 (Claw) Open / Close
* `SPACE`: Preview motion smoothly
* `S`: Record current angles as a named waypoint into `macros.json`.

---

## 6. Virtual Arm & Face Emulator (`tools/emulator.py`)

To develop 100% of the software without hardware:
1. Creates a virtual pseudo-terminal (PTY) or local socket simulating `/dev/tty.usbserial-ESP32`.
2. **ASCII / Graphical Arm Viewer:** Displays real-time joint angles, 2D kinematic schematic, and current movement trajectory.
3. **Virtual OLED Window:** A 128x64 pixel window simulating the SSD1306 OLED display, showing the procedural animated eyes and expressions.
4. Allows end-to-end testing of voice conversation, instant reflex perking, thinking states, and macro playback.

---

## 7. ESP32 Firmware Specification (For Hardware Deployment)

* **Platform:** PlatformIO / Arduino C++ on ESP32 (ESP-WROOM-32).
* **Motor Control:** Native ESP32 LEDC PWM peripheral (6 channels @ 50Hz, 16-bit resolution).
* **FreeRTOS Dual-Core Architecture:**
  * **Core 0:** OLED Display rendering loop (`U8g2` library, ~30 FPS eye animations).
  * **Core 1:** 50Hz LEDC servo interpolation and Serial JSON parsing (`ArduinoJson` v7).
* **Safety Limits:** Hardcoded minimum and maximum angles for each joint to prevent physical collisions or link binding.

---

## 8. Software-First Phased Roadmap

| Phase | Focus | Deliverables |
| :--- | :--- | :--- |
| **Phase 1: Environment & Virtual Emulator** | Mac Setup & Mocking | • Python virtual env with MLX, sounddevice, pyserial.<br>• Virtual ESP32 Emulator (`emulator.py`) with arm visualizer and virtual OLED face. |
| **Phase 2: Voice & AI Pipeline** | Speech & Personality | • Silero VAD reflex trigger loop.<br>• MLX-Whisper STT + Kokoro-82M / Edge-TTS audio playback.<br>• Qwen 2.5 / Gemini LLM prompt with structured emotion & macro output. |
| **Phase 3: Motion Engine & Calibration CLI** | Behavior & Macros | • Easing & Spring momentum interpolator.<br>• Interactive calibration keyboard tool (`calibrate.py`).<br>• Initial `macros.json` library (`PICK_BLOCK`, `DUNCE`, `HIGH_FIVE`). |
| **Phase 4: ESP32 Firmware** | Embedded Core | • PlatformIO C++ firmware with LEDC PWM and `U8g2` eyes.<br>• Verified against test serial scripts. |
| **Phase 5: Physical Integration** | Real Hardware | • Wire servos, external 5V power, capacitor, OLED.<br>• Flash ESP32, calibrate desk waypoints, live interactive test. |

---

## 9. Verification & Success Criteria

1. **Reflex Latency:** The virtual arm (and later real arm) begins perking up in under $50$ms after the user begins speaking.
2. **Audio Quality & Flow:** Kokoro/Edge-TTS delivers rich conversational speech with natural pauses; talking motions sync with audio.
3. **Dum-E Comedy:** Reprimands instantly cause dejected head droops; compliments and completed tasks trigger excited celebrations.
4. **Macro Accuracy:** Saved waypoints in `macros.json` execute smoothly and predictably without jerky discontinuities.
5. **Drop-in Hardware Readiness:** When the physical ESP32 is plugged in, switching from the virtual port to `/dev/cu.usbserial` requires zero laptop code changes.
