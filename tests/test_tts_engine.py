import os
from unittest.mock import MagicMock, patch
import pytest
from jarmvis.tts_engine import TTSEngine

def test_tts_initialization_defaults():
    tts = TTSEngine(use_mock=True)
    assert tts.voice == "en-US-ChristopherNeural"
    assert tts.use_mock is True

def test_tts_mock_speak(capsys):
    start_mock = MagicMock()
    end_mock = MagicMock()
    tts = TTSEngine(voice="en-GB-RyanNeural", use_mock=True)

    tts.speak("Hello sir, all systems operational.", on_playback_start=start_mock, on_playback_end=end_mock)

    assert start_mock.called
    assert end_mock.called
    captured = capsys.readouterr().out
    assert "[tts:mock]" in captured
    assert "voice=en-GB-RyanNeural" in captured
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
    assert "[tts:mock]" in captured
    assert "voice=en-GB-ThomasNeural" in captured

def test_tts_error_graceful_fallback(capsys, monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    # When synthesis fails (e.g. network disconnect), it should log error and call on_playback_end
    start_mock = MagicMock()
    end_mock = MagicMock()
    tts = TTSEngine(voice="en-GB-RyanNeural", use_mock=False, elevenlabs_api_key="")

    with patch("edge_tts.Communicate.save", side_effect=RuntimeError("Connection refused")):
        tts.speak("Emergency alert.", on_playback_start=start_mock, on_playback_end=end_mock)

    assert start_mock.called
    assert end_mock.called
    captured = capsys.readouterr().out
    assert "[tts:fallback]" in captured
    assert "Emergency alert." in captured

def test_tts_real_playback_invokes_system_player(monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    tts = TTSEngine(use_mock=False, elevenlabs_api_key="")
    
    with patch("edge_tts.Communicate.save") as mock_save, patch("jarmvis.tts_engine.play_audio_process") as mock_play:
        mock_proc = MagicMock()
        mock_play.return_value = mock_proc
        tts.speak("Testing audio player integration.")
        assert mock_save.called
        assert mock_play.called
        assert mock_proc.wait.called

def test_tts_elevenlabs_invocation():
    tts = TTSEngine(elevenlabs_api_key="xi-mock-key-12345", use_mock=False)
    fake_res = MagicMock()
    fake_res.status_code = 200
    fake_res.content = b"fake mp3 audio data bytes that are definitely longer than one hundred characters in total length to pass verification"

    with patch("requests.post", return_value=fake_res) as mock_post, patch("jarmvis.tts_engine.play_audio_process") as mock_play:
        mock_proc = MagicMock()
        mock_play.return_value = mock_proc
        tts.speak("Hello from ElevenLabs.", emotion="CONFIDENT")
        assert mock_post.called
        assert "api.elevenlabs.io" in mock_post.call_args[0][0]
        assert mock_play.called
        assert mock_proc.wait.called
