import json
import logging
import os
import time
from typing import Callable, Any
from jarmvis.serial_bridge import SerialBridge

logger = logging.getLogger("jarmvis.macros")

class MacroSequencer:
    def __init__(self, bridge: SerialBridge, macros_file: str = "config/macros.json"):
        self.bridge = bridge
        self.macros_file = macros_file
        self.macros: dict[str, list[dict[str, Any]]] = {}
        self.load_macros()

    def load_macros(self) -> dict:
        if os.path.exists(self.macros_file):
            try:
                with open(self.macros_file, "r", encoding="utf-8") as f:
                    self.macros = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.error(f"Failed to load macros from {self.macros_file}: {e}")
                self.macros = {}
        else:
            self.macros = {}
        return self.macros

    def save_waypoint(self, macro_name: str, angles: list[int], speed: int = 40, pause_ms: int = 300, face: str = "NEUTRAL") -> None:
        if macro_name not in self.macros:
            self.macros[macro_name] = []
        self.macros[macro_name].append({
            "angles": angles,
            "speed": speed,
            "pause_ms": pause_ms,
            "face": face
        })
        os.makedirs(os.path.dirname(os.path.abspath(self.macros_file)), exist_ok=True)
        with open(self.macros_file, "w", encoding="utf-8") as f:
            json.dump(self.macros, f, indent=2)

    def execute_macro(self, name: str, step_callback: Callable[[dict[str, Any]], None] | None = None) -> bool:
        if name not in self.macros:
            logger.warning(f"Macro '{name}' not found!")
            return False
        
        waypoints = self.macros[name]
        logger.info(f"Executing macro: {name} ({len(waypoints)} waypoints)")
        for wp in waypoints:
            angles = wp["angles"]
            speed = wp.get("speed", 50)
            easing = wp.get("easing", "cosine")
            face = wp.get("face", None)
            pause_sec = wp.get("pause_ms", 200) / 1000.0

            self.bridge.send_pose(angles=angles, speed=speed, easing=easing, face=face)
            if step_callback:
                step_callback(wp)
            if pause_sec > 0:
                time.sleep(pause_sec)
        return True
