import math
from typing import Any
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.style import Style
from rich import box

# Custom Doctor Doom Palette Tokens
COLOR_DOOM_GREEN   = "#477A43"
COLOR_SHADOW_GREEN = "#24452D"
COLOR_DOOM_GOLD    = "#D6AD35"
COLOR_MASK_STEEL   = "#85898A"

console = Console()

class TerminalUI:
    """Minimalist, zero-emoji, hairline-bordered terminal interface styled with Doctor Doom palette."""

    def __init__(self, console_instance: Console | None = None):
        self.console = console_instance or console

    def print_banner(self) -> None:
        """Prints a clean, quiet header banner."""
        title = Text("JARMVIS", style=Style(color=COLOR_DOOM_GOLD, bold=True))
        subtitle = Text("  robotic desk intelligence  ", style=Style(color=COLOR_MASK_STEEL))
        header = Text.assemble(title, subtitle)
        self.console.print()
        self.console.print(Panel(
            header,
            box=box.ROUNDED,
            border_style=COLOR_SHADOW_GREEN,
            expand=False,
            padding=(0, 2)
        ))
        self.console.print()

    def create_audio_capsule(self, is_speaking: bool, rms_level: float) -> Panel:
        """Generates an in-place live audio level capsule."""
        # Convert RMS to intuitive dB scale (-60 dB to 0 dB)
        if rms_level <= 1e-6:
            db = -60.0
        else:
            db = max(-60.0, min(0.0, 20.0 * math.log10(rms_level)))

        # 14-bar acoustic dot meter
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
        # User message panel
        user_panel = Panel(
            Text(user_text, style=Style(color="#FFFFFF")),
            title=Text("User", style=Style(color=COLOR_MASK_STEEL)),
            title_align="left",
            box=box.ROUNDED,
            border_style=COLOR_SHADOW_GREEN,
            padding=(0, 2),
            expand=False
        )

        # Meta tags for face and macro
        meta_parts = []
        if face and face != "NEUTRAL":
            meta_parts.append(face.lower())
        if macro:
            meta_parts.append(macro.lower())
        
        meta_str = f" [{', '.join(meta_parts)}]" if meta_parts else ""
        
        # Knox response panel
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
