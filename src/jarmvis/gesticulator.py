import math
from typing import Any
import numpy as np
from jarmvis.audio_analyzer import AudioFeatures


DEFAULT_LIMITS: list[tuple[int, int]] = [
    (0, 180),   # 0: Waist
    (15, 165),  # 1: Shoulder (prevents base crash)
    (15, 165),  # 2: Elbow
    (0, 180),   # 3: Wrist Pitch
    (0, 180),   # 4: Wrist Roll (End-effector rotation)
    (10, 120),  # 5: Gripper Claw (10=pinched, 120=fully open)
]

EMOTION_PRESETS: dict[str, dict[str, Any]] = {
    "CONFIDENT": {
        "energy": 1.2,
        "shoulder_bias": 3.0,
        "elbow_bias": 5.0,
        "wrist_roll_amp": 24.0,
        "wrist_pitch_bias": 2.0,
        "pinch_strength": 0.8,
        "claw_rest": 32.0,
    },
    "SARCASTIC": {
        "energy": 1.1,
        "shoulder_bias": 1.0,
        "elbow_bias": 3.0,
        "wrist_roll_amp": 30.0,
        "wrist_pitch_bias": 6.0,  # Inquisitive head/wrist tilt
        "pinch_strength": 1.0,    # Sharp, tight precision pinch
        "claw_rest": 30.0,
    },
    "EXCITED": {
        "energy": 1.5,
        "shoulder_bias": 8.0,
        "elbow_bias": 10.0,
        "wrist_roll_amp": 36.0,
        "wrist_pitch_bias": 4.0,
        "pinch_strength": 0.6,
        "claw_rest": 45.0,
    },
    "HAPPY": {
        "energy": 1.1,
        "shoulder_bias": 4.0,
        "elbow_bias": 6.0,
        "wrist_roll_amp": 22.0,
        "wrist_pitch_bias": 2.0,
        "pinch_strength": 0.5,
        "claw_rest": 35.0,
    },
    "ANGRY": {
        "energy": 1.4,
        "shoulder_bias": 6.0,
        "elbow_bias": 2.0,
        "wrist_roll_amp": 15.0,
        "wrist_pitch_bias": -6.0,
        "pinch_strength": 1.2,
        "claw_rest": 20.0,
    },
    "SAD": {
        "energy": 0.4,
        "shoulder_bias": -10.0,
        "elbow_bias": -12.0,
        "wrist_roll_amp": 6.0,
        "wrist_pitch_bias": -12.0,
        "pinch_strength": 0.0,
        "claw_rest": 25.0,
    },
    "ASHAMED": {
        "energy": 0.3,
        "shoulder_bias": -12.0,
        "elbow_bias": -15.0,
        "wrist_roll_amp": 4.0,
        "wrist_pitch_bias": -16.0,
        "pinch_strength": 0.0,
        "claw_rest": 22.0,
    },
    "CURIOUS": {
        "energy": 1.0,
        "shoulder_bias": 3.0,
        "elbow_bias": 4.0,
        "wrist_roll_amp": 20.0,
        "wrist_pitch_bias": 8.0,
        "pinch_strength": 0.7,
        "claw_rest": 32.0,
    },
    "NEUTRAL": {
        "energy": 1.0,
        "shoulder_bias": 0.0,
        "elbow_bias": 0.0,
        "wrist_roll_amp": 16.0,
        "wrist_pitch_bias": 0.0,
        "pinch_strength": 0.5,
        "claw_rest": 30.0,
    },
}


