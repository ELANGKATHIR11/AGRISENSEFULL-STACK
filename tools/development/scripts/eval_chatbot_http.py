from __future__ import annotations

import argparse
import json
import os
import random
import re
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import requests  # type: ignore


def normalize_text(s: str) -> str:
    s = s.lower().strip()
    s = s.replace("Â°C", "°C").replace("Â", "").replace("\u00c2\u00b0C", "°C")
    s = re.sub(r"\s+", " ", s)
    return s


def jaccard(a: str, b: str) -> float:
    ta = set(w for w in re.findall(r"\w+", a.lower()) if len(w) >= 3)
    tb = set(w for w in re.findall(r"\w+", b.lower()) if len(w) >= 3)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union else 0.0


def load_pairs(repo_root: Path, sample: int, seed: int = 42) -> List[Tuple[str, str]]:
    # Reuse dataset loader from compute_chatbot_metrics if available
    try:
        import importlib.util

        script = (
            repo_root / "AGRISENSEFULL-STACK" / "scripts" / "compute_chatbot_metrics.py"
        )
        if not script.exists():
            script = repo_root / "scripts" / "compute_chatbot_metrics.py"
        spec = importlib.util.spec_from_file_location("cbm", str(script))
        assert spec and spec.loader
        cbm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cbm)  # type: ignore
        df = cbm.load_datasets(repo_root)  # type: ignore
        df = df.sample(n=min(sample, len(df)), random_state=seed).reset_index(drop=True)
        return list(
            zip(df["question"].astype(str).tolist(), df["answer"].astype(str).tolist())
        )
    except Exception as e:
        raise RuntimeError(f"Failed to load datasets: {e}")


def write_backend_env(backend_dir: Path, alpha: float, min_cos: float) -> None:
    env_path = backend_dir / ".env"
    lines: List[str] = []
    if env_path.exists():
        try:
            lines = env_path.read_text(encoding="utf-8").splitlines()
        except Exception:
            lines = []

    def upsert(lines: List[str], key: str, value: str) -> List[str]:
        out: List[str] = []
        found = False
        for ln in lines:
            if re.match(rf"^\s*{re.escape(key)}\s*=", ln):
                out.append(f"{key}={value}")
                found = True
            else:
                out.append(ln)
        if not found:
            out.append(f"{key}={value}")
        return out

    lines = upsert(lines, "CHATBOT_ALPHA", f"{alpha}")
    lines = upsert(lines, "CHATBOT_MIN_COS", f"{min_cos}")
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def wait_ready(base: str, timeout: float = 20.0) -> None:
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            r = requests.get(f"{base}/health", timeout=2)
            if r.ok:
                return
        except Exception:
            pass
        time.sleep(0.3)
    raise RuntimeError("Backend health check timed out")


def reload_backend(base: str) -> Dict[str, Any]:
    # A reload can briefly drop the connection; be patient and verify health
    for i in range(10):
        try:
            r = requests.post(f"{base}/chatbot/reload", timeout=20)
            if r.ok:
                # Give the app a moment to settle and confirm health
                time.sleep(0.3)
                try:
                    wait_ready(base, timeout=10)
                except Exception:
                    pass
                return r.json()
        except Exception:
            time.sleep(0.6 + 0.2 * i)
    # As a last resort, if health is OK, proceed even if reload endpoint keeps failing
    try:
        wait_ready(base, timeout=10)
        return {"ok": True}
    except Exception:
        raise RuntimeError("Failed to reload backend")


def evaluate_once(
    base: str, qa: List[Tuple[str, str]], top_k: int = 3
) -> Tuple[float, List[Dict[str, Any]]]:
    correct = 0
    details: List[Dict[str, Any]] = []
    for q, gold in qa:
        try:
            resp = requests.post(
                f"{base}/chatbot/ask", json={"question": q, "top_k": top_k}, timeout=30
            )
            if not resp.ok:
                details.append({"q": q, "gold": gold, "ok": False, "err": resp.text})
                continue
            data = resp.json()
            results = data.get("results") or []
            if not results:
                details.append({"q": q, "gold": gold, "ok": False, "err": "no results"})
                continue
            pred = str(results[0].get("text") or results[0].get("answer") or "")
            # Exact or fuzzy match
            ok = False
            n_pred = normalize_text(pred)
            n_gold = normalize_text(gold)
            if n_pred == n_gold:
                ok = True
            elif n_gold in n_pred or n_pred in n_gold:
                ok = True
            elif jaccard(n_pred, n_gold) >= 0.5:
                ok = True
            if ok:
                correct += 1
            details.append({"q": q, "gold": gold, "pred": pred, "ok": ok})
        except Exception as e:
            details.append({"q": q, "gold": gold, "ok": False, "err": str(e)})
    acc = correct / len(qa) if qa else 0.0
    return acc, details


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sample", type=int, default=100, help="Number of questions to evaluate"
    )
    parser.add_argument(
        "--base", type=str, default="http://127.0.0.1:8004", help="Backend base URL"
    )
    parser.add_argument("--top_k", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--grid",
        action="store_true",
        help="Grid-search alpha/min_cos via .env + reload",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    backend_dir = repo_root / "agrisense_app" / "backend"
    qa = load_pairs(repo_root, sample=args.sample, seed=args.seed)

    if args.grid:
        # Parameter grid for quick tuning
        alphas = [0.45, 0.5, 0.55, 0.6]
        mins = [0.28, 0.30, 0.32, 0.34]
        tried: List[Tuple[float, float, float]] = []  # (alpha, min_cos, acc)
        best = (-1.0, 0.0, 0.0, [])  # (acc, alpha, min_cos, details)
        for a in alphas:
            for m in mins:
                write_backend_env(backend_dir, a, m)
                info = reload_backend(args.base)
                time.sleep(0.3)
                acc, details = evaluate_once(args.base, qa, top_k=args.top_k)
                tried.append((a, m, acc))
                if acc > best[0]:
                    best = (acc, a, m, details)
                print(
                    f"alpha={a:.2f} min_cos={m:.2f} -> acc@1={acc*100:.1f}% (answers={info.get('answers')})"
                )

        acc, a, m, details = best
        print("\nBest:")
        print(f"alpha={a:.2f} min_cos={m:.2f} -> acc@1={acc*100:.1f}%")
        # Persist best into backend .env
        write_backend_env(backend_dir, a, m)
        try:
            reload_backend(args.base)
        except Exception:
            pass
    else:
        # Single eval of current settings with a light reload attempt
        try:
            wait_ready(args.base, timeout=20)
        except Exception:
            pass
        try:
            reload_backend(args.base)
        except Exception:
            pass
        acc, details = evaluate_once(args.base, qa, top_k=args.top_k)
        print(f"acc@1={acc*100:.1f}% over {len(qa)} questions (top_k={args.top_k})")

    # Dump failure examples for inspection
    fails = [d for d in details if not d.get("ok")]
    out = backend_dir / "chatbot_eval_failures.json"
    out.write_text(
        json.dumps(fails[:50], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Saved up to 50 failure cases -> {out}")


if __name__ == "__main__":
    main()
