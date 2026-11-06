"""Kinematic Motion & Spring-Damper Easing Engine for Jarmvis."""

import math


class MotionPlanner:
    def __init__(self, safe_limits: list[tuple[int, int]] | None = None):
        # Default safe angle bounds (min, max) for 6 joints
        self.safe_limits = safe_limits or [
            (0, 180),  # Waist
            (15, 165), # Shoulder (avoid mechanical collision with base)
            (15, 165), # Elbow
            (0, 180),  # Wrist Pitch
            (0, 180),  # Wrist Roll
            (10, 120), # Gripper (10=closed, 120=fully open)
        ]

    def clamp(self, angles: list[int | float]) -> list[int]:
        clamped = []
        for i, a in enumerate(angles):
            min_a, max_a = self.safe_limits[i]
            clamped.append(int(round(max(min_a, min(max_a, a)))))
        return clamped

    def interpolate(
        self,
        start_angles: list[int | float],
        target_angles: list[int | float],
        steps: int = 10,
        easing: str = "cosine"
    ) -> list[list[int]]:
        if steps <= 1:
            return [self.clamp(target_angles)]

        trajectory = []
        for step in range(steps):
            t = step / (steps - 1)
            if easing == "cosine":
                eased_t = (1.0 - math.cos(math.pi * t)) / 2.0
            elif easing == "linear":
                eased_t = t
            elif easing == "spring":
                # Damped spring approximation: 1 - exp(-5t) * cos(1.5*pi*t)
                eased_t = 1.0 - math.exp(-5.0 * t) * math.cos(math.pi * 1.5 * t)
            else:
                eased_t = t

            point = []
            for j in range(6):
                val = start_angles[j] + (target_angles[j] - start_angles[j]) * eased_t
                point.append(val)
            trajectory.append(self.clamp(point))
        return trajectory

    def generate_spring_overshoot(
        self,
        start: list[int | float],
        target: list[int | float],
        overshoot_deg: float = 3.0
    ) -> list[list[int]]:
        trajectory = []
        overshoot_target = []
        for j in range(6):
            diff = target[j] - start[j]
            if abs(diff) > 5:
                direction = 1 if diff > 0 else -1
                overshoot_target.append(target[j] + direction * overshoot_deg)
            else:
                overshoot_target.append(target[j])

        # Step 1: Rapid movement to overshoot target
        trajectory.extend(self.interpolate(start, overshoot_target, steps=8, easing="cosine"))
        # Step 2: Settle back to final target
        trajectory.extend(self.interpolate(overshoot_target, target, steps=5, easing="cosine"))
        return trajectory

    def generate_breathing_idle(self, current: list[int | float], step_index: int) -> list[int]:
        cycle = (step_index % 100) / 100.0 * 2 * math.pi
        shoulder_offset = math.sin(cycle) * 2.0
        elbow_offset = math.sin(cycle + 0.5) * 2.5
        result = list(current)
        result[1] = result[1] + shoulder_offset
        result[2] = result[2] + elbow_offset
        return self.clamp(result)
