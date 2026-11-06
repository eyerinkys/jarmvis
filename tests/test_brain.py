import json
import pytest
from unittest.mock import patch, MagicMock
from jarmvis.brain import JarvisBrain, SYSTEM_PROMPT, extract_json

def test_parse_structured_json_response():
    brain = JarvisBrain(use_mock=True)
    response = brain.think("Pick up that block on your left")
    assert "speech" in response
    assert response["macro"] == "PICK_BLOCK"
    assert response["emotion"] in ["FOCUSED", "CONFIDENT", "ALERT"]
    assert response["face"] in ["ALERT", "FOCUSED", "NEUTRAL"]

def test_parse_scolding_response():
    brain = JarvisBrain(use_mock=True)
    response = brain.think("Dummy you messed up, go to the corner!")
    assert response["emotion"] == "ASHAMED"
    assert response["macro"] == "DUNCE_CORNER"
    assert response["face"] == "SAD"

def test_parse_praise_response():
    brain = JarvisBrain(use_mock=True)
    response = brain.think("Good job Dum-E, that was great!")
    assert response["emotion"] == "EXCITED"
    assert response["macro"] == "CELEBRATE"
    assert response["face"] == "HAPPY"

def test_ollama_fallback_to_mock_on_error():
    brain = JarvisBrain(use_mock=False)
    # Pointing to invalid local URL should gracefully fall back to mock without raising exception
    response = brain.think("Pick up the block")
    assert response["macro"] == "PICK_BLOCK"

def test_extract_json_markdown_blocks():
    markdown_output = """Here is the plan:
```json
{
  "speech": "I shall attend to this immediately, sir.",
  "emotion": "CONFIDENT",
  "face": "FOCUSED",
  "macro": "PICK_BLOCK"
}
```
Standing by."""
    parsed = extract_json(markdown_output)
    assert parsed["speech"] == "I shall attend to this immediately, sir."
    assert parsed["emotion"] == "CONFIDENT"
    assert parsed["face"] == "FOCUSED"
    assert parsed["macro"] == "PICK_BLOCK"

def test_extract_json_malformed_fallback():
    raw = "Not valid JSON at all."
    parsed = extract_json(raw)
    assert parsed["speech"] == "Not valid JSON at all."
    assert parsed["macro"] is None
    assert parsed["emotion"] == "NEUTRAL"
    assert parsed["face"] == "NEUTRAL"

def test_ollama_successful_response():
    brain = JarvisBrain(use_mock=False)
    fake_response = MagicMock()
    fake_response.read.return_value = json.dumps({
        "response": json.dumps({
            "speech": "Splendid, sir. Everything is proceeding as expected.",
            "emotion": "CONFIDENT",
            "face": "NEUTRAL",
            "macro": None
        })
    }).encode("utf-8")
    fake_response.__enter__.return_value = fake_response
    fake_response.__exit__.return_value = None

    with patch("urllib.request.urlopen", return_value=fake_response):
        res = brain.think("Status report")
        assert res["speech"] == "Splendid, sir. Everything is proceeding as expected."
        assert res["emotion"] == "CONFIDENT"
        assert res["face"] == "NEUTRAL"
        assert res["macro"] is None

def test_brain_init_spec_compliance():
    brain = JarvisBrain("qwen2.5:7b", "test-api-key", use_mock=True)
    assert brain.model == "qwen2.5:7b"
    assert brain.api_key == "test-api-key"
    assert brain.use_mock is True
    assert brain.endpoint == "http://localhost:11434/api/generate"

def test_groq_llama_successful_response():
    brain = JarvisBrain(api_key="gsk_mock_valid_key_for_testing_1234567890", use_mock=False)
    fake_response = MagicMock()
    fake_response.read.return_value = json.dumps({
        "choices": [{
            "message": {
                "content": json.dumps({
                    "speech": "Indeed, sir. Llama 3.3 70B is functioning at peak efficiency.",
                    "emotion": "CONFIDENT",
                    "face": "FOCUSED",
                    "macro": None
                })
            }
        }]
    }).encode("utf-8")
    fake_response.__enter__.return_value = fake_response
    fake_response.__exit__.return_value = None

    with patch("urllib.request.urlopen", return_value=fake_response) as mock_urlopen:
        res = brain.think("Status report with Llama")
        assert mock_urlopen.called
        assert res["speech"] == "Indeed, sir. Llama 3.3 70B is functioning at peak efficiency."
        assert res["emotion"] == "CONFIDENT"
