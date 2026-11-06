import json
import logging
from typing import Any

logger = logging.getLogger("jarmvis.serial")

class SerialBridge:
    def __init__(self, port: str | None = None, baud: int = 115200, dry_run: bool = False):
        self.port = port
        self.baud = baud
        self.dry_run = dry_run
        self.serial = None

        if not self.dry_run and self.port is None:
            # Auto-detect ESP32 serial port if available
            try:
                import serial.tools.list_ports
                for p in serial.tools.list_ports.comports():
                    device = p.device or ""
                    if "usbserial" in device.lower() or "usbmodem" in device.lower() or "wchusbserial" in device.lower():
                        self.port = device
                        logger.info(f"Auto-detected ESP32 serial device: {self.port}")
                        break
            except Exception as e:
                logger.debug(f"Port auto-detection error: {e}")

        if not self.dry_run and self.port:
            try:
                import serial
                self.serial = serial.Serial(self.port, self.baud, timeout=1.0)
                logger.info(f"Connected to ESP32 on {self.port} @ {self.baud} baud")
            except Exception as e:
                logger.warning(f"Failed to connect to {self.port}: {e}. Falling back to dry-run mode.")
                self.dry_run = True
        else:
            self.dry_run = True

    def _transmit(self, payload: dict[str, Any]) -> bool:
        packet_str = json.dumps(payload) + "\n"
        if self.dry_run:
            cmd = payload.get("cmd", "").upper()
            if cmd == "POSE":
                print(f"🤖 [DRY-RUN POSE] Angles: {payload.get('angles')} | Speed: {payload.get('speed')}% | Easing: {payload.get('easing')} | Face: {payload.get('face')}")
            elif cmd == "REFLEX":
                print(f"⚡ [DRY-RUN REFLEX] Trigger: {payload.get('type')}")
            elif cmd == "FACE":
                print(f"👀 [DRY-RUN FACE] State: {payload.get('state')} (x={payload.get('pupil_x')}, y={payload.get('pupil_y')})")
            else:
                print(f"📦 [DRY-RUN PACKET] {packet_str.strip()}")
            return True
        
        try:
            if self.serial:
                self.serial.write(packet_str.encode("utf-8"))
                return True
        except Exception as e:
            logger.error(f"Serial transmission failed: {e}")
        return False

    def send_pose(self, angles: list[int], speed: int = 50, easing: str = "cosine", face: str | None = None) -> bool:
        if len(angles) != 6:
            raise ValueError(f"Expected 6 joint angles, got {len(angles)}")
        clamped_angles = [max(0, min(180, int(a))) for a in angles]
        payload = {
            "cmd": "pose",
            "angles": clamped_angles,
            "speed": max(1, min(100, int(speed))),
            "easing": easing,
            "face": face
        }
        return self._transmit(payload)

    def send_reflex(self, reflex_type: str) -> bool:
        payload = {
            "cmd": "reflex",
            "type": reflex_type.upper()
        }
        return self._transmit(payload)

    def send_face(self, state: str, pupil_x: int = 0, pupil_y: int = 0) -> bool:
        payload = {
            "cmd": "face",
            "state": state.upper(),
            "pupil_x": int(pupil_x),
            "pupil_y": int(pupil_y)
        }
        return self._transmit(payload)

    def close(self) -> None:
        if self.serial and self.serial.is_open:
            self.serial.close()

