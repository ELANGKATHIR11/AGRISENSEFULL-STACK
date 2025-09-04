import os
import sys
from typing import Any, Dict

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient  # type: ignore
from agrisense_app.backend.main import app


def run() -> None:
    client = TestClient(app)
    # metrics may or may not exist; 200 or 404 are acceptable
    # Legacy metrics endpoint moved to /chat/metrics (RAG adapter)
    # Keep compatibility with old tests by trying both endpoints.
    r0 = client.get("/chat/metrics")
    if r0.status_code == 404:
        r0 = client.get("/chatbot/metrics")
    assert r0.status_code in (200, 404)

    # ask about carrot to trigger crop facts shortcut
    # New RAG endpoint expects { message: str, zone_id?: str, top_k?: int }
    r1 = client.post(
        "/chat/ask", json={"message": "Tell me about carrot", "top_k": 3}
    )
    assert r1.status_code == 200, r1.text
    data: Dict[str, Any] = r1.json()
    results = data.get("results") or []
    assert isinstance(results, list) and len(results) >= 1

    # general QA
    r2 = client.post(
        "/chat/ask",
        json={"message": "Which crop grows best in sandy soil?", "top_k": 3},
    )
    assert r2.status_code == 200, r2.text

    print("Chatbot in-process smoke tests passed.")


if __name__ == "__main__":
    run()
