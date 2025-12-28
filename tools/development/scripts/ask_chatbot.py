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
    payload: Dict[str, Any] = {"question": question, "top_k": top_k}
    r = requests.post(f"{base}/chatbot/ask", json=payload, timeout=30)
    r.raise_for_status()
    print(json.dumps(r.json(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
