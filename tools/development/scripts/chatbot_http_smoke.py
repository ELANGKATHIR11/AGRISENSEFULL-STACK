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
    # Metrics may be absent; accept 404 as informational
    try:
        r = requests.get(f"{BASE}/chatbot/metrics", timeout=10)
        print("/chatbot/metrics:", r.status_code)
    except Exception as e:
        print("/chatbot/metrics ERROR:", e)

    # Try /chatbot/ask first; if unavailable (503/404), fallback to /chat/ask
    questions = ["Tell me about carrot", "How to grow tomatoes?"]
    for q in questions:
        try:
            rr = requests.post(
                f"{BASE}/chatbot/ask", json={"question": q, "top_k": 3}, timeout=20
            )
            if rr.status_code == 200:
                data: Dict[str, Any] = cast(Dict[str, Any], rr.json())
                results: List[Dict[str, Any]] = cast(
                    List[Dict[str, Any]], data.get("results", [])
                )
                print("/chatbot/ask results:", len(results))
                continue
            else:
                print("/chatbot/ask status:", rr.status_code)
        except Exception as e:
            print("/chatbot/ask ERROR:", e)

        # Fallback to lightweight chat API
        try:
            rc = requests.post(
                f"{BASE}/chat/ask", json={"message": q}, timeout=15
            )
            rc.raise_for_status()
            data2: Dict[str, Any] = cast(Dict[str, Any], rc.json())
            ans = data2.get("answer")
            print("/chat/ask answer: ", (ans[:60] + "...") if isinstance(ans, str) and len(ans) > 60 else ans)
        except Exception as e:
            print("/chat/ask ERROR:", e)


if __name__ == "__main__":
    smoke()
