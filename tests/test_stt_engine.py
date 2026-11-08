import numpy as np
import io
import wave
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

def test_stt_groq_whisper_transcription(monkeypatch):
    dummy_audio = np.ones(8000, dtype=np.float32) * 0.1
    stt = STTEngine(use_mock=False, api_key="test_groq_key")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"text": "Knox, raise the arm"}

    with patch("requests.post", return_value=mock_resp) as mock_post:
        result = stt.transcribe(dummy_audio)
        assert mock_post.called
        assert result == "Knox, raise the arm"

def test_stt_faster_whisper_fallback():
    dummy_audio = np.ones(8000, dtype=np.float32) * 0.1
    # STT without groq key should fall back to local faster-whisper or mlx
    stt = STTEngine(use_mock=False, api_key="")

    mock_segment = MagicMock()
    mock_segment.text = "Hello from faster whisper"
    mock_model = MagicMock()
    mock_model.transcribe.return_value = ([mock_segment], None)

    with patch.dict("sys.modules", {"faster_whisper": MagicMock(WhisperModel=MagicMock(return_value=mock_model))}):
        result = stt.transcribe(dummy_audio)
        assert "Hello from faster whisper" in result

def test_stt_mlx_transcription_invocation():
    stt = STTEngine(use_mock=False, api_key="")
    dummy_audio = np.ones(8000, dtype=np.float32) * 0.1

    mock_mlx = MagicMock()
    mock_mlx.transcribe.return_value = {"text": "Hello Jarvis"}
    with patch.dict("sys.modules", {"mlx_whisper": mock_mlx, "faster_whisper": None}):
        result = stt.transcribe(dummy_audio)
        assert result == "Hello Jarvis"


