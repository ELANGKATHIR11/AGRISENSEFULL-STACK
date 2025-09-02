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
    r = requests.get(f"{BASE}/chatbot/metrics", timeout=10)
    print("/chatbot/metrics:", r.status_code)

    payloads = [
        {"question": "Tell me about carrot", "top_k": 3},
        {"question": "How to grow tomatoes?", "top_k": 3},
    ]
    for p in payloads:
        rr = requests.post(f"{BASE}/chatbot/ask", json=p, timeout=20)
        rr.raise_for_status()
        data: Dict[str, Any] = cast(Dict[str, Any], rr.json())
        results: List[Dict[str, Any]] = cast(
            List[Dict[str, Any]], data.get("results", [])
        )
        print("/chatbot/ask results:", len(results))


if __name__ == "__main__":
    smoke()
