"""
CLI to query the trained chatbot retrieval model.

Usage (PowerShell):
    .venv\\Scripts\\python.exe AGRISENSEFULL-STACK\\scripts\\chatbot_infer.py -q "Which crop grows best in acidic soil?" -k 5
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Tuple

import numpy as np
import tensorflow as tf

try:
    from tensorflow.keras import layers  # type: ignore
except ImportError:
    import keras  # type: ignore
    from keras import layers  # type: ignore


def load_artifacts(repo_root: Path):
    backend_dir = repo_root / "AGRISENSEFULL-STACK" / "agrisense_app" / "backend"
    if not backend_dir.exists():
        backend_dir = repo_root / "agrisense_app" / "backend"

    qenc_dir = backend_dir / "chatbot_question_encoder"
    index_npz = backend_dir / "chatbot_index.npz"
    index_json = backend_dir / "chatbot_index.json"
    if not (qenc_dir.exists() and index_npz.exists() and index_json.exists()):
        raise FileNotFoundError(
            "Missing model or index artifacts. Run train_chatbot.py first."
        )

    # Load SavedModel via Keras TFSMLayer for easy calling
    q_layer = layers.TFSMLayer(str(qenc_dir), call_endpoint="serve")

    with np.load(index_npz, allow_pickle=False) as data:
        emb = data["embeddings"]
    answers = json.loads(index_json.read_text(encoding="utf-8")).get("answers", [])
    return q_layer, emb, answers


def rank_answers(
    q_layer, embeddings: np.ndarray, answers: List[str], question: str, k: int = 5
) -> List[Tuple[float, str]]:
    q_vec = q_layer(tf.constant([question]))
    # TFSMLayer returns a tuple/list of tensors sometimes; handle both cases
    if isinstance(q_vec, (tuple, list)):
        q_vec = q_vec[0]
    q_vec = q_vec.numpy()[0]
    scores = embeddings @ q_vec  # cosine similarity if both are L2-normalized
    topk_idx = np.argsort(-scores)[:k]
    return [(float(scores[i]), answers[i]) for i in topk_idx]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--question", "-q", type=str, required=True)
    ap.add_argument("--topk", "-k", type=int, default=5)
    args = ap.parse_args()

    script_path = Path(__file__).resolve()
    repo_root = script_path.parents[2]
    q_layer, emb, answers = load_artifacts(repo_root)
    results = rank_answers(q_layer, emb, answers, args.question, args.topk)
    for i, (score, ans) in enumerate(results, 1):
        print(f"{i}. ({score:.3f}) {ans}")


if __name__ == "__main__":
    main()
