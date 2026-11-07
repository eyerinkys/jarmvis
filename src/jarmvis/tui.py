import math
import time
from typing import Any
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text
from rich.style import Style
from rich.table import Table
from rich.live import Live
from rich import box

# Doctor Doom & Mark-LXXXV Specification Palette Tokens
COLOR_DOOM_GREEN   = "#477A43"
COLOR_SHADOW_GREEN = "#24452D"
COLOR_DOOM_GOLD    = "#D6AD35"
COLOR_MASK_STEEL   = "#85898A"

console = Console()

KNOX_ASCII_WORDMARK = [
    "  ██╗  ██╗███╗   ██╗ ██████╗ ██╗  ██╗",
    "  ██║ ██╔╝████╗  ██║██╔═══██╗╚██╗██╔╝",
    "  █████╔╝ ██╔██╗ ██║██║   ██║ ╚███╔╝ ",
    "  ██╔═██╗ ██║╚██╗██║██║   ██║ ██╔██╗ ",
    "  ██║  ██╗██║ ╚████║╚██████╔╝██╔╝ ██╗",
    "  ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝",
]


class TerminalUI:
    """Swiss-minimalist, zero-emoji, avionics-grade terminal interface.
    
    Styled with the authentic Doctor Doom & Mark-LXXXV titanium-gold palette.
    """

    def __init__(self, console_instance: Console | None = None):
        self.console = console_instance or console

    def print_banner(self) -> None:
        """Prints the Claude CLI-style giant KNOX wordmark and workshop metadata."""
        self.console.print()
        
        # Render the large block wordmark in Doom Gold
        wordmark_text = Text()
        for line in KNOX_ASCII_WORDMARK:
            wordmark_text.append(f"{line}\n", style=Style(color=COLOR_DOOM_GOLD, bold=True))
        
        self.console.print(wordmark_text)

        # Hairline metadata sub-bar
        meta = Text()
        meta.append("  KNOX WORKSHOP SYSTEM", style=Style(color=COLOR_MASK_STEEL, bold=True))
        meta.append("  |  ", style=Style(color=COLOR_SHADOW_GREEN))
        meta.append("MARK-LXXXV RUNTIME", style=Style(color=COLOR_MASK_STEEL))
        meta.append("  |  ", style=Style(color=COLOR_SHADOW_GREEN))
        meta.append("LATVERIA SPEC-8", style=Style(color=COLOR_DOOM_GREEN))
        
        status = Text()
        status.append("  STATUS: ", style=Style(color=COLOR_MASK_STEEL))
        status.append("ONLINE", style=Style(color=COLOR_DOOM_GREEN, bold=True))
        status.append("  |  ", style=Style(color=COLOR_SHADOW_GREEN))
        status.append("BUS: 6-DOF LEDC HW PWM 50Hz", style=Style(color=COLOR_MASK_STEEL))
        status.append("  |  ", style=Style(color=COLOR_SHADOW_GREEN))
        status.append("VAD <30ms", style=Style(color=COLOR_MASK_STEEL))

        content = Group(meta, Text(), status)
        self.console.print(Panel(
            content,
            box=box.ROUNDED,
            border_style=COLOR_SHADOW_GREEN,
            expand=False,
            padding=(0, 2)
        ))
        self.console.print()

    def play_hud_boot(self, fast: bool = False, skip: bool = False) -> None:
        """Executes a realistic Iron Man Mark-LXXXV / JARVIS helmet HUD initialization.
        
        Renders transiently in-place without terminal scrollback clutter.
        """
        if skip:
            return

        delay = 0.02 if fast else 0.07

        # Frame generation helper functions
        def frame_reticle(step: int) -> Panel:
            if step == 0:
                body = Text("\n              [ · ]              \n", style=Style(color=COLOR_DOOM_GOLD))
                sub = "ACQUIRING RETICLE FOCUS"
            elif step == 1:
                body = Text("\n       [ ───┼─── ]       [ ───┼─── ]       \n", style=Style(color=COLOR_DOOM_GOLD))
                sub = "COLLIMATING DUAL OPTIC AXES"
            else:
                body = Text(
                    "   ┌──       ──┐                       ┌──       ──┐   \n"
                    "   │     ┼     │    [ COLLIMATED ]     │     ┼     │   \n"
                    "   └──       ──┘                       └──       ──┘   \n",
                    style=Style(color=COLOR_DOOM_GOLD, bold=True)
                )
                sub = "AZIMUTH: 000.0°  ELEVATION: +00.0°  OPTICS: f/1.4 35mm"

            t = Text()
            t.append("OPTICAL HUD INIT\n", style=Style(color=COLOR_MASK_STEEL, bold=True))
            t.append_text(body)
            t.append(f"  {sub}", style=Style(color=COLOR_DOOM_GREEN))
            return Panel(t, box=box.ROUNDED, border_style=COLOR_SHADOW_GREEN, expand=False, padding=(0, 2))

        def frame_horizon(level: bool) -> Panel:
            if not level:
                pitch_str = "PITCH: -02.40°   ROLL: +01.80°"
                horizon_line = "      ━━━━━━╸      [ -02.4° ]      ╺━━━━━━"
                status_str = "INERTIAL PLATFORM: CALIBRATING..."
                h_style = Style(color=COLOR_DOOM_GOLD)
            else:
                pitch_str = "PITCH: +00.00°   ROLL: +00.00°"
                horizon_line = "      ━━━━━━━━━━━  [  00.0° ]  ━━━━━━━━━━━"
                status_str = "INERTIAL PLATFORM: LOCKED  |  6-DOF IMU: CALIBRATED"
                h_style = Style(color=COLOR_DOOM_GREEN, bold=True)

            t = Text()
            t.append("ARTIFICIAL HORIZON & GYRO PITCH LADDER\n", style=Style(color=COLOR_MASK_STEEL, bold=True))
            t.append("              ───┬─── [ -05.0° ] ───┬───              \n", style=Style(color=COLOR_SHADOW_GREEN))
            t.append("                 │                  │                 \n", style=Style(color=COLOR_SHADOW_GREEN))
            t.append(f"{horizon_line}\n", style=h_style)
            t.append("                 │                  │                 \n", style=Style(color=COLOR_SHADOW_GREEN))
            t.append("              ───┴─── [ +05.0° ] ───┴───              \n", style=Style(color=COLOR_SHADOW_GREEN))
            t.append(f"  {pitch_str}  |  {status_str}", style=Style(color=COLOR_MASK_STEEL))
            return Panel(t, box=box.ROUNDED, border_style=COLOR_SHADOW_GREEN, expand=False, padding=(0, 2))

        def frame_visors() -> Table:
            grid = Table.grid(padding=1)
            left_text = Text(
                "LEDC HW PWM: 50 Hz (6 CHANNELS)\n"
                "BUS VOLTAGE: 6.02 V NOMINAL\n"
                "TORQUE LIMIT: 12.8 kg·cm MAX\n"
                "SERVO LATENCY: < 12 ms",
                style=Style(color=COLOR_MASK_STEEL)
            )
            left_panel = Panel(
                left_text,
                title=Text("LEFT VISOR: ACTUATION", style=Style(color=COLOR_DOOM_GREEN, bold=True)),
                box=box.ROUNDED,
                border_style=COLOR_SHADOW_GREEN,
                padding=(0, 2)
            )

            right_text = Text(
                "CAPACITOR BANK: 99.4% CHARGED\n"
                "ARC SHUNT: 3.2 GW PEAK CAPACITY\n"
                "CHASSIS: TITANIUM-GOLD ALLOY\n"
                "THERMAL CORE: 34.2° C NOMINAL",
                style=Style(color=COLOR_MASK_STEEL)
            )
            right_panel = Panel(
                right_text,
                title=Text("RIGHT VISOR: METALLURGY", style=Style(color=COLOR_DOOM_GOLD, bold=True)),
                box=box.ROUNDED,
                border_style=COLOR_SHADOW_GREEN,
                padding=(0, 2)
            )
            grid.add_row(left_panel, right_panel)
            return grid

        def frame_faceplate() -> Panel:
            t = Text()
            t.append("HELMET SEAL ENGAGED  |  MARK-LXXXV FLIGHT DECK READY\n\n", style=Style(color=COLOR_DOOM_GOLD, bold=True))
            t.append("  ALL 6 SERVO MOTORS CALIBRATED AND ZEROED\n", style=Style(color=COLOR_MASK_STEEL))
            t.append("  LATVERIAN POWER HARNESS: NOMINAL\n", style=Style(color=COLOR_MASK_STEEL))
            t.append("  JARVIS NEURAL CORE: ONLINE", style=Style(color=COLOR_DOOM_GREEN, bold=True))
            return Panel(t, box=box.ROUNDED, border_style=COLOR_DOOM_GOLD, expand=False, padding=(0, 3))

        # Transient live playback
        with Live(frame_reticle(0), console=self.console, refresh_per_second=20, transient=True) as live:
            # Phase 1: Reticle collimation
            time.sleep(delay)
            live.update(frame_reticle(1))
            time.sleep(delay)
            live.update(frame_reticle(2))
            time.sleep(delay * 1.5)

            # Phase 2: Horizon pitch ladder
            live.update(frame_horizon(level=False))
            time.sleep(delay * 1.2)
            live.update(frame_horizon(level=True))
            time.sleep(delay * 1.5)

            # Phase 3: Visor diagnostics
            live.update(frame_visors())
            time.sleep(delay * 2.2)

            # Phase 4: Faceplate lock
            live.update(frame_faceplate())
            time.sleep(delay * 1.8)

    def create_audio_capsule(self, is_speaking: bool, rms_level: float) -> Panel:
        """Generates an in-place live audio level capsule."""
        if rms_level <= 1e-6:
            db = -60.0
        else:
            db = max(-60.0, min(0.0, 20.0 * math.log10(rms_level)))

        normalized = max(0.0, min(1.0, (db + 50.0) / 45.0))
        active_bars = int(round(normalized * 14))

        meter = ""
        for i in range(14):
            if i < active_bars:
                meter += "•"
            else:
                meter += "·"

        if is_speaking:
            status_text = Text("Recording ", style=Style(color=COLOR_DOOM_GOLD, bold=True))
            meter_text = Text(f" {meter} ", style=Style(color=COLOR_DOOM_GREEN, bold=True))
            db_text = Text(f"{db:4.1f} dB", style=Style(color=COLOR_MASK_STEEL))
            border = COLOR_DOOM_GOLD
        else:
            status_text = Text("Listening ", style=Style(color=COLOR_MASK_STEEL))
            meter_text = Text(f" {meter} ", style=Style(color=COLOR_SHADOW_GREEN))
            db_text = Text(f"{db:4.1f} dB", style=Style(color=COLOR_SHADOW_GREEN))
            border = COLOR_SHADOW_GREEN

        content = Text.assemble(status_text, meter_text, "  ", db_text)
        return Panel(content, box=box.ROUNDED, border_style=border, expand=False, padding=(0, 2))

    def create_transcribing_capsule(self) -> Panel:
        """Capsule shown while Whisper is transcribing."""
        content = Text("Transcribing speech...", style=Style(color=COLOR_DOOM_GOLD, italic=True))
        return Panel(content, box=box.ROUNDED, border_style=COLOR_DOOM_GREEN, expand=False, padding=(0, 2))

    def print_dialogue(self, user_text: str, response_text: str, face: str = "NEUTRAL", macro: str | None = None) -> None:
        """Prints a clean, balanced dialogue exchange with Doom palette tokens."""
        user_panel = Panel(
            Text(user_text, style=Style(color="#FFFFFF")),
            title=Text("User", style=Style(color=COLOR_MASK_STEEL)),
            title_align="left",
            box=box.ROUNDED,
            border_style=COLOR_SHADOW_GREEN,
            padding=(0, 2),
            expand=False
        )

        meta_parts = []
        if face and face != "NEUTRAL":
            meta_parts.append(face.lower())
        if macro:
            meta_parts.append(macro.lower())
        
        meta_str = f" [{', '.join(meta_parts)}]" if meta_parts else ""
        
        bot_panel = Panel(
            Text(response_text, style=Style(color=COLOR_DOOM_GOLD)),
            title=Text(f"Knox{meta_str}", style=Style(color=COLOR_DOOM_GREEN, bold=True)),
            title_align="left",
            box=box.ROUNDED,
            border_style=COLOR_DOOM_GREEN,
            padding=(0, 2),
            expand=False
        )

        self.console.print(user_panel)
        self.console.print(bot_panel)
        self.console.print()

    def print_status(self, text: str, style: str | Style | None = None) -> None:
        """Prints an understated status notice."""
        applied_style = style or Style(color=COLOR_MASK_STEEL)
        self.console.print(Text(f"  {text}", style=applied_style))
