import asyncio
import logging
import os
import re
import tempfile
from typing import Callable

logger = logging.getLogger("jarmvis.tts")


def _clean_tts_text(text: str) -> str:
    """Normalize text to prevent Azure SSML parser quirks with acronym periods."""
    # Convert dotted acronyms like J.A.R.V.I.S. -> JARVIS so SSML doesn't split them into 1-letter empty sentences
    cleaned = re.sub(r'\bJ\.A\.R\.V\.I\.S\.?\b', 'JARVIS', text, flags=re.IGNORECASE)
    # Remove emojis or characters that can confuse Edge TTS
    cleaned = re.sub(r'[\U00010000-\U0010ffff]|[\u2600-\u27BF]', '', cleaned)
    return cleaned.strip()


class TTSEngine:
    def __init__(
        self,
        voice: str = "en-GB-RyanNeural",
        rate: str = "+0%",
        volume: str = "+0%",
        pitch: str = "+0Hz",
        use_mock: bool = False
    ):
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.pitch = pitch
        self.use_mock = use_mock

    async def _synthesize(self, text: str, output_path: str) -> None:
        import edge_tts
        cleaned = _clean_tts_text(text)
        for attempt in range(2):
            try:
                communicate = edge_tts.Communicate(
                    text=cleaned,
                    voice=self.voice,
                    rate=self.rate,
                    volume=self.volume,
                    pitch=self.pitch
                )
                await communicate.save(output_path)
                return
            except Exception as e:
                if attempt == 0:
                    await asyncio.sleep(0.25)
                    continue
                raise

    def speak(
        self,
        text: str,
        on_playback_start: Callable[[], None] | None = None,
        on_playback_end: Callable[[], None] | None = None
    ) -> None:
        cleaned_text = text.strip()
        if not cleaned_text:
            return

        logger.info(f"Speaking: '{cleaned_text}'")
        if on_playback_start:
            on_playback_start()

        if self.use_mock:
            print(f"[tts:mock] voice={self.voice} text=\"{cleaned_text}\"")
            if on_playback_end:
                on_playback_end()
            return

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name

            # Run asynchronous edge-tts synthesis
            asyncio.run(self._synthesize(cleaned_text, tmp_path))

            # Play audio using macOS native afplay (zero external dependencies)
            os.system(f"afplay '{tmp_path}' > /dev/null 2>&1")
        except Exception as e:
            logger.warning(f"Cloud TTS synthesis failed: {e}. Falling back to system voice.")
            print(f"[tts:fallback] text=\"{cleaned_text}\"")
            try:
                safe_text = _clean_tts_text(cleaned_text).replace('"', '\\"').replace("'", "\\'")
                os.system(f'say -v Daniel "{safe_text}" > /dev/null 2>&1 || say "{safe_text}" > /dev/null 2>&1')
            except Exception:
                pass
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            if on_playback_end:
                on_playback_end()
