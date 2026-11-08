import io
import os
import wave
import contextlib
import logging
from typing import Optional
import numpy as np
import requests

logger = logging.getLogger("jarmvis.stt")

@contextlib.contextmanager
def _suppress_output():
    """Suppresses C-level and Python-level stdout/stderr (e.g. HuggingFace / tqdm bars)."""
    try:
        null_fd = os.open(os.devnull, os.O_RDWR)
        old_stdout = os.dup(1)
        old_stderr = os.dup(2)
        os.dup2(null_fd, 1)
        os.dup2(null_fd, 2)
        try:
            yield
        finally:
            os.dup2(old_stdout, 1)
            os.dup2(old_stderr, 2)
            os.close(null_fd)
            os.close(old_stdout)
            os.close(old_stderr)
    except Exception:
        yield

class STTEngine:
    """Universal High-Performance Speech-to-Text Engine.
    
    Supports:
    1. Groq Cloud Whisper (whisper-large-v3-turbo, ~150ms ultra-low latency, cross-platform)
    2. local faster-whisper (CTranslate2 accelerated, Linux/macOS/Windows)
    3. local mlx-whisper (Apple Silicon Metal accelerated)
    4. local openai-whisper (PyTorch fallback)
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        use_mock: bool = False,
        api_key: Optional[str] = None
    ):
        self.use_mock = use_mock
        self.api_key = api_key if api_key is not None else os.environ.get("GROQ_API_KEY")
        self.model_name = model_name or os.environ.get("STT_MODEL", "whisper-large-v3-turbo")
        self._faster_whisper_model = None

    def _audio_to_wav_bytes(self, audio_data: np.ndarray, sample_rate: int = 16000) -> bytes:
        """Encodes float32 numpy audio chunk to in-memory 16-bit PCM WAV bytes."""
        clipped = np.clip(audio_data, -1.0, 1.0)
        pcm_16 = (clipped * 32767.0).astype(np.int16)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_16.tobytes())
        return buf.getvalue()

    def _transcribe_groq(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Optional[str]:
        """Calls Groq Cloud Whisper API for near-instant transcription."""
        if not self.api_key:
            return None

        try:
            wav_bytes = self._audio_to_wav_bytes(audio_data, sample_rate=sample_rate)
            model = self.model_name if "whisper" in self.model_name.lower() else "whisper-large-v3-turbo"
            files = {"file": ("utterance.wav", wav_bytes, "audio/wav")}
            data = {"model": model, "response_format": "json"}
            headers = {"Authorization": f"Bearer {self.api_key}"}

            resp = requests.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers=headers,
                files=files,
                data=data,
                timeout=6.0
            )
            if resp.status_code == 200:
                text = resp.json().get("text", "").strip()
                logger.info(f"Groq Whisper transcribed: '{text}'")
                return text
            else:
                logger.warning(f"Groq Whisper HTTP {resp.status_code}: {resp.text}")
                return None
        except Exception as e:
            logger.warning(f"Groq Whisper request error: {e}")
            return None

    def _transcribe_faster_whisper(self, audio_data: np.ndarray) -> Optional[str]:
        """Runs local faster-whisper (CTranslate2) model with automatic CPU/GPU fallback."""
        try:
            import faster_whisper
            if self._faster_whisper_model is None:
                local_model_name = os.environ.get("LOCAL_WHISPER_MODEL", "base.en")
                device = os.environ.get("WHISPER_DEVICE", "cpu")
                compute_type = "int8" if device == "cpu" else "default"
                try:
                    self._faster_whisper_model = faster_whisper.WhisperModel(
                        local_model_name,
                        device=device,
                        compute_type=compute_type
                    )
                except Exception:
                    self._faster_whisper_model = faster_whisper.WhisperModel(
                        local_model_name,
                        device="cpu",
                        compute_type="int8"
                    )
            with _suppress_output():
                segments, _ = self._faster_whisper_model.transcribe(audio_data, beam_size=1)
                text = " ".join(s.text.strip() for s in segments).strip()
            logger.info(f"faster-whisper transcribed: '{text}'")
            return text
        except Exception as e:
            logger.debug(f"faster-whisper unavailable or failed: {e}")
            return None

    def _transcribe_mlx(self, audio_data: np.ndarray) -> Optional[str]:
        """Runs Apple Silicon Metal mlx-whisper."""
        try:
            import mlx_whisper
            with _suppress_output():
                result = mlx_whisper.transcribe(
                    audio_data,
                    path_or_hf_repo=self.model_name or "mlx-community/whisper-base-mlx",
                    verbose=False
                )
            text = result.get("text", "").strip()
            logger.info(f"mlx-whisper transcribed: '{text}'")
            return text
        except Exception as e:
            logger.debug(f"mlx-whisper unavailable or failed: {e}")
            return None

    def _transcribe_openai_whisper(self, audio_data: np.ndarray) -> Optional[str]:
        """Runs standard OpenAI whisper."""
        try:
            import whisper
            with _suppress_output():
                model = whisper.load_model("base.en")
                result = model.transcribe(audio_data)
            text = result.get("text", "").strip()
            logger.info(f"openai-whisper transcribed: '{text}'")
            return text
        except Exception as e:
            logger.debug(f"openai-whisper unavailable or failed: {e}")
            return None

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribes audio chunk to text using the highest-priority available backend."""
        if audio_data is None or len(audio_data) == 0:
            return ""

        if self.use_mock:
            return "Knox, pick up that block on your left."

        # Ensure float32 normalized between -1.0 and 1.0
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        max_val = float(np.max(np.abs(audio_data)))
        if max_val > 1.0:
            audio_data = audio_data / max_val

        # 1. Cloud Groq Whisper (ultra-low latency, cross-platform)
        if self.api_key:
            groq_result = self._transcribe_groq(audio_data, sample_rate=sample_rate)
            if groq_result is not None:
                return groq_result

        # 2. Local faster-whisper (Linux / Mac / Windows CTranslate2)
        fw_result = self._transcribe_faster_whisper(audio_data)
        if fw_result is not None:
            return fw_result

        # 3. Local mlx-whisper (Apple Silicon Metal)
        mlx_result = self._transcribe_mlx(audio_data)
        if mlx_result is not None:
            return mlx_result

        # 4. Standard PyTorch whisper fallback
        whisper_result = self._transcribe_openai_whisper(audio_data)
        if whisper_result is not None:
            return whisper_result

        logger.error("No Speech-to-Text backend succeeded (Groq API, faster-whisper, mlx-whisper, openai-whisper all unavailable).")
        return ""
