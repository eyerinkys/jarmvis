import pytest
from jarmvis.motion import MotionPlanner

def test_cosine_interpolation():
    planner = MotionPlanner(safe_limits=[(0, 180)] * 6)
    start = [0, 0, 0, 0, 0, 0]
    target = [90, 90, 90, 90, 90, 90]
    trajectory = planner.interpolate(start, target, steps=5, easing="cosine")
    assert len(trajectory) == 5
    assert trajectory[0] == start
    assert trajectory[-1] == target
    assert trajectory[2] == [45, 45, 45, 45, 45, 45]

def test_spring_overshoot():
    planner = MotionPlanner()
    start = [90, 90, 90, 90, 90, 90]
    target = [90, 120, 90, 90, 90, 90]
    trajectory = planner.generate_spring_overshoot(start, target, overshoot_deg=5.0)
    shoulder_angles = [pt[1] for pt in trajectory]
    assert max(shoulder_angles) > 120
    assert trajectory[-1] == target

def test_idle_breathing():
    planner = MotionPlanner()
    base = [90, 60, 110, 45, 90, 30]
    p1 = planner.generate_breathing_idle(base, step_index=0)
    p2 = planner.generate_breathing_idle(base, step_index=25)
    assert p1[1] != p2[1]

def test_clamp_default_limits():
    planner = MotionPlanner()
    # Limits: [(0, 180), (15, 165), (15, 165), (0, 180), (0, 180), (10, 120)]
    out_of_bounds = [-10, 5, 180, 200, -5, 150]
    clamped = planner.clamp(out_of_bounds)
    assert clamped == [0, 15, 165, 180, 0, 120]

def test_interpolate_single_step():
    planner = MotionPlanner()
    target = [90, 90, 90, 90, 90, 90]
    trajectory = planner.interpolate(start_angles=[50, 50, 50, 50, 50, 50], target_angles=target, steps=1)
    assert len(trajectory) == 1
    assert trajectory[0] == target
