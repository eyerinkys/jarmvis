#!/usr/bin/env python3
"""Interactive Hardware Diagnostic & Bring-Up Test Suite for Jarmvis (Knox)."""

import argparse
import sys
import time
from jarmvis.audio_analyzer import AudioAnalyzer
from jarmvis.gesticulator import Gesticulator
from jarmvis.playback_engine import CoordinatedPlaybackEngine
from jarmvis.serial_bridge import SerialBridge
from jarmvis.tts_engine import TTSEngine


def calibrate_neutral(bridge: SerialBridge) -> None:
    print("\n[Calibrate] Centering all 6 joints to safe electronic neutral:")
    print("  Joints 0-4 (Waist, Shoulder, Elbow, Wrist Pitch, Wrist Roll) -> 90°")
    print("  Joint 5 (Claw) -> 30° (Relaxed Rest)")
    print("Hold position active. You can now mount the servo horns and linkages securely.\n")
    bridge.send_pose(angles=[90, 90, 90, 90, 90, 30], speed=40)
    time.sleep(1.0)


def test_oled_eyes(bridge: SerialBridge) -> None:
    print("\n[OLED] Cycling through all 8 eye expressions:")
    faces = ["ALERT", "FOCUSED", "HAPPY", "CURIOUS", "CONFUSED", "ANGRY", "SAD", "NEUTRAL"]
    for face in faces:
        print(f"  Displaying Face: {face}")
        bridge.send_face(face)
        time.sleep(1.2)
    bridge.send_face("NEUTRAL")


def test_single_joint(bridge: SerialBridge, joint_index: int, joint_name: str, test_angles: list[int]) -> None:
    print(f"\n[Test Joint {joint_index}: {joint_name}] Sweeping positions:")
    base = [90, 90, 90, 90, 90, 30]
    for angle in test_angles:
        base[joint_index] = angle
        print(f"  Target: {joint_name} = {angle}°")
        bridge.send_pose(angles=base, speed=35)
        time.sleep(0.9)
    # Return to neutral
    base[joint_index] = 90 if joint_index < 5 else 30
    bridge.send_pose(angles=base, speed=35)
    time.sleep(0.5)


def test_reflexes(bridge: SerialBridge) -> None:
    print("\n[Reflexes] Testing built-in kinetic reflexes:")
    reflexes = ["PERK_UP", "THINK", "STARTLE", "DROOP"]
    for r in reflexes:
        print(f"  Firing reflex: {r}")
        bridge.send_reflex(r)
        time.sleep(2.0)
    print("  Returning home...")
    bridge.send_pose(angles=[90, 90, 90, 90, 90, 30], speed=40)
    bridge.send_face("NEUTRAL")


def test_speech_gesticulation(bridge: SerialBridge) -> None:
    print("\n[Gesticulation] Testing live speech-driven reactive motion...")
    tts = TTSEngine(use_mock=False)
    analyzer = AudioAnalyzer(fps=50)
    gesticulator = Gesticulator()
    playback = CoordinatedPlaybackEngine(bridge=bridge, fps=50)

    test_phrase = "I am Knox. Part genius, part metallic swagger. Watch the wrist roll and claw pinch."
    print(f"  Knox speaking: \"{test_phrase}\"")
    bridge.send_face("HAPPY")

    audio_file = tts.synthesize_to_file(test_phrase, emotion="CONFIDENT")
    if not audio_file:
        print("  Notice: Cloud TTS unavailable. Falling back to synthetic mock audio.")
        tts.use_mock = True
        audio_file = tts.synthesize_to_file(test_phrase, emotion="CONFIDENT")

    try:
        features = analyzer.extract_features_from_file(audio_file)
        print(f"  Extracted {len(features.rms_envelope)} 50Hz frames ({features.duration_sec:.2f}s duration)")
        trajectory = gesticulator.generate_trajectory(
            features=features,
            emotion="CONFIDENT",
            base_pose=[90, 90, 90, 90, 90, 30],
        )
        print("  Streaming 50Hz trajectory in sync with audio...")
        playback.play_with_gestures(audio_path=audio_file, trajectory=trajectory, blocking=True)
    finally:
        import os
        if audio_file and os.path.exists(audio_file):
            try:
                os.remove(audio_file)
            except OSError:
                pass
        bridge.send_face("NEUTRAL")
    print("  Done. Gesticulation completed cleanly.\n")


def print_menu():
    print("\n" + "=" * 55)
    print("     JARMVIS (KNOX) HARDWARE DIAGNOSTICS & TEST")
    print("=" * 55)
    print("1. Calibrate / Center all Servos (Hold at 90° / 30°)")
    print("2. Test OLED Animated Eyes (Cycle all 8 expressions)")
    print("3. Test Joint 0: Waist Sweep (60° -> 90° -> 120°)")
    print("4. Test Joint 1: Shoulder Pitch (70° -> 90° -> 110°)")
    print("5. Test Joint 2: Elbow Pitch (70° -> 90° -> 110°)")
    print("6. Test Joint 3: Wrist Pitch Tilt (60° -> 90° -> 120°)")
    print("7. Test Joint 4: Wrist Roll Flourish (45° -> 90° -> 135°)")
    print("8. Test Joint 5: Claw Pinch & Open (12° -> 30° -> 80°)")
    print("9. Test Reflexes (PERK_UP, THINK, STARTLE, DROOP)")
    print("10. Test Reactive Co-Speech Gesticulation (Speech + 50Hz Arm)")
    print("0. Exit")
    print("=" * 55)


def main():
    parser = argparse.ArgumentParser(description="Jarmvis Hardware Bring-Up & Test Tool")
    parser.add_argument("--port", type=str, default=None, help="ESP32 serial port (e.g. /dev/cu.usbserial-*)")
    parser.add_argument("--calibrate", action="store_true", help="Directly enter calibration hold mode and exit")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without physical serial hardware")
    args = parser.parse_args()

    bridge = SerialBridge(port=args.port, dry_run=args.dry_run)

    if args.calibrate:
        calibrate_neutral(bridge)
        return

    while True:
        print_menu()
        try:
            choice = input("Select an option [0-10]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if choice == "0":
            print("Exiting.")
            break
        elif choice == "1":
            calibrate_neutral(bridge)
        elif choice == "2":
            test_oled_eyes(bridge)
        elif choice == "3":
            test_single_joint(bridge, 0, "Waist", [60, 90, 120, 90])
        elif choice == "4":
            test_single_joint(bridge, 1, "Shoulder", [70, 90, 110, 90])
        elif choice == "5":
            test_single_joint(bridge, 2, "Elbow", [70, 90, 110, 90])
        elif choice == "6":
            test_single_joint(bridge, 3, "Wrist Pitch", [60, 90, 120, 90])
        elif choice == "7":
            test_single_joint(bridge, 4, "Wrist Roll", [45, 90, 135, 90])
        elif choice == "8":
            test_single_joint(bridge, 5, "Claw", [12, 30, 80, 30])
        elif choice == "9":
            test_reflexes(bridge)
        elif choice == "10":
            test_speech_gesticulation(bridge)
        else:
            print("Invalid selection. Please choose 0 to 10.")


if __name__ == "__main__":
    main()
