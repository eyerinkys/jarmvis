import numpy as np
import pytest
from unittest.mock import MagicMock, patch
from jarmvis.voice_vad import VoiceActivityDetector

def test_energy_fallback_vad_triggers():
    on_start = MagicMock()
    on_end = MagicMock()
    vad = VoiceActivityDetector(on_speech_start=on_start, on_speech_end=on_end, energy_threshold=0.05, silence_timeout_chunks=3)
    
    # Silence: values near 0
    silence = np.zeros(512, dtype=np.float32)
    vad.process_audio_chunk(silence)
    assert not on_start.called

    # Loud speech chunk
    loud_speech = np.ones(512, dtype=np.float32) * 0.3
    vad.process_audio_chunk(loud_speech)
    assert on_start.called
    assert vad.is_speaking is True

    # Trailing silence triggers speech end
    vad.process_audio_chunk(silence)
    vad.process_audio_chunk(silence)
    vad.process_audio_chunk(silence)
    assert on_end.called
    assert vad.is_speaking is False
    recorded_audio = on_end.call_args[0][0]
    assert isinstance(recorded_audio, np.ndarray)
    assert len(recorded_audio) == 512 * 4

def test_stream_controls():
    vad = VoiceActivityDetector()
    # Mocking or testing start/stop stream methods
    assert hasattr(vad, "start_listening_stream")
    assert hasattr(vad, "stop_listening_stream")

def test_int16_conversion_and_empty_chunks():
    on_start = MagicMock()
    vad = VoiceActivityDetector(on_speech_start=on_start, energy_threshold=0.05)
    
    # Empty chunk
    empty = np.array([], dtype=np.float32)
    vad.process_audio_chunk(empty)
    assert not on_start.called

    # int16 loud speech (0.3 of 32767 ~= 10000)
    int16_speech = np.ones(512, dtype=np.int16) * 10000
    vad.process_audio_chunk(int16_speech)
    assert on_start.called
    assert vad.is_speaking is True

def test_multichannel_audio_chunk():
    vad = VoiceActivityDetector(energy_threshold=0.05)
    # 2D stereo array
    stereo_silence = np.zeros((512, 2), dtype=np.float32)
    assert vad.process_audio_chunk(stereo_silence) is False

def test_start_stop_listening_stream_lifecycle():
    with patch("sounddevice.InputStream") as mock_stream_cls:
        mock_instance = MagicMock()
        mock_stream_cls.return_value = mock_instance

        vad = VoiceActivityDetector()
        started = vad.start_listening_stream()
        assert started is True
        mock_instance.start.assert_called_once()

        # Calling again should reuse stream
        assert vad.start_listening_stream() is True

        vad.stop_listening_stream()
        mock_instance.stop.assert_called_once()
        mock_instance.close.assert_called_once()
        assert vad._stream is None

def test_start_listening_stream_failure_handling():
    with patch("sounddevice.InputStream", side_effect=RuntimeError("No audio device")):
        vad = VoiceActivityDetector()
        started = vad.start_listening_stream()
        assert started is False
        assert vad._stream is None
