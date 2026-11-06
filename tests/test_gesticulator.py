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
        fps=fps,
    )

    gesticulator = Gesticulator(
        safe_limits=[
            (0, 180),
            (15, 165),
            (15, 165),
            (0, 180),
            (0, 180),
            (10, 120),
        ]
    )
    trajectory = gesticulator.generate_trajectory(
        features=features,
        emotion="SARCASTIC",
        base_pose=[90, 90, 90, 90, 90, 30],
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

    # Verify dynamic wrist roll and claw pinch activity during speech
    wrist_rolls = [f[4] for f in trajectory]
    claws = [f[5] for f in trajectory]
    assert max(wrist_rolls) != min(wrist_rolls)  # Dynamic wrist roll flourishes
    assert min(claws) < 30  # Claw pinches tighter on emphasis


def test_gesticulator_emotion_modulation():
    fps = 50
    num_frames = 150  # 3 seconds
    rms = 0.5 * np.ones(num_frames)
    beats = np.zeros(num_frames)
    beats[25] = 1.0
    beats[75] = 1.0
    features = AudioFeatures(
        rms_envelope=rms,
        beat_onsets=beats,
        duration_sec=3.0,
        fps=fps,
    )

    gest = Gesticulator()
    traj_excited = gest.generate_trajectory(features, emotion="EXCITED")
    traj_sad = gest.generate_trajectory(features, emotion="SAD")

    # Excited should have greater arm elevation (shoulder / elbow) than sad
    avg_elbow_excited = np.mean([f[2] for f in traj_excited])
    avg_elbow_sad = np.mean([f[2] for f in traj_sad])
    assert avg_elbow_excited > avg_elbow_sad

    # Excited wrist rolls should have higher variance than sad
    wr_excited = [f[4] for f in traj_excited]
    wr_sad = [f[4] for f in traj_sad]
    assert np.var(wr_excited) > np.var(wr_sad)


def test_gesticulator_empty_features():
    features = AudioFeatures(
        rms_envelope=np.array([], dtype=np.float32),
        beat_onsets=np.array([], dtype=np.float32),
        duration_sec=0.0,
        fps=50,
    )
    gest = Gesticulator()
    traj = gest.generate_trajectory(features)
    assert traj == []

