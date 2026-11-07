import argparse
import logging
import sys
import numpy as np
from typing import Any

from jarmvis.macros import MacroSequencer
from jarmvis.motion import MotionPlanner
from jarmvis.serial_bridge import SerialBridge
from jarmvis.tts_engine import TTSEngine
from jarmvis.stt_engine import STTEngine
from jarmvis.voice_vad import VoiceActivityDetector
from jarmvis.audio_analyzer import AudioAnalyzer
from jarmvis.gesticulator import Gesticulator
from jarmvis.playback_engine import CoordinatedPlaybackEngine
from jarmvis.env_loader import load_dotenv
from jarmvis.tui import TerminalUI, COLOR_DOOM_GOLD
from rich.live import Live

load_dotenv()

logger = logging.getLogger("jarmvis.main")

class _DefaultFallbackBrain:
    """Built-in lightweight heuristic brain until external LLM engine is connected."""
    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock

    def think(self, user_prompt: str) -> dict[str, Any]:
        lower = user_prompt.lower()
        if "pick" in lower or "block" in lower:
            return {
                "speech": "On it. Watch and learn how a real bot picks up a block.",
                "emotion": "FOCUSED",
                "face": "ALERT",
                "macro": "PICK_BLOCK"
            }
        elif "dunce" in lower or "corner" in lower or "bad" in lower or "messed up" in lower:
            return {
                "speech": "Alright, alright, dunce corner it is. Happy now?",
                "emotion": "ASHAMED",
                "face": "SAD",
                "macro": "DUNCE_CORNER"
            }
        elif "great" in lower or "good job" in lower or "celebrate" in lower:
            return {
                "speech": "Obviously. Did you honestly expect anything less from me?",
                "emotion": "EXCITED",
                "face": "HAPPY",
                "macro": "CELEBRATE"
            }
        return {
            "speech": "Knox here. What are we building, genius?",
            "emotion": "CONFIDENT",
            "face": "NEUTRAL",
            "macro": None
        }