class Gesticulator:
    def __init__(self, safe_limits: list[tuple[int, int]] | None = None):
        self.safe_limits = safe_limits or DEFAULT_LIMITS

    def clamp(self, angles: list[float | int]) -> list[int]:
        clamped = []
        for i, a in enumerate(angles):
            min_a, max_a = self.safe_limits[i]
            clamped.append(int(round(max(min_a, min(max_a, float(a))))))
        return clamped

    def generate_trajectory(
        self,
        features: AudioFeatures,
        emotion: str = "CONFIDENT",
        base_pose: list[int] | None = None,
    ) -> list[list[int]]:
        """Generates continuous 50Hz joint trajectories synchronized with speech audio."""
        if features is None or len(features.rms_envelope) == 0:
            return []

        num_frames = len(features.rms_envelope)
        fps = features.fps or 50
        base = list(base_pose) if base_pose else [90, 90, 90, 90, 90, 30]

        emo_key = str(emotion).upper()
        emo_cfg = EMOTION_PRESETS.get(emo_key, EMOTION_PRESETS["NEUTRAL"])
        energy_scale = float(emo_cfg["energy"])

        trajectory: list[list[int]] = []

        for i in range(num_frames):
            t = float(i) / fps
            rms = float(features.rms_envelope[i])
            beat = float(features.beat_onsets[i]) if i < len(features.beat_onsets) else 0.0

            # ----------------------------------------------------
            # Layer 1: Biological Micro-Drift (Organic Life)
            # Continuous multi-sine breathing sway so the arm is never still
            # ----------------------------------------------------
            drift_waist = 1.0 * math.sin(2.0 * math.pi * 0.25 * t)
            drift_shoulder = 1.5 * math.sin(2.0 * math.pi * 0.35 * t) + 0.8 * math.sin(2.0 * math.pi * 0.75 * t + 0.4)
            drift_elbow = 1.8 * math.sin(2.0 * math.pi * 0.35 * t + 0.6) + 0.6 * math.cos(2.0 * math.pi * 0.60 * t)
            drift_wp = 1.2 * math.sin(2.0 * math.pi * 0.45 * t + 1.0)
            drift_wr = 2.0 * math.sin(2.0 * math.pi * 0.30 * t)
            drift_claw = 1.0 * math.sin(2.0 * math.pi * 0.40 * t)

            # ----------------------------------------------------
            # Layer 2: Audio Prosody & Beats (Speech Cadence)
            # Volume pulses elbow/shoulder, beats trigger syllable nods & twitches
            # ----------------------------------------------------
            prosody_shoulder = emo_cfg["shoulder_bias"] + (rms * 3.5 + beat * 2.5) * energy_scale
            prosody_elbow = emo_cfg["elbow_bias"] + (rms * 7.0 + beat * 5.0) * energy_scale
            prosody_wp = emo_cfg["wrist_pitch_bias"] - (beat * 6.5 * energy_scale)
            prosody_waist = drift_waist + (beat * 2.0 * math.sin(t * 3.0))

            # ----------------------------------------------------
            # Layer 3: Expressive End-Effector Motifs (Flourishes & Pinch)
            # Wrist Roll (supination/pronation flourishes) + Claw Pinch
            # ----------------------------------------------------
            roll_amp = emo_cfg["wrist_roll_amp"]
            # Gestural cycle for forearm rotation flourishes (explaining / palm open)
            roll_cycle = math.sin(2.0 * math.pi * 0.75 * t) * roll_amp
            # Dynamic twitch on syllable beats
            beat_roll_twitch = beat * 10.0 * math.cos(t * 5.0)
            prosody_wr = roll_cycle + beat_roll_twitch + drift_wr

            # Claw gripper behavior:
            # Emphatic beats with pinch strength clamp fingers into a "precision pinch",
            # while broad speech volume softly expands fingers open.
            claw_rest = float(emo_cfg["claw_rest"])
            pinch_factor = float(emo_cfg["pinch_strength"])
            if beat > 0.35 and pinch_factor > 0.0:
                # Pinch fingers tight (down to ~12-16 degrees)
                claw_offset = -(beat * 18.0 * pinch_factor)
            else:
                # Open fingers gently proportional to volume
                claw_offset = (rms * 12.0) + drift_claw

            claw_val = claw_rest + claw_offset

            # Combine all layers additively onto base pose
            pose = [
                base[0] + prosody_waist,
                base[1] + prosody_shoulder + drift_shoulder,
                base[2] + prosody_elbow + drift_elbow,
                base[3] + prosody_wp + drift_wp,
                base[4] + prosody_wr,
                claw_val,
            ]

            trajectory.append(self.clamp(pose))

        return trajectory
