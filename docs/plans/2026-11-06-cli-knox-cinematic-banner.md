# Implementation Plan: KNOX CLI Cinematic Iron Man Helmet HUD & Typography

> **Status:** Awaiting User Review & Approval  
> **Aesthetic Philosophy:** Swiss Minimalism & Industrial Avionics. Pure monospace typography, hairline geometric box-drawing borders (`rich.box.ROUNDED`), zero emojis, zero pseudo-hacker slashes (`///`) or fake security protocols. Realistic robotics and avionics telemetry.

---

## 1. Objective

Deliver a high-impact, realistic terminal startup experience for `jarmvis` inspired by:
1. **Claude CLI's Wordmark**: An authoritative, beautifully proportioned large monospace `KNOX` display font in Doom Gold (`#D6AD35`) and Mask Steel (`#85898A`).
2. **Iron Man Mark Helmet HUD Boot Sequence**: A realistic multi-phase HUD calibration sequence (reticle acquisition, artificial horizon gyro ladder, dual-visor diagnostics, faceplate seal lock).
3. **Latverian Metallurgy Telemetry**: Understated Doctor Doom chassis and power containment specifications in Shadow Green (`#24452D`) and Doom Green (`#477A43`).

The animation will run transiently in-place via `rich.live.Live(transient=True)` so that zero scrollback clutter is created, resolving smoothly into the interactive terminal prompt.

---

## 2. Color System & Design Tokens

Strictly constrained to the four authentic Doctor Doom / Mark-LXXXV specification tokens:

| Token | Hex | Role | Applied Elements |
|---|---|---|---|
| **Doom Gold** | `#D6AD35` | Primary Accent / Lock | Giant `KNOX` wordmark, target lock reticle, active prompt indicator |
| **Doom Green** | `#477A43` | Operational Status | Pitch ladder horizon, online status chips, waveform peaks |
| **Shadow Green** | `#24452D` | Structure & Wireframe | Hairline box frames, inactive pitch ticks, diagnostic borders |
| **Mask Steel** | `#85898A` | Telemetry & Metadata | Avionics readouts, degree ticks, voltage/frequency metrics |

---

## 3. Visual Components Specification

### A. Claude CLI-Inspired Large Monospace `KNOX` Wordmark
Authoritative, clean block letterforms designed for standard 80+ column terminal viewports:

```text
██╗  ██╗███╗   ██╗ ██████╗ ██╗  ██╗
██║ ██╔╝████╗  ██║██╔═══██╗╚██╗██╔╝
█████╔╝ ██╔██╗ ██║██║   ██║ ╚███╔╝ 
██╔═██╗ ██║╚██╗██║██║   ██║ ██╔██╗ 
██║  ██╗██║ ╚████║╚██████╔╝██╔╝ ██╗
╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝
```

Sub-bar typography:
```text
KNOX WORKSHOP SYSTEM  |  MARK-LXXXV ARCHITECTURE  |  LATVERIA SPEC-8
```

---

### B. Realistic Iron Man Helmet HUD Boot Sequence (~700ms Total)

The sequence executes in 4 coherent avionics phases rendered in-place using `rich.live.Live(refresh_per_second=20, transient=True)`. Each phase displays authentic kinematics and optical metrics:

#### Phase 1: Reticle Acquisition & Ocular Collimation (180ms)
Twin ocular targeting brackets expand from center horizon to focal width:
```text
      ┌──       ──┐                   ┌──       ──┐
      │     ┼     │   [ COLLIMATING ] │     ┼     │
      └──       ──┘                   └──       ──┘
   AZIMUTH: 000.0°  ELEVATION: +00.0°  OPTICS: f/1.4 35mm
```
- **Frame 1 (60ms):** Focal point acquisition `[  ·  ]` at center.
- **Frame 2 (60ms):** Dual reticle expansion `[ ─┼─ ]` with azimuth scan.
- **Frame 3 (60ms):** Optical brackets lock into bilateral eye position.

