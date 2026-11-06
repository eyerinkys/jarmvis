import asyncio
import logging
import os
import re
import tempfile
from typing import Callable

logger = logging.getLogger("jarmvis.tts")


def _clean_tts_text(text: str) -> str:
    """Normalize text and quotes to prevent Azure SSML parser quirks."""
    # Convert dotted acronyms like J.A.R.V.I.S. or Knox
    cleaned = re.sub(r'\bJ\.A\.R\.V\.I\.S\.?\b', 'JARVIS', text, flags=re.IGNORECASE)
    # Convert curly / smart quotes to standard ASCII
    cleaned = cleaned.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    # Remove emojis or characters that can confuse Edge TTS
    cleaned = re.sub(r'[\U00010000-\U0010ffff]|[\u2600-\u27BF]', '', cleaned)
    return cleaned.strip()


EMOTION_MODULATION: dict[str, dict[str, str]] = {
    "ANGRY": {"rate": "+16%", "pitch": "+10Hz"},
    "EXCITED": {"rate": "+18%", "pitch": "+12Hz"},
    "CONFIDENT": {"rate": "+8%", "pitch": "+2Hz"},
    "SARCASTIC": {"rate": "+2%", "pitch": "-5Hz"},
    "SAD": {"rate": "-12%", "pitch": "-10Hz"},
    "ASHAMED": {"rate": "-15%", "pitch": "-10Hz"},
    "CURIOUS": {"rate": "+5%", "pitch": "+8Hz"},
    "HAPPY": {"rate": "+12%", "pitch": "+6Hz"},
    "NEUTRAL": {"rate": "+0%", "pitch": "+0Hz"},
}


class TTSEngine:
    def __init__(
        self,
        voice: str = "en-US-ChristopherNeural",
        rate: str = "+0%",
        volume: str = "+0%",
        pitch: str = "+0Hz",
        use_mock: bool = False,
        elevenlabs_api_key: str | None = None,
        elevenlabs_voice_id: str | None = None,
    ):
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.pitch = pitch
        self.use_mock = use_mock
        self.elevenlabs_api_key = elevenlabs_api_key or os.environ.get("ELEVENLABS_API_KEY")
        self.elevenlabs_voice_id = elevenlabs_voice_id or os.environ.get("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")

    def _synthesize_elevenlabs(self, text: str, output_path: str, emotion: str | None = None) -> bool:
        api_key = self.elevenlabs_api_key or os.environ.get("ELEVENLABS_API_KEY")
        if not api_key:
            return False

        voice_id = self.elevenlabs_voice_id or os.environ.get("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")
        model_id = os.environ.get("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")

        # Lower stability gives expressive human inflection, breath, and realism
        stability = 0.30
        style = 0.50
        emo_upper = str(emotion).upper() if emotion else ""
        if emo_upper in ["ANGRY", "EXCITED", "SARCASTIC"]:
            stability = 0.20
            style = 0.65
        elif emo_upper in ["SAD", "ASHAMED"]:
            stability = 0.45
            style = 0.30

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": 0.80,
                "style": style,
                "use_speaker_boost": True
            }
        }
        for attempt in range(2):
            try:
                import requests
                res = requests.post(url, headers=headers, json=payload, timeout=8.0)
                if res.status_code == 200 and len(res.content) > 100:
                    with open(output_path, "wb") as f:
                        f.write(res.content)
                    logger.info(f"Synthesized with ElevenLabs (voice={voice_id}, model={model_id})")
                    return True
                else:
                    logger.warning(f"ElevenLabs TTS returned HTTP {res.status_code}: {res.text[:120]}")
                    return False
            except Exception as e:
                if attempt == 0:
                    import time
                    time.sleep(0.5)
                    continue
                logger.warning(f"ElevenLabs TTS request failed: {e}")
                return False
        return False

    async def _synthesize(
        self,
        text: str,
        output_path: str,
        rate: str | None = None,
        pitch: str | None = None
    ) -> None:
        import edge_tts
        cleaned = _clean_tts_text(text)
        use_rate = rate or self.rate
        use_pitch = pitch or self.pitch
        for attempt in range(2):
            try:
                communicate = edge_tts.Communicate(
                    text=cleaned,
                    voice=self.voice,
                    rate=use_rate,
                    volume=self.volume,
                    pitch=use_pitch
                )
                await communicate.save(output_path)
                return
            except Exception as e:
                if attempt == 0:
                    await asyncio.sleep(0.25)
                    continue
                raise

    def synthesize_to_file(self, text: str, emotion: str | None = None) -> str | None:
        """Synthesizes speech to an audio file and returns its path without blocking playback."""
        cleaned_text = text.strip()
        if not cleaned_text:
            return None

        if self.use_mock:
            # Generate a synthetic modulated WAV file for offline testing/dry-run
            import wave
            import numpy as np
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp_path = tmp.name
            tmp.close()
            sr = 16000
            words = len(cleaned_text.split())
            duration = max(0.8, min(8.0, words * 0.35))
            t = np.linspace(0, duration, int(sr * duration), endpoint=False)
            # Syllabic amplitude modulated waveform
            audio = (0.4 * np.sin(2 * np.pi * 200 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 4.0 * t)) * 32767).astype(np.int16)
            with wave.open(tmp_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sr)
                wf.writeframes(audio.tobytes())
            return tmp_path

        mod = EMOTION_MODULATION.get(str(emotion).upper(), {}) if emotion else {}
        mod_rate = mod.get("rate", self.rate)
        mod_pitch = mod.get("pitch", self.pitch)

        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp_path = tmp.name
        tmp.close()

        try:
            used_eleven = self._synthesize_elevenlabs(cleaned_text, tmp_path, emotion=emotion)
            if not used_eleven:
                asyncio.run(self._synthesize(cleaned_text, tmp_path, rate=mod_rate, pitch=mod_pitch))
            return tmp_path
        except Exception as e:
            logger.warning(f"Synthesis to file failed: {e}")
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            return None

    def speak(
        self,
        text: str,
        emotion: str | None = None,
        on_playback_start: Callable[[], None] | None = None,
        on_playback_end: Callable[[], None] | None = None
    ) -> None:
        cleaned_text = text.strip()
        if not cleaned_text:
            return

        # Modulate rate & pitch based on emotion for expressive tonation
        mod = EMOTION_MODULATION.get(str(emotion).upper(), {}) if emotion else {}
        mod_rate = mod.get("rate", self.rate)
        mod_pitch = mod.get("pitch", self.pitch)

        logger.info(f"Speaking: '{cleaned_text}' (emotion={emotion}, rate={mod_rate}, pitch={mod_pitch})")
        if on_playback_start:
            on_playback_start()

        if self.use_mock:
            print(f"[tts:mock] voice={self.voice} text=\"{cleaned_text}\"")
            if on_playback_end:
                on_playback_end()
            return

        tmp_path = self.synthesize_to_file(cleaned_text, emotion=emotion)
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.system(f"afplay '{tmp_path}' > /dev/null 2>&1")
            else:
                raise RuntimeError("Audio synthesis returned no file")
        except Exception as e:
            logger.warning(f"Audio playback failed: {e}. Falling back to system voice.")
            print(f"[tts:fallback] text=\"{cleaned_text}\"")
            try:
                safe_text = _clean_tts_text(cleaned_text).replace('"', '\\"').replace("'", "\\'")
                os.system(f'say -v Samantha "{safe_text}" > /dev/null 2>&1 || say "{safe_text}" > /dev/null 2>&1')
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
