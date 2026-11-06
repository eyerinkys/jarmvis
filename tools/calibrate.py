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
    parser.add_argument("--macros", type=str, default="config/macros.json", help="Path to macros JSON file")
    args = parser.parse_args()

    bridge = SerialBridge(port=args.port, dry_run=args.dry_run)
    sequencer = MacroSequencer(bridge, macros_file=args.macros)

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
        try:
            prompt = f"Current {angles} > ".strip() + " "
            cmd = input(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            break

        if not cmd:
            continue
        if cmd in ("quit", "exit"):
            break
        elif cmd.startswith("save "):
            macro_name = cmd.split(" ", 1)[1].strip().upper()
            sequencer.save_waypoint(macro_name, list(angles))
            print(f" Saved waypoint to macro: {macro_name}")
            continue
        elif cmd.startswith("run "):
            macro_name = cmd.split(" ", 1)[1].strip().upper()
            if not sequencer.execute_macro(macro_name):
                print(f" Macro '{macro_name}' not found!")
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
