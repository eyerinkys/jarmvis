import os
from unittest.mock import MagicMock, patch
import pytest
from jarmvis.tts_engine import TTSEngine

def test_tts_initialization_defaults():
    tts = TTSEngine(use_mock=True)
    assert tts.voice == "en-GB-RyanNeural"
    assert tts.use_mock is True

def test_tts_mock_speak(capsys):
    start_mock = MagicMock()
    end_mock = MagicMock()
    tts = TTSEngine(voice="en-GB-RyanNeural", use_mock=True)

    tts.speak("Hello sir, all systems operational.", on_playback_start=start_mock, on_playback_end=end_mock)

    assert start_mock.called
    assert end_mock.called
    captured = capsys.readouterr().out
    assert "[MOCK TTS VOICE: en-GB-RyanNeural]" in captured
    assert "Hello sir, all systems operational." in captured

def test_tts_empty_string_noop():
    start_mock = MagicMock()
    end_mock = MagicMock()
    tts = TTSEngine(use_mock=True)

    tts.speak("   ", on_playback_start=start_mock, on_playback_end=end_mock)
    assert not start_mock.called
    assert not end_mock.called

def test_tts_custom_voice_and_rate(capsys):
    tts = TTSEngine(voice="en-GB-ThomasNeural", rate="+15%", use_mock=True)
    assert tts.voice == "en-GB-ThomasNeural"
    assert tts.rate == "+15%"
    tts.speak("Testing custom configuration.")
    captured = capsys.readouterr().out
    assert "[MOCK TTS VOICE: en-GB-ThomasNeural]" in captured

def test_tts_error_graceful_fallback(capsys):
    # When synthesis fails (e.g. network disconnect), it should log error and call on_playback_end
    start_mock = MagicMock()
    end_mock = MagicMock()
    tts = TTSEngine(voice="en-GB-RyanNeural", use_mock=False)

    with patch("edge_tts.Communicate.save", side_effect=RuntimeError("Connection refused")):
        tts.speak("Emergency alert.", on_playback_start=start_mock, on_playback_end=end_mock)

    assert start_mock.called
    assert end_mock.called
    captured = capsys.readouterr().out
    assert "[FALLBACK TTS]" in captured
    assert "Emergency alert." in captured

def test_tts_real_playback_invokes_system_player():
    tts = TTSEngine(use_mock=False)
    
    with patch("edge_tts.Communicate.save") as mock_save, patch("os.system") as mock_system:
        tts.speak("Testing audio player integration.")
        assert mock_save.called
        assert mock_system.called
        # On macOS, os.system should be called with afplay
        assert "afplay" in mock_system.call_args[0][0]
