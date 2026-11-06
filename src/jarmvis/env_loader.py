import os

def load_dotenv(path: str | None = None) -> None:
    """Loads key-value pairs from .env into os.environ without overriding existing vars."""
    if path is None:
        candidates = [
            os.path.join(os.getcwd(), ".env"),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")),
        ]
        path = next((p for p in candidates if os.path.isfile(p)), None)

    if not path or not os.path.isfile(path):
        return

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key and key not in os.environ and val:
                    os.environ[key] = val
    except Exception:
        pass