#### Phase 2: Artificial Horizon & Gyro Pitch Ladder (180ms)
An authentic flight/combat HUD pitch ladder leveling across the horizontal plane:
```text
            ───┬─── [ -05.0° ] ───┬───
               │                  │   
         ━━━━━━╸   [  00.0° ]   ╺━━━━━━  PITCH: +0.02°
               │                  │      ROLL:  -0.01°
            ───┴─── [ +05.0° ] ───┴───
   INERTIAL PLATFORM: LOCKED  |  6-DOF IMU: CALIBRATED
```
- Horizon line levels out from a slight pitch tilt (`-02.4°` -> `00.0°`).
- Roll ladder ticks align with lateral bracket guides.

#### Phase 3: Dual Visor Mark Diagnostics & Latverian Telemetry (200ms)
Split dual-panel avionics diagnostics detailing hardware PWM and chassis integrity:
```text
┌─ LEFT VISOR: ACTUATION ───────┐ ┌─ RIGHT VISOR: POWER ──────────┐
│ LEDC HW PWM: 50 Hz (6-CH)     │ │ CAPACITOR BANK: 99.4% CHARGE  │
│ BUS VOLTAGE: 6.02 V NOMINAL   │ │ ARC SHUNT: 3.2 GW PEAK        │
│ TORQUE LIMIT: 12.8 kg·cm MAX  │ │ CHASSIS: TITANIUM-GOLD ALLOY  │
│ SERVO RESPONSE: < 12 ms       │ │ THERMAL CORE: 34.2° C NOMINAL │
└───────────────────────────────┘ └───────────────────────────────┘
```
- No fictional gibberish: actual hardware numbers matching our PCA9685/ESP32 LEDC PWM and MG996R servo specs.

#### Phase 4: Faceplate Pressure Seal & System Lock (160ms)
The mechanical faceplate locks into position with high-contrast target lock reticle:
```text
   ┌───────────────────────────────────────────────────────────────┐
   │  FACEPLATE SEAL: ENGAGED      SYSTEM INTEGRITY: 100% NOMINAL  │
   │  TARGET TRACKING: ACTIVE      JARVIS NEURAL CORE: ONLINE      │
   └───────────────────────────────────────────────────────────────┘
```
- Resolves cleanly into the main persistent TUI workspace.

---

## 4. Execution Architecture

### File Modifications
1. **`src/jarmvis/tui.py`**:
   - `BANNER_KNOX`: Large monospace block string in `#D6AD35`.
   - `HUDSequence`: Dedicated helper class with 4 discrete frame generators.
   - `TerminalUI.play_hud_boot(fast: bool = False)`: Transient in-place live renderer.
   - `TerminalUI.render_persistent_header()`: Compact persistent status chip rendered once boot completes.
2. **`src/jarmvis/app.py`**:
   - Add CLI argument `--no-anim` to skip the boot animation for instant development cycles.
   - Call `tui.play_hud_boot()` immediately prior to audio listening or command loop.

### Command Flags
- `python jarmvis --cli --dry-run`: Runs full cinematic boot sequence + CLI prompt.
- `python jarmvis --cli --dry-run --no-anim`: Bypasses boot animation instantly into prompt.

---

## 5. Verification Plan

### Visual & Interactive Verification
1. Run `python -c "from jarmvis.tui import TerminalUI; TerminalUI().play_hud_boot()"` in Windows PowerShell to verify:
   - In-place rendering without vertical line scrolling.
   - Exact hex colors (`#477A43`, `#24452D`, `#D6AD35`, `#85898A`).
   - Timing (~700ms total, crisp frame transitions).
2. Run `python jarmvis --cli --dry-run --no-anim` to confirm instant-bypass flag operates as expected.
3. Run existing test suite (`pytest tests/ -v`) to ensure zero regression across core kinematics and serial bridges.
