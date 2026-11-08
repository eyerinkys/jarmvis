import os
import tempfile
import wave
import numpy as np
import pytest
from jarmvis.audio_analyzer import AudioAnalyzer, AudioFeatures


def test_audio_analyzer_synthetic_signal():
    sr = 16000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    signal = 0.8 * np.sin(2 * np.pi * 440 * t)
    signal[int(0.4 * sr) : int(0.7 * sr)] = 0.0  # silence gap

    analyzer = AudioAnalyzer(fps=50)
    features = analyzer.extract_features_from_array(signal, sample_rate=sr)

    assert isinstance(features, AudioFeatures)
    assert features.fps == 50
    assert 48 <= len(features.rms_envelope) <= 52
    assert features.duration_sec == pytest.approx(1.0, abs=0.05)

    # Tone period should have significantly higher RMS than silence period
    tone_rms = np.mean(features.rms_envelope[5:15])
    silent_rms = np.mean(features.rms_envelope[25:30])
    assert tone_rms > silent_rms * 5.0
    assert len(features.beat_onsets) == len(features.rms_envelope)
    assert np.all(features.rms_envelope >= 0.0)
    assert np.all(features.rms_envelope <= 1.0)


def test_audio_analyzer_from_wav_file():
    sr = 16000
    t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
    signal = (0.5 * np.sin(2 * np.pi * 300 * t) * 32767).astype(np.int16)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        with wave.open(tmp_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(signal.tobytes())

        analyzer = AudioAnalyzer(fps=50)
        features = analyzer.extract_features_from_file(tmp_path)
        assert isinstance(features, AudioFeatures)
        assert features.duration_sec == pytest.approx(0.5, abs=0.05)
        assert len(features.rms_envelope) >= 20
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_audio_analyzer_empty_signal():
    analyzer = AudioAnalyzer(fps=50)
    features = analyzer.extract_features_from_array(np.array([], dtype=np.float32))
    assert len(features.rms_envelope) == 0
    assert len(features.beat_onsets) == 0
    assert features.duration_sec == 0.0


def test_audio_analyzer_from_mp3_file():
    sr = 16000
    t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
    samples = (0.5 * np.sin(2 * np.pi * 300 * t) * 32767).astype(np.int16)

    import av
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        container = av.open(tmp_path, mode="w")
        stream = container.add_stream("mp3", rate=sr)
        frame = av.AudioFrame.from_ndarray(samples.reshape(1, -1), format="s16", layout="mono")
        frame.sample_rate = sr
        for packet in stream.encode(frame):
            container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
        container.close()

        analyzer = AudioAnalyzer(fps=50)
        features = analyzer.extract_features_from_file(tmp_path)
        assert isinstance(features, AudioFeatures)
        assert features.duration_sec == pytest.approx(0.5, abs=0.1)
        assert len(features.rms_envelope) >= 20
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_audio_analyzer_invalid_file_fallback():
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp.write(b"not an audio file at all")
        tmp_path = tmp.name

    try:
        analyzer = AudioAnalyzer(fps=50)
        features = analyzer.extract_features_from_file(tmp_path)
        assert isinstance(features, AudioFeatures)
        assert len(features.rms_envelope) == 0
        assert features.duration_sec == 0.0
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_audio_analyzer_ffmpeg_fallback(monkeypatch):
    # Test that if PyAV fails, it falls back to ffmpeg CLI converter
    sr = 16000
    t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
    samples = (0.5 * np.sin(2 * np.pi * 300 * t) * 32767).astype(np.int16)

    import av
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        container = av.open(tmp_path, mode="w")
        stream = container.add_stream("mp3", rate=sr)
        frame = av.AudioFrame.from_ndarray(samples.reshape(1, -1), format="s16", layout="mono")
        frame.sample_rate = sr
        for packet in stream.encode(frame):
            container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
        container.close()

        # Force PyAV open to fail to test CLI fallback
        monkeypatch.setattr("av.open", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("av disabled")))

        analyzer = AudioAnalyzer(fps=50)
        features = analyzer.extract_features_from_file(tmp_path)
        assert isinstance(features, AudioFeatures)
        assert features.duration_sec == pytest.approx(0.5, abs=0.1)
        assert len(features.rms_envelope) >= 20
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)



