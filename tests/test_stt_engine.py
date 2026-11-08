import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from jarmvis.stt_engine import STTEngine, SystemChecker

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

def test_system_checker_macos():
    with patch("platform.system", return_value="Darwin"):
        assert SystemChecker.is_macos() is True
        assert SystemChecker.get_preferred_backend() == "mlx"

def test_system_checker_non_macos():
    with patch("platform.system", return_value="Linux"):
        assert SystemChecker.is_macos() is False
        assert SystemChecker.get_preferred_backend() == "faster-whisper"

def test_stt_non_macos_uses_faster_whisper_and_ignores_groq_api_key():
    """Verifies that non-macOS systems use local faster-whisper and DO NOT call Groq even if api_key exists."""
    dummy_audio = np.ones(8000, dtype=np.float32) * 0.1
    mock_checker = MagicMock(is_macos=MagicMock(return_value=False))
    stt = STTEngine(use_mock=False, api_key="test_groq_key", system_checker=mock_checker)

    mock_segment = MagicMock()
    mock_segment.text = "Local faster-whisper transcription without Groq"
    mock_model = MagicMock()
    mock_model.transcribe.return_value = ([mock_segment], None)

    with patch("requests.post") as mock_post:
        with patch.dict("sys.modules", {"faster_whisper": MagicMock(WhisperModel=MagicMock(return_value=mock_model))}):
            result = stt.transcribe(dummy_audio)
            assert result == "Local faster-whisper transcription without Groq"
            # Crucial: Groq API MUST NOT be called!
            assert not mock_post.called

def test_stt_macos_prioritizes_mlx():
    """Verifies that macOS systems prioritize local mlx_whisper."""
    dummy_audio = np.ones(8000, dtype=np.float32) * 0.1
    mock_checker = MagicMock(is_macos=MagicMock(return_value=True))
    stt = STTEngine(use_mock=False, api_key="test_groq_key", system_checker=mock_checker)

    mock_mlx = MagicMock()
    mock_mlx.transcribe.return_value = {"text": "Apple Silicon MLX transcription"}

    with patch("requests.post") as mock_post:
        with patch.dict("sys.modules", {"mlx_whisper": mock_mlx}):
            result = stt.transcribe(dummy_audio)
            assert result == "Apple Silicon MLX transcription"
            assert not mock_post.called

def test_stt_macos_falls_back_to_faster_whisper_if_mlx_unavailable():
    """Verifies that macOS falls back to faster-whisper if mlx-whisper fails."""
    dummy_audio = np.ones(8000, dtype=np.float32) * 0.1
    mock_checker = MagicMock(is_macos=MagicMock(return_value=True))
    stt = STTEngine(use_mock=False, api_key="test_groq_key", system_checker=mock_checker)

    mock_segment = MagicMock()
    mock_segment.text = "Mac fallback to faster-whisper"
    mock_model = MagicMock()
    mock_model.transcribe.return_value = ([mock_segment], None)

    with patch("requests.post") as mock_post:
        with patch.dict("sys.modules", {
            "mlx_whisper": None,
            "faster_whisper": MagicMock(WhisperModel=MagicMock(return_value=mock_model))
        }):
            result = stt.transcribe(dummy_audio)
            assert result == "Mac fallback to faster-whisper"
            assert not mock_post.called

def test_stt_cloud_groq_when_explicitly_allowed():
    """Verifies that Groq is only used when allow_cloud_fallback=True and local engines fail."""
    dummy_audio = np.ones(8000, dtype=np.float32) * 0.1
    mock_checker = MagicMock(is_macos=MagicMock(return_value=False))
    stt = STTEngine(
        use_mock=False,
        api_key="test_groq_key",
        system_checker=mock_checker,
        allow_cloud_fallback=True
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"text": "Knox, cloud fallback"}

    with patch("requests.post", return_value=mock_resp) as mock_post:
        with patch.dict("sys.modules", {"faster_whisper": None, "whisper": None}):
            result = stt.transcribe(dummy_audio)
            assert mock_post.called
            assert result == "Knox, cloud fallback"
