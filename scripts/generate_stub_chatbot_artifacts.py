"""Generate minimal chatbot artifact files for local testing.

Creates:
 - agrisense_app/backend/chatbot_index.npz
 - agrisense_app/backend/chatbot_metrics.json

This is safe to run and intended for CI/dev testing when real artifacts are absent.
"""
from pathlib import Path
import json
import numpy as np


def main():
    backend = Path(__file__).resolve().parents[1] / "agrisense_app" / "backend"
    backend.mkdir(parents=True, exist_ok=True)
    npz_path = backend / "chatbot_index.npz"
    metrics_path = backend / "chatbot_metrics.json"

    # Small 1x384 embedding of zeros (dummy)
    emb = np.zeros((1, 384), dtype=np.float32)
    np.savez_compressed(npz_path, embeddings=emb)

    metrics = {"generated": True, "entries": 1}
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f)

    print(f"Wrote {npz_path} and {metrics_path}")


if __name__ == "__main__":
    main()
