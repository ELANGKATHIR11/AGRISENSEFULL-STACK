import os
import sys
import json
import requests  # type: ignore


def main() -> None:
    base = os.environ.get("AGRISENSE_API", "http://127.0.0.1:8004")
    if len(sys.argv) > 1:
        base = sys.argv[1]
    r = requests.post(f"{base}/chatbot/reload", timeout=30)
    r.raise_for_status()
    print(json.dumps(r.json(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
