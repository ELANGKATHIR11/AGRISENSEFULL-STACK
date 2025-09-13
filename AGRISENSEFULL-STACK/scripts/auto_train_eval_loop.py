from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import Tuple

import requests  # type: ignore


def run(cmd: list[str], cwd: Path) -> int:
    print("$", " ".join(cmd))
    p = subprocess.Popen(cmd, cwd=str(cwd))
    return p.wait()


def reload_backend(base: str) -> None:
    for i in range(10):
        try:
            r = requests.post(f"{base}/chatbot/reload", timeout=20)
            if r.ok:
                time.sleep(0.2)
                return
        except Exception:
            time.sleep(0.5 + 0.2 * i)
    raise RuntimeError("failed to reload backend")


def eval10(repo: Path, base: str) -> Tuple[float, str]:
    cmd = [
        str(repo / ".venv" / "Scripts" / "python.exe"),
        str(repo / "scripts" / "eval_chatbot_http.py"),
        "--sample",
        "10",
        "--top_k",
        "3",
    ]
    p = subprocess.Popen(
        cmd, cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    out, _ = p.communicate()
    print(out)
    acc = 0.0
    for line in out.splitlines():
        if line.strip().startswith("acc@1="):
            # acc@1=xx.x% over 10 questions
            try:
                num = line.split("=")[1].split("%")[0].strip()
                acc = float(num) / 100.0
            except Exception:
                pass
    return acc, out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-iters", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--base", type=str, default="http://127.0.0.1:8004")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]

    for i in range(1, args.max_iters + 1):
        print(f"\n=== Iteration {i}/{args.max_iters} ===")
        code = run(
            [
                str(repo / ".venv" / "Scripts" / "python.exe"),
                str(repo / "scripts" / "train_chatbot.py"),
                "-e",
                str(args.epochs),
                "-bs",
                "256",
                "--vocab",
                "60000",
                "--seq-len",
                "128",
                "--augment",
            ],
            repo,
        )
        if code != 0:
            print("Training failed, aborting.")
            sys.exit(code)
        try:
            reload_backend(args.base)
        except Exception as e:
            print(f"Reload failed: {e}")
        acc, _ = eval10(repo, args.base)
        print(f"Iteration {i}: acc@1={acc*100:.1f}%")
        if acc >= 1.0:
            print("Reached 10/10. Stopping.")
            return
    print("Did not reach 10/10 within max iterations.")


if __name__ == "__main__":
    main()
