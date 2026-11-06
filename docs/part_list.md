# Jarmvis - Hardware & Parts List

This document lists all hardware, electrical, mechanical, and structural components required to build **Jarmvis** (a 5-DOF + 1-DOF Gripper robotic arm with Tony Stark's Dum-E personality and JARVIS voice intelligence).

---

## 1. Actuators & Motors (6 Servos Total)

| Component | Quantity | Location / Joint | Role & Specifications |
| :--- | :---: | :--- | :--- |
| **MG996R Metal-Gear Servo** | 3 | • Base (Rotating Waist)<br>• Shoulder (Arm 1)<br>• Elbow (Arm 2) | High-torque (10–12 kg·cm), metal gears. Handles the heavy cantilever weight of the arm. Working voltage: 4.8V–6V. |
| **SG90 (or MG90S) Micro Servo** | 3 | • Wrist Pitch (Arm 3)<br>• Wrist Roll (Gripper Base)<br>• Claw (Grip mechanism) | Lightweight micro servo (1.8–2.2 kg·cm). Fast movement for expressive wrist flicks, tilts, and claw gestures. |
| **Included Servo Horns & Screws** | 6 sets | All motors | **Crucial:** Keep all plastic horns and tiny screws included in the servo packaging. The 3D-printed gears and links attach directly to them. |

---

## 2. Microcontroller & Display Face

| Component | Quantity | Purpose | Notes |
| :--- | :---: | :--- | :--- |
| **ESP32 Dev Board** | 1 | Real-time motion controller & OLED driver | ESP-WROOM-32 (30-pin or 38-pin NodeMCU form-factor). Has hardware PWM (LEDC) on all pins. |
| **USB Data Cable** | 1 | Serial bridge to laptop + ESP32 logic power | Must be a **data-capable** cable (not a charge-only cable). Micro-USB or USB-C depending on your ESP32 board. |
| **0.96" or 1.3" I2C OLED Display** | 1 | Dum-E's "Face" / Animated Eyes | SSD1306 driver, 128x64 resolution, 4 pins (`VCC`, `GND`, `SDA`, `SCL`). Mounted onto the wrist/gripper head. |

---

## 3. Power Supply & Electrical Components

> [!WARNING]
> **Never power the servos from the ESP32 5V pin or laptop USB.** 
> The 3x MG996R servos can draw up to 4A–6A peak stall current under load, which will brownout/reboot the ESP32 or trip laptop USB safety limits.

| Component | Quantity | Specifications & Purpose |
| :--- | :---: | :--- |
| **5V DC External Power Supply** | 1 | **5V 5A (or 5V 6A / 10A)** regulated power adapter. Dedicated solely to powering the 6 servos. |
| **DC Barrel Jack to Screw Terminal** | 1 | Female 5.5mm × 2.1mm to screw terminal. Allows clean wire hookup without cutting your power adapter cable. |
| **Electrolytic Capacitor** | 1 | **1000 µF to 2200 µF (16V or 25V)**. Connected across the servo `+5V` and `GND` rails right at the power distribution point. Absorbs current spikes when all motors move. |
| **Power Distribution** | 1 | Mini breadboard (170-point), screw terminal distribution block, or perfboard to split the 5V power into 6 servo pairs. |
| **Jumper Wires (M-to-F)** | 10–15 | Male-to-Female jumpers to connect servo signal lines to ESP32 GPIOs. |
| **Jumper Wires (F-to-F)** | 4 | Female-to-Female jumpers for the OLED display (`VCC`, `GND`, `GPIO 21 [SDA]`, `GPIO 22 [SCL]`). |
| **Solid Core Hookup Wire (22 AWG)** | 1 pack | Red & Black wire for tidy power rail distribution. |

---

## 4. Mechanical Fasteners & Structural Parts

### A. 3D Printed Parts (`armschema/printable_parts/`)
* `Circular_Base.stl` (Base foundation)
* `Rotating_Waste.stl` (Waist rotation plate)
* `Arm_1.stl` & `Gear_Arm_1.stl` (Shoulder segment & gear)
* `Arm_2.stl` & `Gear_Arm_2.stl` (Elbow segment & gear)
* `Arm_3.stl` (Wrist tilt mount)
* `Gripper_Base.stl` (Wrist roll & gripper mount)
* `Grip.stl` (Claw finger)
* `Link.stl` (Gripper linkage rod)
* `Microservo_horn.stl` (Horn adapter)

### B. Screws, Nuts & Fasteners
* **M3 Screw Assortment Kit:**
  * `M3 × 8mm` (approx. 6–8 pcs)
  * `M3 × 10mm / 12mm` (approx. 10 pcs)
  * `M3 × 16mm / 20mm` (approx. 6–8 pcs for joint pivots)
  * `M3 Hex Nuts` (approx. 15–20 pcs, standard or nyloc)
  * `M3 Flat Washers` (prevents screws from digging into 3D prints)

### C. Desk Mount / Stability
* **Base Anchor:** A heavy wooden/acrylic mounting plate, desktop G-clamp, or heavy counterweight.
  * *Why:* When the arm extends fully forward, the torque from the 3 MG996R motors can easily tip the arm over without a clamped base.

---

## 5. Laptop Software Stack ($0 Free & Local)

| Purpose | Tool / Model | Cost |
| :--- | :--- | :--- |
| **Voice Activity Detection (VAD)** | Silero VAD (Python) | Free / Open Source |
| **Speech-to-Text (STT)** | `faster-whisper` (running locally on laptop) | Free / Open Source |
| **Brain / LLM** | Google AI Studio (Gemini 2.0 Flash) free tier OR Local Ollama (`llama3.2:3b`) | Free |
| **Text-to-Speech (TTS)** | `edge-tts` (Microsoft neural British voice: `en-GB-RyanNeural`) | Free / No API key |
| **Serial Communication** | Python `pyserial` (115200 baud packet bridge to ESP32) | Free |

