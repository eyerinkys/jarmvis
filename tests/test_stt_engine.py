import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from jarmvis.stt_engine import STTEngine

def test_stt_mock_transcribe():
    stt = STTEngine(use_mock=True)
    audio = np.zeros(16000, dtype=np.float32)
    text = stt.transcribe(audio)
    assert isinstance(text, str)
    assert len(text) > 0

def test_stt_empty_audio():
    stt = STTEngine(use_mock=True)
    empty = np.array([], dtype=np.float32)
    assert stt.transcribe(empty) == ""

def test_stt_mlx_transcription_invocation():
    stt = STTEngine(use_mock=False)
    dummy_audio = np.ones(8000, dtype=np.float32) * 0.1

    with patch("mlx_whisper.transcribe", return_value={"text": "Hello Jarvis"}) as mock_mlx:
        result = stt.transcribe(dummy_audio)
        assert mock_mlx.called
        assert result == "Hello Jarvis"

