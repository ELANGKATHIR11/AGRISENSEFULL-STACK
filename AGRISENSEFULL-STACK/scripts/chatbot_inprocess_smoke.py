from typing import Any, Dict

from fastapi.testclient import TestClient
import sys
import os

# Ensure repo root is on sys.path so agrisense_app is importable when running from scripts/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agrisense_app.backend.main import app  # type: ignore


client = TestClient(app)


def pretty(obj: Any) -> str:
    try:
        import json

        return json.dumps(obj, indent=2, ensure_ascii=False)
    except Exception:
        return str(obj)


def main() -> None:
    print("/health =>", client.get("/health").json())
    # ensure chatbot artifacts are loaded
    print("/chatbot/reload =>", pretty(client.post("/chatbot/reload").json()))
    q = "Which crop is best for sandy soil?"
    res = client.post("/chatbot/ask", json={"question": q, "top_k": 3}).json()
    print("/chatbot/ask =>", pretty(res))


if __name__ == "__main__":
    main()
