import logging
import os
import shutil
import subprocess
import tempfile
import wave
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger("jarmvis.audio_analyzer")


@dataclass
class AudioFeatures:
    rms_envelope: np.ndarray  # Normalized [0.0, 1.0] array at given fps
    beat_onsets: np.ndarray   # Transient onset spike intensities [0.0, 1.0]
    duration_sec: float
    fps: int = 50


class AudioAnalyzer:
    def __init__(self, fps: int = 50):
        self.fps = fps

    def extract_features_from_array(self, samples: np.ndarray, sample_rate: int = 16000) -> AudioFeatures:
        """Extracts 50Hz RMS intensity envelope and onset beats from raw audio array."""
        if samples is None or len(samples) == 0:
            return AudioFeatures(
                rms_envelope=np.array([], dtype=np.float32),
                beat_onsets=np.array([], dtype=np.float32),
                duration_sec=0.0,
                fps=self.fps,
            )

        # Convert to mono float32 normalized to [-1.0, 1.0]
        audio = np.asarray(samples, dtype=np.float32)
        if audio.ndim > 1:
            audio = np.mean(audio, axis=1)

        # Normalize int16 or int32 if needed
        max_val = np.max(np.abs(audio))
        if max_val > 1.0:
            audio = audio / max(max_val, 32768.0)

        duration_sec = len(audio) / float(sample_rate)
        total_frames = int(round(duration_sec * self.fps))
        if total_frames <= 0:
            return AudioFeatures(
                rms_envelope=np.array([], dtype=np.float32),
                beat_onsets=np.array([], dtype=np.float32),
                duration_sec=duration_sec,
                fps=self.fps,
            )

        hop_size = float(sample_rate) / self.fps
        raw_rms = np.zeros(total_frames, dtype=np.float32)

        for i in range(total_frames):
            start = int(round(i * hop_size))
            end = int(round((i + 1) * hop_size))
            chunk = audio[start:end]
            if len(chunk) > 0:
                raw_rms[i] = float(np.sqrt(np.mean(chunk**2)))

        # Normalize RMS envelope with floor noise removal
        peak = np.max(raw_rms) if len(raw_rms) > 0 else 0.0
        if peak > 0.001:
            normalized_rms = raw_rms / peak
        else:
            normalized_rms = raw_rms

        # Attack-decay smoothing filter
        smoothed_rms = np.zeros_like(normalized_rms)
        attack_rate = 0.75
        decay_rate = 0.35
        curr = 0.0
        for i in range(len(normalized_rms)):
            target = normalized_rms[i]
            if target > curr:
                curr = attack_rate * target + (1.0 - attack_rate) * curr
            else:
                curr = decay_rate * target + (1.0 - decay_rate) * curr
            smoothed_rms[i] = curr

        # Compute onsets via positive first-difference of RMS
        diff = np.diff(smoothed_rms, prepend=smoothed_rms[0])
        rectified_diff = np.maximum(0.0, diff)
        diff_max = np.max(rectified_diff) if len(rectified_diff) > 0 else 0.0
        if diff_max > 0.02:
            beat_onsets = rectified_diff / diff_max
            # Suppress minor noise fluctuations below 0.15 threshold
            beat_onsets[beat_onsets < 0.15] = 0.0
        else:
            beat_onsets = np.zeros_like(smoothed_rms)

        return AudioFeatures(
            rms_envelope=smoothed_rms,
            beat_onsets=beat_onsets,
            duration_sec=duration_sec,
            fps=self.fps,
        )

    def extract_features_from_file(self, file_path: str) -> AudioFeatures:
        """Extracts features from an audio file (.wav, .mp3, etc.) cross-platform."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        # 1. If standard WAV, attempt fast standard library wave reading
        if file_path.lower().endswith(".wav"):
            try:
                with wave.open(file_path, "rb") as wf:
                    channels = wf.getnchannels()
                    sample_width = wf.getsampwidth()
                    rate = wf.getframerate()
                    num_frames = wf.getnframes()
                    raw_bytes = wf.readframes(num_frames)

                dtype_map = {1: np.uint8, 2: np.int16, 4: np.int32}
                dtype = dtype_map.get(sample_width, np.int16)
                data = np.frombuffer(raw_bytes, dtype=dtype)
                if channels > 1:
                    data = data.reshape(-1, channels)
                return self.extract_features_from_array(data, sample_rate=rate)
            except Exception as e:
                logger.debug(f"Direct wave reading failed ({e}). Falling back to multi-format decoders.")

        # 2. Universal decoding via PyAV (supports MP3, AAC, FLAC, OGG, WAV in-memory)
        try:
            import av
            container = av.open(file_path)
            if container.streams.audio:
                stream = container.streams.audio[0]
                resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)
                frames = []
                for frame in container.decode(stream):
                    for r in resampler.resample(frame):
                        frames.append(r.to_ndarray())
                container.close()
                if frames:
                    audio_data = np.concatenate(frames, axis=1).reshape(-1)
                    return self.extract_features_from_array(audio_data, sample_rate=16000)
            else:
                container.close()
        except Exception as e:
            logger.debug(f"PyAV audio decoding failed: {e}. Trying CLI converter fallback.")

        # 3. CLI conversion fallback (ffmpeg on Linux/Windows/macOS or afconvert on macOS)
        tmp_wav = None
        try:
            if shutil.which("ffmpeg"):
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp_wav = tmp.name
                cmd = ["ffmpeg", "-y", "-i", file_path, "-ac", "1", "-ar", "16000", "-f", "wav", tmp_wav]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                with wave.open(tmp_wav, "rb") as wf:
                    rate = wf.getframerate()
                    num_frames = wf.getnframes()
                    raw_bytes = wf.readframes(num_frames)
                data = np.frombuffer(raw_bytes, dtype=np.int16)
                return self.extract_features_from_array(data, sample_rate=rate)
            elif shutil.which("afconvert"):
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp_wav = tmp.name
                cmd = ["afconvert", "-f", "WAVE", "-d", "LEI16", "-c", "1", "-r", "16000", file_path, tmp_wav]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                with wave.open(tmp_wav, "rb") as wf:
                    rate = wf.getframerate()
                    num_frames = wf.getnframes()
                    raw_bytes = wf.readframes(num_frames)
                data = np.frombuffer(raw_bytes, dtype=np.int16)
                return self.extract_features_from_array(data, sample_rate=rate)
        except Exception as e:
            logger.warning(f"CLI audio converter fallback failed: {e}")
        finally:
            if tmp_wav and os.path.exists(tmp_wav):
                try:
                    os.remove(tmp_wav)
                except OSError:
                    pass

        # 4. Graceful fallback on complete failure to decode (never crash caller thread)
        logger.warning(f"Could not decode audio from {file_path}. Returning empty audio features.")
        return AudioFeatures(
            rms_envelope=np.array([], dtype=np.float32),
            beat_onsets=np.array([], dtype=np.float32),
            duration_sec=0.0,
            fps=self.fps,
        )

