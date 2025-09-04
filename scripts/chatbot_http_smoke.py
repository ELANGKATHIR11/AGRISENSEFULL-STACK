import time
from typing import Any, Dict, List, TypedDict, cast

import requests  # type: ignore

BASE = "http://127.0.0.1:8004"


def wait_ready(timeout: float = 10.0) -> None:
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            r = requests.get(f"{BASE}/health", timeout=2)
            if r.ok:
                return
        except Exception:
            pass
        time.sleep(0.3)
    raise SystemExit("Backend did not start in time")


def smoke() -> None:
    wait_ready()
    # Prefer the new /chat/metrics endpoint; fall back to legacy /chatbot/metrics
    r = requests.get(f"{BASE}/chat/metrics", timeout=10)
    if r.status_code == 404:
        r = requests.get(f"{BASE}/chatbot/metrics", timeout=10)
    print("/chat metrics status:", r.status_code)

    payloads = [
        {"question": "Tell me about carrot", "top_k": 3},
        {"question": "How to grow tomatoes?", "top_k": 3},
    ]
    for p in payloads:
        # Map old payload shape to new shape expected by /chat/ask
        payload = {"message": p.get("question"), "top_k": p.get("top_k", 3)}
        rr = requests.post(f"{BASE}/chat/ask", json=payload, timeout=20)
        if rr.status_code == 404:
            # fallback to legacy endpoint
            rr = requests.post(f"{BASE}/chatbot/ask", json=p, timeout=20)
        rr.raise_for_status()
        data: Dict[str, Any] = cast(Dict[str, Any], rr.json())
        # New endpoint returns { answer: str, sources?: [] } while legacy returned results list
        if isinstance(data.get("results"), list):
            results: List[Dict[str, Any]] = cast(List[Dict[str, Any]], data.get("results", []))
            print("/chatbot/ask results:", len(results))
        else:
            print("/chat/ask reply length:", len(data.get("answer", "")))


if __name__ == "__main__":
    smoke()
