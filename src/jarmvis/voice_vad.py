from collections import deque
import logging
from typing import Callable, Optional
import numpy as np

logger = logging.getLogger("jarmvis.vad")


class VoiceActivityDetector:
    def __init__(
        self,
        on_speech_start: Optional[Callable[[], None]] = None,
        on_speech_end: Optional[Callable[[np.ndarray], None]] = None,
        sample_rate: int = 16000,
        chunk_size: int = 512,
        energy_threshold: float = 0.0005,
        silence_timeout_chunks: int = 22,
        pre_buffer_chunks: int = 0,
    ):
        self.on_speech_start = on_speech_start
        self.on_speech_end = on_speech_end
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.energy_threshold = energy_threshold
        self.silence_timeout_chunks = silence_timeout_chunks
        self.pre_buffer_chunks = pre_buffer_chunks

        self.is_speaking = False
        self.silence_count = 0
        self.speech_buffer: list[np.ndarray] = []
        self._pre_buffer = deque(maxlen=max(1, pre_buffer_chunks)) if pre_buffer_chunks > 0 else None
        self._stream = None

    def calibrate_noise_floor(self, duration: float = 0.4, device: Optional[int | str] = None) -> float:
        """Sample ambient noise for calibration and auto-set threshold."""
        try:
            import sounddevice as sd
            frames = int(duration * self.sample_rate)
            rec = sd.rec(frames, samplerate=self.sample_rate, channels=1, dtype="float32", device=device)
            sd.wait()
            ambient_energy = float(np.mean(rec ** 2))
            # Set threshold safely above room ambient noise floor (4x noise floor, clamped [0.0002, 0.01])
            self.energy_threshold = max(0.0002, min(0.01, ambient_energy * 4.0))
            logger.info(f"Calibrated noise floor: {ambient_energy:.8f}, threshold set to {self.energy_threshold:.6f}")
            return self.energy_threshold
        except Exception as e:
            logger.warning(f"Could not calibrate ambient noise: {e}. Using fallback 0.0005")
            self.energy_threshold = 0.0005
            return self.energy_threshold

    def process_audio_chunk(self, chunk: np.ndarray) -> bool:
        if len(chunk) == 0:
            return self.is_speaking

        if chunk.dtype != np.float32:
            if np.issubdtype(chunk.dtype, np.integer):
                chunk = chunk.astype(np.float32) / 32768.0
            else:
                chunk = chunk.astype(np.float32)

        if chunk.ndim > 1:
            chunk = np.mean(chunk, axis=-1)

        energy = float(np.mean(chunk ** 2))
        is_chunk_speech = energy > self.energy_threshold

        if is_chunk_speech:
            if not self.is_speaking:
                self.is_speaking = True
                self.speech_buffer = []
                if self._pre_buffer:
                    self.speech_buffer.extend(list(self._pre_buffer))
                logger.info("Speech start detected!")
                if self.on_speech_start:
                    self.on_speech_start()
            self.speech_buffer.append(chunk)
            self.silence_count = 0
        elif self.is_speaking:
            self.speech_buffer.append(chunk)
            self.silence_count += 1
            if self.silence_count >= self.silence_timeout_chunks:
                self.is_speaking = False
                logger.info("Speech end detected.")
                if self.on_speech_end and self.speech_buffer:
                    full_utterance = np.concatenate(self.speech_buffer)
                    self.on_speech_end(full_utterance)
                self.speech_buffer = []
                self.silence_count = 0
        elif self._pre_buffer is not None:
            self._pre_buffer.append(chunk)

        return self.is_speaking

    def start_listening_stream(self, device: Optional[int | str] = None) -> bool:
        if self._stream is not None:
            return True
        try:
            import sounddevice as sd

            def audio_callback(indata, frames, time_info, status):
                if status:
                    logger.debug(f"Audio stream status: {status}")
                chunk = indata[:, 0].copy() if indata.ndim > 1 else indata.flatten().copy()
                self.process_audio_chunk(chunk)

            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                channels=1,
                dtype="float32",
                callback=audio_callback,
                device=device,
            )
            self._stream.start()
            logger.info("Started audio input stream via sounddevice.")
            return True
        except Exception as e:
            logger.warning(f"Could not start sounddevice InputStream: {e}")
            self._stream = None
            return False

    def stop_listening_stream(self) -> None:
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                logger.warning(f"Error stopping stream: {e}")
            finally:
                self._stream = None
                logger.info("Stopped audio input stream.")
