import argparse
import logging
import sys
from typing import Any

from jarmvis.macros import MacroSequencer
from jarmvis.motion import MotionPlanner
from jarmvis.serial_bridge import SerialBridge
from jarmvis.tts_engine import TTSEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("jarmvis.main")

class _DefaultFallbackBrain:
    """Built-in lightweight heuristic brain until external LLM engine is connected."""
    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock

    def think(self, user_prompt: str) -> dict[str, Any]:
        lower = user_prompt.lower()
        if "pick" in lower or "block" in lower:
            return {
                "speech": "Right away, sir. Attempting to retrieve the block now.",
                "emotion": "FOCUSED",
                "face": "ALERT",
                "macro": "PICK_BLOCK"
            }
        elif "dunce" in lower or "corner" in lower or "bad" in lower or "messed up" in lower:
            return {
                "speech": "My sincere apologies, sir. Heading to the dunce corner immediately.",
                "emotion": "ASHAMED",
                "face": "SAD",
                "macro": "DUNCE_CORNER"
            }
        elif "great" in lower or "good job" in lower or "celebrate" in lower:
            return {
                "speech": "Most gratifying, sir. Always a pleasure to be of service.",
                "emotion": "EXCITED",
                "face": "HAPPY",
                "macro": "CELEBRATE"
            }
        return {
            "speech": "Standing by for your instructions, sir.",
            "emotion": "NEUTRAL",
            "face": "NEUTRAL",
            "macro": None
        }

class JarmvisApp:
    def __init__(
        self,
        bridge: SerialBridge,
        brain: Any = None,
        use_mock_ai: bool = False,
        macros_file: str = "config/macros.json"
    ):
        self.bridge = bridge
        self.use_mock_ai = use_mock_ai

        # Initialize Brain (Dependency Injection or dynamic import of JarvisBrain)
        if brain is not None:
            self.brain = brain
        else:
            try:
                from jarmvis.brain import JarvisBrain
                self.brain = JarvisBrain(use_mock=use_mock_ai)
            except ImportError:
                self.brain = _DefaultFallbackBrain(use_mock=use_mock_ai)

        self.tts = TTSEngine(use_mock=use_mock_ai)
        self.macros = MacroSequencer(bridge=self.bridge, macros_file=macros_file)
        self.motion = MotionPlanner()

    def perk_up(self) -> None:
        self.bridge.send_reflex("PERK_UP")

    def home(self) -> None:
        self.macros.execute_macro("HOME")

    def dunce(self) -> None:
        self.macros.execute_macro("DUNCE_CORNER")

    def celebrate(self) -> None:
        self.macros.execute_macro("CELEBRATE")

    def handle_voice_prompt(self, user_text: str) -> None:
        cleaned_text = user_text.strip()
        if not cleaned_text:
            return

        print(f"\n👤 [USER] \"{cleaned_text}\"")

        # 1. Immediate reflex: Thinking head tilt
        self.bridge.send_reflex("THINK")

        # 2. Query Brain
        response = self.brain.think(cleaned_text)
        speech = response.get("speech", "")
        face = response.get("face", "NEUTRAL")
        macro = response.get("macro", None)

        print(f"🤖 [JARVIS] \"{speech}\" (Face: {face}, Macro: {macro})")
        if face:
            self.bridge.send_face(face)

        # 3. Speak response
        if speech:
            self.tts.speak(speech)

        # 4. Trigger physical macro if requested
        if macro:
            self.macros.execute_macro(macro)

    def run_cli_interactive(self) -> None:
        print("\n=======================================================")
        print("          JARMVIS: JARVIS MIND & DUM-E BODY            ")
        print("=======================================================")
        print("Commands:")
        print("  - Type any statement to talk (e.g., 'Pick up that block')")
        print("  - 'perk' to test instant reflex")
        print("  - 'dunce' to test shame dejected droop")
        print("  - 'celebrate' to test victory claw clack")
        print("  - 'home' to reset to rest position")
        print("  - 'quit' to exit\n")

        # Initial wake up gesture
        self.perk_up()

        while True:
            try:
                line = input("Jarmvis> ").strip()
                if not line:
                    continue
                cmd_lower = line.lower()
                if cmd_lower in ["quit", "exit"]:
                    break
                elif cmd_lower == "perk":
                    self.perk_up()
                elif cmd_lower == "dunce":
                    self.dunce()
                elif cmd_lower == "celebrate":
                    self.celebrate()
                elif cmd_lower == "home":
                    self.home()
                else:
                    self.handle_voice_prompt(line)
            except (KeyboardInterrupt, EOFError):
                break
        print("\nShutting down Jarmvis.")

def main():
    parser = argparse.ArgumentParser(description="Jarmvis Master Runner")
    parser.add_argument("--port", type=str, default=None, help="ESP32 serial port (e.g. /dev/cu.usbserial-*)")
    parser.add_argument("--dry-run", action="store_true", help="Run in terminal mock mode without ESP32")
    parser.add_argument("--mock-ai", action="store_true", help="Use instant mock brain and TTS for testing")
    args = parser.parse_args()

    bridge = SerialBridge(port=args.port, dry_run=args.dry_run)
    app = JarmvisApp(bridge=bridge, use_mock_ai=args.mock_ai)
    app.run_cli_interactive()

if __name__ == "__main__":
    main()