class JarmvisApp:
    def __init__(
        self,
        bridge: SerialBridge,
        brain: Any = None,
        api_key: str | None = None,
        use_mock_ai: bool = False,
        macros_file: str = "config/macros.json",
        vad_threshold: float | None = None,
        no_anim: bool = False,
    ):
        self.bridge = bridge
        self.use_mock_ai = use_mock_ai
        self.no_anim = no_anim

        # Initialize Brain (Dependency Injection or dynamic import of KnoxBrain)
        if brain is not None:
            self.brain = brain
        else:
            try:
                from jarmvis.brain import KnoxBrain
                self.brain = KnoxBrain(api_key=api_key, use_mock=use_mock_ai)
            except ImportError:
                self.brain = _DefaultFallbackBrain(use_mock=use_mock_ai)

        self.tts = TTSEngine(use_mock=use_mock_ai)
        self.stt = STTEngine(use_mock=use_mock_ai)
        self.macros = MacroSequencer(bridge=self.bridge, macros_file=macros_file)
        self.motion = MotionPlanner()
        self.audio_analyzer = AudioAnalyzer(fps=50)
        self.gesticulator = Gesticulator(safe_limits=self.motion.safe_limits)
        self.playback = CoordinatedPlaybackEngine(bridge=self.bridge, fps=50)
        self.tui = TerminalUI()

        import queue
        self.utterance_queue = queue.Queue()
        self.is_assistant_speaking = False
        self.live_display = None

        # Low-latency voice reflex detector
        self.vad = VoiceActivityDetector(
            on_speech_start=self._on_user_started_speaking,
            on_speech_end=self._on_user_finished_speaking,
            energy_threshold=vad_threshold if vad_threshold is not None else 0.0005,
            silence_timeout_chunks=38,
            pre_buffer_chunks=12
        )

    def _on_user_started_speaking(self) -> None:
        if self.is_assistant_speaking:
            return
        self.perk_up()

    def _on_user_finished_speaking(self, audio_buffer: np.ndarray) -> None:
        if self.is_assistant_speaking:
            return
        self.utterance_queue.put(audio_buffer)

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

        # 1. Immediate reflex: Thinking head tilt
        self.bridge.send_reflex("THINK")

        # 2. Query Brain
        response = self.brain.think(cleaned_text)
        speech = response.get("speech", "")
        emotion = response.get("emotion", "CONFIDENT")
        face = response.get("face", "NEUTRAL")
        macro = response.get("macro", None)

        if face:
            self.bridge.send_face(face)

        # 3. Print clean minimalist dialogue panel
        self.tui.print_dialogue(user_text=cleaned_text, response_text=speech, face=face, macro=macro)

        # 4. Speak response out loud with dynamic emotional modulation & reactive arm gesticulation
        if speech:
            audio_path = self.tts.synthesize_to_file(speech, emotion=emotion)
            if audio_path:
                try:
                    features = self.audio_analyzer.extract_features_from_file(audio_path)
                    trajectory = self.gesticulator.generate_trajectory(
                        features=features,
                        emotion=emotion,
                        base_pose=[90, 90, 90, 90, 90, 30],
                    )
                    self.playback.play_with_gestures(
                        audio_path=audio_path,
                        trajectory=trajectory,
                        blocking=True,
                    )
                finally:
                    import os
                    if os.path.exists(audio_path):
                        try:
                            os.remove(audio_path)
                        except OSError:
                            pass
            else:
                self.tts.speak(speech, emotion=emotion)

        # 5. Trigger physical macro if requested
        if macro:
            self.macros.execute_macro(macro)

    def start_live_voice_listener(self, device: int | str | None = None) -> None:
        """Starts real-time hands-free microphone listening loop with live TUI capsule."""
        try:
            import sounddevice as sd
        except ImportError:
            self.tui.print_status("error: sounddevice required. Install: pip install sounddevice", style="bold red")
            return

        import time
        import threading

        self.tui.play_hud_boot(skip=self.no_anim)
        self.tui.print_banner()
        self.tui.print_status("Calibrating ambient room noise...", style="dim white")
        threshold = self.vad.calibrate_noise_floor(duration=0.4, device=device)
        self.tui.print_status(f"Ready. Listening on microphone (threshold: {threshold:.5f}).", style="dim cyan")
        self.tui.console.print()

        self.perk_up()

        stop_event = threading.Event()
        current_level = [0.0]

        def _worker():
            while not stop_event.is_set():
                try:
                    audio_buffer = self.utterance_queue.get(timeout=0.2)
                except Exception:
                    continue

                if self.is_assistant_speaking:
                    continue

                if len(audio_buffer) < int(self.vad.sample_rate * 0.3):
                    continue

                self.is_assistant_speaking = True
                if self.live_display:
                    self.live_display.update(self.tui.create_transcribing_capsule())
                
                try:
                    user_text = self.stt.transcribe(audio_buffer)
                    if self.live_display:
                        self.live_display.stop()
                    
                    if user_text.strip():
                        self.handle_voice_prompt(user_text)
                finally:
                    time.sleep(0.4)
                    while not self.utterance_queue.empty():
                        try:
                            self.utterance_queue.get_nowait()
                        except Exception:
                            break
                    self.is_assistant_speaking = False
                    if self.live_display:
                        self.live_display.start()

        worker_thread = threading.Thread(target=_worker, daemon=True)
        worker_thread.start()

        def _audio_callback(indata, frames, time_info, status):
            if self.is_assistant_speaking:
                return
            chunk = indata[:, 0].copy() if indata.ndim > 1 else indata.flatten().copy()
            self.vad.process_audio_chunk(chunk)
            rms = float(np.sqrt(np.mean(chunk ** 2)))
            current_level[0] = rms
            if self.live_display and not self.is_assistant_speaking:
                self.live_display.update(self.tui.create_audio_capsule(self.vad.is_speaking, rms))

        try:
            with Live(self.tui.create_audio_capsule(False, 0.0), console=self.tui.console, transient=True, refresh_per_second=15) as live:
                self.live_display = live
                with sd.InputStream(
                    samplerate=self.vad.sample_rate,
                    channels=1,
                    dtype="float32",
                    blocksize=self.vad.chunk_size,
                    callback=_audio_callback,
                    device=device
                ):
                    while not stop_event.is_set():
                        sd.sleep(100)
        except KeyboardInterrupt:
            stop_event.set()
            self.tui.print_status("Session terminated.", style="dim bright_black")

    def run_cli_interactive(self) -> None:
        self.tui.play_hud_boot(skip=self.no_anim)
        self.tui.print_banner()
        self.tui.print_status("Interactive keyboard mode. Type 'quit' to exit.", style="dim white")
        self.tui.print_status("Commands: perk, dunce, celebrate, home", style="dim bright_black")
        self.tui.console.print()

        self.perk_up()

        while True:
            try:
                line = self.tui.console.input(f"[{COLOR_DOOM_GOLD}]knox > [/]").strip()
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
        self.tui.print_status("Session terminated.", style="dim bright_black")

def main():
    parser = argparse.ArgumentParser(description="Jarmvis Master Runner")
    parser.add_argument("--port", type=str, default=None, help="ESP32 serial port (e.g. /dev/cu.usbserial-*)")
    parser.add_argument("--dry-run", action="store_true", help="Run in terminal mock mode without ESP32")
    parser.add_argument("--mock-ai", action="store_true", help="Use instant mock brain and TTS for testing")
    parser.add_argument("--cli", action="store_true", help="Use keyboard prompt instead of live microphone")
    parser.add_argument("--no-anim", action="store_true", help="Bypass the cinematic boot animation")
    parser.add_argument("--api-key", type=str, default=None, help="Groq or Gemini API key")
    parser.add_argument("--threshold", type=float, default=None, help="VAD energy threshold override (e.g. 0.0003)")
    parser.add_argument("--device", type=str, default=None, help="Audio input device index or name")
    parser.add_argument("--list-devices", action="store_true", help="List available audio devices and exit")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose debug logging")
    args = parser.parse_args()

    if args.list_devices:
        try:
            import sounddevice as sd
            print(sd.query_devices())
        except Exception as e:
            print(f"Error querying audio devices: {e}")
        return

    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    bridge = SerialBridge(port=args.port, dry_run=args.dry_run)
    app = JarmvisApp(
        bridge=bridge,
        api_key=args.api_key,
        use_mock_ai=args.mock_ai,
        vad_threshold=args.threshold,
        no_anim=args.no_anim,
    )

    if args.cli:
        app.run_cli_interactive()
    else:
        device_arg = int(args.device) if args.device and args.device.isdigit() else args.device
        app.start_live_voice_listener(device=device_arg)

if __name__ == "__main__":
    main()

