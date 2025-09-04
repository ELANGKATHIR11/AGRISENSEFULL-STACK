import sys
import json
from typing import Any, Dict
import os

import requests  # type: ignore


def main() -> None:
    base = os.environ.get("AGRISENSE_API", "http://127.0.0.1:8004")
    # Usage: python ask_chatbot.py "your question" [top_k] [base_url]
    question = (
        "Which crop is best for sandy soil?" if len(sys.argv) < 2 else sys.argv[1]
    )
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    if len(sys.argv) > 3:
        base = sys.argv[3]
    # Prefer the new /chat/ask endpoint; legacy /chatbot/ask accepted too
    payload_new: Dict[str, Any] = {"message": question, "top_k": top_k}
    r = requests.post(f"{base}/chat/ask", json=payload_new, timeout=30)
    if r.status_code == 404:
        payload: Dict[str, Any] = {"question": question, "top_k": top_k}
        r = requests.post(f"{base}/chatbot/ask", json=payload, timeout=30)
    r.raise_for_status()
    print(json.dumps(r.json(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
