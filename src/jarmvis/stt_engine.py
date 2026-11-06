import os
import contextlib
import logging
import numpy as np

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
    """Apple Silicon Metal accelerated Speech-to-Text using mlx-whisper."""

    def __init__(self, model_name: str = "mlx-community/whisper-tiny", use_mock: bool = False):
        self.model_name = model_name
        self.use_mock = use_mock

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        if audio_data is None or len(audio_data) == 0:
            return ""

        if self.use_mock:
            return "Jarvis, pick up that block on your left."

        # Ensure float32 normalized between -1.0 and 1.0
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        max_val = np.max(np.abs(audio_data))
        if max_val > 1.0:
            audio_data = audio_data / max_val

        try:
            import mlx_whisper
            with _suppress_output():
                result = mlx_whisper.transcribe(
                    audio_data,
                    path_or_hf_repo=self.model_name,
                    verbose=False
                )
            raw_text = result.get("text", "").strip()
            logger.info(f"MLX-Whisper transcribed: '{raw_text}'")
            return raw_text
        except Exception as e:
            logger.error(f"MLX-Whisper transcription failed: {e}")
            return ""

