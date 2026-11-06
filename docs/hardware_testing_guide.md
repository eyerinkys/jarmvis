# Jarmvis (Knox) - Physical Hardware Bring-Up & Testing Guide

This guide walks you through **everything** you need to test, calibrate, and run Knox on physical hardware from the moment your parts arrive.

---

## 1. Hardware & Wiring Checklist

### A. Pinout Map

| Joint / Component | Hardware Pin | GPIO on ESP32 | Wire Color Convention | Notes |
| :--- | :---: | :---: | :---: | :--- |
| **Joint 0: Waist** | PWM Signal | **GPIO 13** | Orange / Yellow | MG996R Metal Gear |
| **Joint 1: Shoulder** | PWM Signal | **GPIO 12** | Orange / Yellow | MG996R Metal Gear |
| **Joint 2: Elbow** | PWM Signal | **GPIO 14** | Orange / Yellow | MG996R Metal Gear |
| **Joint 3: Wrist Pitch** | PWM Signal | **GPIO 27** | Orange / Yellow | SG90 / MG90S Micro |
| **Joint 4: Wrist Roll** | PWM Signal | **GPIO 26** | Orange / Yellow | SG90 / MG90S Micro (End-effector) |
| **Joint 5: Claw / Gripper**| PWM Signal | **GPIO 25** | Orange / Yellow | SG90 / MG90S Micro (Pinch mechanism)|
| **OLED SDA** | I2C Data | **GPIO 21** | Blue / Green | SSD1306 128x64 I2C |
| **OLED SCL** | I2C Clock | **GPIO 22** | Yellow / White | SSD1306 128x64 I2C |
| **OLED VCC & GND** | Power | **3.3V & GND** | Red & Black | Powered from ESP32 3.3V rail |

---

### B. Power Wiring (CRITICAL SAFETY RULES)

```
 [ External 5V 5A Power Adapter ]
          │          │
         +5V        GND
          │          │
          ├──[ 1000µF Capacitor ]──┤ (Smooths motor current spikes)
          │                        │
  ┌───────┴──────┐         ┌───────┴──────┐
  │ Servo Red +  │         │ Servo Brown -│ (All 6 Servos)
  └──────────────┘         └───────┬──────┘
                                   │
              COMMON GROUND JUMPER └───> [ ESP32 GND Pin ]
                                                │
                                    [ Laptop USB Data Cable ]
                                     (Powers ESP32 logic only)
```

> [!CAUTION]
> **1. NEVER power servos from the ESP32 5V pin or laptop USB port.** The 3x MG996R servos draw up to 4A–6A peak under load, which will brownout the ESP32 or trip laptop USB protection.
> **2. YOU MUST CONNECT A COMMON GROUND:** Connect the negative/GND wire of your external 5V power supply to one of the **GND pins on the ESP32**. If you forget this common ground, the servo PWM signals have no voltage reference and the arm will violently spasm or jitter.

---

## 2. Step 0: Center Calibration (DO THIS BEFORE ASSEMBLING ARMS!)

> [!IMPORTANT]
> **Do not attach the 3D-printed horns or assemble the arm linkages yet!**
> Servos ship at random internal positions. If you assemble the arm and power it on, the motor may immediately snap 120° into a mechanical hard-stop and strip plastic gears.

### Zero/Center Calibration Procedure:
1. Connect the ESP32 to your laptop via USB.
2. Connect external 5V power and common ground.
3. Plug in the 6 servo signal wires to the ESP32 pins (13, 12, 14, 27, 26, 25).
4. Run the interactive hardware test script:
   ```bash
   python3 scripts/hardware_test.py --calibrate
   ```
5. All 5 arm servos will rotate to their exact electronic neutral center (**90.0°**), and the claw servo will move to resting rest (**30.0°**).
6. **Now**, mount the servo horns onto the splines so the arm segments and claw linkages sit at their straight, physical home positions, then tighten the horn center screws.

---

## 3. Step 1: Flashing the ESP32 Firmware

PlatformIO is already configured in `firmware/platformio.ini`.

### A. Identify USB Serial Port on macOS:
Plug your ESP32 into your Mac and run:
```bash
ls /dev/cu.usb* /dev/cu.wch*
```
Common port names:
- Silicon Labs CP2102: `/dev/cu.usbserial-0001` or `/dev/cu.SLAB_USBtoUART`
- WCH CH340: `/dev/cu.wchusbserial110` or `/dev/cu.usbserial-110`

