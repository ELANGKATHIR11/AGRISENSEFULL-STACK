"""
Quick RAG HTTP smoke test.

Runs against a local backend on port 8004:
- GET /health
- POST /chat/ingest (defaults)
- POST /chat/reload
- POST /chat/ask with a known dataset question

Prints concise results including sources.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict

import requests


BASE = os.environ.get("AGRISENSE_BASE_URL", "http://127.0.0.1:8004")


def _print(label: str, value: Any) -> None:
    try:
        text = json.dumps(value, ensure_ascii=False)
    except Exception:
        text = str(value)
    print(f"{label}: {text}")


def main() -> int:
    # 1) Health
    try:
        r = requests.get(f"{BASE}/health", timeout=10)
        _print("GET /health", r.status_code)
    except Exception as e:
        _print("GET /health error", str(e))
        return 1

    # 2) Ingest (defaults)
    try:
        r = requests.post(f"{BASE}/chat/ingest", json={}, timeout=120)
        _print("POST /chat/ingest", r.status_code)
        try:
            _print("ingest.body", r.json())
        except Exception:
            pass
    except Exception as e:
        _print("POST /chat/ingest error", str(e))
        return 1

    # 3) Reload
    try:
        r = requests.post(f"{BASE}/chat/reload", json={}, timeout=20)
        _print("POST /chat/reload", r.status_code)
    except Exception as e:
        _print("POST /chat/reload error", str(e))
        return 1

    # 4) Ask (exact and normalized variants)
    q1 = {
        "message": "According to Simpson (1983), what is the basis of agriculture?",
        "top_k": 3,
    }
    q2 = {
        "message": "according to simpson 1983 what is the basis of agriculture???   ",
        "top_k": 3,
    }
    try:
        r1 = requests.post(f"{BASE}/chat/ask", json=q1, timeout=20)
        d1: Dict[str, Any] = r1.json()
        _print("POST /chat/ask (exact)", r1.status_code)
        _print("answer", d1.get("answer"))
        _print("sources", d1.get("sources"))
    except Exception as e:
        _print("/chat/ask exact error", str(e))
        return 1

    try:
        r2 = requests.post(f"{BASE}/chat/ask", json=q2, timeout=20)
        d2: Dict[str, Any] = r2.json()
        _print("POST /chat/ask (normalized)", r2.status_code)
        _print("answer", d2.get("answer"))
        _print("sources", d2.get("sources"))
    except Exception as e:
        _print("/chat/ask normalized error", str(e))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
