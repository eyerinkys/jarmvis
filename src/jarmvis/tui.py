import math
from typing import Any
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()

class TerminalUI:
    """Minimalist, zero-emoji, hairline-bordered terminal interface."""

    def __init__(self, console_instance: Console | None = None):
        self.console = console_instance or console

    def print_banner(self) -> None:
        """Prints a clean, quiet header banner."""
        title = Text("JARMVIS", style="bold cyan")
        subtitle = Text("  robotic desk intelligence  ", style="dim white")
        header = Text.assemble(title, subtitle)
        self.console.print()
        self.console.print(Panel(
            header,
            box=box.ROUNDED,
            border_style="dim bright_black",
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

        # 16-bar acoustic dot meter
        normalized = max(0.0, min(1.0, (db + 50.0) / 45.0))
        active_bars = int(round(normalized * 14))

        meter = ""
        for i in range(14):
            if i < active_bars:
                meter += "•"
            else:
                meter += "·"

        if is_speaking:
            status_text = Text("Recording ", style="bold cyan")
            meter_text = Text(f" {meter} ", style="bold white")
            db_text = Text(f"{db:4.1f} dB", style="dim cyan")
            border = "cyan"
        else:
            status_text = Text("Listening ", style="dim white")
            meter_text = Text(f" {meter} ", style="dim bright_black")
            db_text = Text(f"{db:4.1f} dB", style="dim bright_black")
            border = "dim bright_black"

        content = Text.assemble(status_text, meter_text, "  ", db_text)
        return Panel(content, box=box.ROUNDED, border_style=border, expand=False, padding=(0, 2))

    def create_transcribing_capsule(self) -> Panel:
        """Capsule shown while Whisper is transcribing."""
        content = Text("Transcribing speech...", style="italic dim cyan")
        return Panel(content, box=box.ROUNDED, border_style="dim cyan", expand=False, padding=(0, 2))

    def print_dialogue(self, user_text: str, response_text: str, face: str = "NEUTRAL", macro: str | None = None) -> None:
        """Prints a clean, balanced dialogue exchange without noisy clutter."""
        # User message
        user_panel = Panel(
            Text(user_text, style="white"),
            title="User",
            title_align="left",
            box=box.ROUNDED,
            border_style="dim bright_black",
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
        
        # Assistant response
        bot_panel = Panel(
            Text(response_text, style="cyan"),
            title=f"Knox{meta_str}",
            title_align="left",
            box=box.ROUNDED,
            border_style="cyan",
            padding=(0, 2),
            expand=False
        )

        self.console.print(user_panel)
        self.console.print(bot_panel)
        self.console.print()

    def print_status(self, text: str, style: str = "dim white") -> None:
        """Prints an understated status notice."""
        self.console.print(Text(f"  {text}", style=style))