### B. Upload Firmware:
From the project root:
```bash
cd firmware
pio run -t upload
```

### C. Verify Serial Handshake:
Open the serial monitor:
```bash
pio device monitor -b 115200
```
Press the **EN / RST** button on the ESP32. You should see:
```json
{"status":"ready","device":"jarmvis_esp32","version":"1.0"}
```
Press `Ctrl + ]` to exit the monitor.

---

## 4. Step 2: Testing with the Interactive CLI Script

We built a dedicated hardware test suite in `scripts/hardware_test.py`. Run it with your port:

```bash
python3 scripts/hardware_test.py --port /dev/cu.usbserial-0001
```

It opens an interactive diagnostic menu:

```
===================================================
     JARMVIS (KNOX) HARDWARE DIAGNOSTICS & TEST
===================================================
1. Calibrate / Center all Servos (Hold at 90°)
2. Test OLED Animated Eyes (Cycle all 8 expressions)
3. Test Joint 0: Waist Sweep (60° -> 90° -> 120°)
4. Test Joint 1: Shoulder Pitch (70° -> 90° -> 110°)
5. Test Joint 2: Elbow Pitch (70° -> 90° -> 110°)
6. Test Joint 3: Wrist Pitch Tilt (60° -> 90° -> 120°)
7. Test Joint 4: Wrist Roll Flourish (45° -> 90° -> 135°)
8. Test Joint 5: Claw Pinch & Open (12° pinch -> 30° rest -> 80° open)
9. Test Reflexes (PERK_UP, THINK, DROOP, STARTLE)
10. Test Reactive Co-Speech Gesticulation (Live speech + 50Hz arm kinematics)
0. Exit
===================================================
```

---

## 5. Step 3: Testing Full Jarmvis App

Once isolated hardware tests pass, test the full integrated assistant:

### A. Keyboard CLI Mode (Test speech & motion without speaking):
```bash
python3 -m jarmvis.app --port /dev/cu.usbserial-0001 --cli
```
Try typing:
- `Explain what you are, genius` $\rightarrow$ Knox speaks with expressive Tony Stark wrist rolls, claw micro-flexes, and animated eyes.
- `perk` $\rightarrow$ Arm perks upright into alert posture.
- `dunce` $\rightarrow$ Arm droops dejectedly into the dunce corner with sad eyes.
- `celebrate` $\rightarrow$ Arm executes victory celebration sequence.
- `home` $\rightarrow$ Smoothly returns to neutral home position.

### B. Live Hands-Free Voice Mode (With Microphone):
```bash
python3 -m jarmvis.app --port /dev/cu.usbserial-0001
```
1. Knox automatically calibrates the ambient room noise threshold (0.4s).
2. The arm pops up into the alert **`PERK_UP`** posture.
3. Speak out loud to Knox. The low-latency VAD detects your speech, immediately triggers the **`THINK`** head tilt, generates the response, and moves reactively while speaking.

---

## 6. Hardware Troubleshooting Matrix

| Symptom | Cause | Solution |
| :--- | :--- | :--- |
| **Servos violently twitch, jitter, or hum loudly** | Missing Common Ground | Connect a jumper wire between **ESP32 GND** and **Power Supply GND (-)**. |
| **ESP32 restarts / reboots when servos move** | Current spike / Brownout | 1. Ensure external 5V 5A adapter is used.<br>2. Add a 1000µF capacitor across the 5V and GND power rails near the motors. |
| **OLED display is blank / not turning on** | Wrong wiring or I2C address | 1. Check SDA $\rightarrow$ GPIO 21 and SCL $\rightarrow$ GPIO 22.<br>2. Make sure OLED VCC is plugged into **3.3V**.<br>3. In `firmware/src/eyes.h`, default address is `0x3C`. If your board uses `0x3D`, change it in `u8g2.begin()`. |
| **Mac shows "Port not found" or permission denied** | USB Driver or Cable | 1. Ensure your USB cable is **data-capable** (not charge-only).<br>2. Install CH340 or CP2102 driver for macOS if needed.<br>3. Check `ls /dev/cu.*` in Terminal. |
| **Servo turns in reverse direction** | Mechanical gear orientation | In `firmware/src/main.cpp`, invert the angle for that joint: `writeServoPWM(jointIndex, 180.0 - angle);` |
| **Arm wobbles or tips over when extending** | Base not anchored | Clamp the base plate to your desk with a G-clamp or mount it to a heavy wood baseboard. |

