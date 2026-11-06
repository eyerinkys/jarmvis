import os
import tempfile
from jarmvis.env_loader import load_dotenv

def test_load_dotenv_custom_path(monkeypatch):
    monkeypatch.delenv("TEST_KEY_ONE", raising=False)
    monkeypatch.delenv("TEST_KEY_TWO", raising=False)

    with tempfile.NamedTemporaryFile("w+", delete=False) as f:
        f.write("# Sample comment\n")
        f.write("TEST_KEY_ONE=hello_world\n")
        f.write("TEST_KEY_TWO=\"quoted_value\"\n")
        f.write("EMPTY_KEY=\n")
        tmp_path = f.name

    try:
        load_dotenv(tmp_path)
        assert os.environ.get("TEST_KEY_ONE") == "hello_world"
        assert os.environ.get("TEST_KEY_TWO") == "quoted_value"
        assert "EMPTY_KEY" not in os.environ
    finally:
        os.remove(tmp_path)
