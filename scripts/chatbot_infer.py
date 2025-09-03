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
from tensorflow.keras import layers


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

    # Try to load SavedModel via Keras TFSMLayer for easy calling. If that fails
    # (for example, because the SavedModel uses py_function callbacks that are
    # not portable), fall back to loading the PyTorch SentenceTransformer at
    # runtime so the CLI still works.
    q_layer = None
    pt_model_name = "sentence-transformers/all-MiniLM-L6-v2"
    try:
        q_layer = layers.TFSMLayer(str(qenc_dir), call_endpoint="serve")
        encoder_mode = "tf"
    except Exception:
        # Fall back to PyTorch SentenceTransformer (requires sentence-transformers in env)
        try:
            from sentence_transformers import SentenceTransformer

            s = SentenceTransformer(pt_model_name)

            class _PTWrapper:
                def __init__(self, model):
                    self._m = model

                def __call__(self, texts):
                    # Accept a list of strings or a single string
                    if isinstance(texts, (list, tuple)):
                        strs = list(texts)
                    else:
                        strs = [texts]
                    emb = self._m.encode(strs, convert_to_numpy=True)
                    emb = emb.astype(np.float32)
                    # ensure L2-normalized
                    norms = np.linalg.norm(emb, axis=1, keepdims=True) + 1e-12
                    emb = emb / norms
                    return tf.constant(emb)

            q_layer = _PTWrapper(s)
            encoder_mode = "pt"
        except Exception as e:
            raise FileNotFoundError(
                "Could not load TFSMLayer SavedModel or fallback SentenceTransformer: "
                + str(e)
            )

    with np.load(index_npz, allow_pickle=False) as data:
        emb = data["embeddings"]
    answers = json.loads(index_json.read_text(encoding="utf-8")).get("answers", [])
    return q_layer, emb, answers


def rank_answers(
    q_layer, embeddings: np.ndarray, answers: List[str], question: str, k: int = 5
) -> List[Tuple[float, str]]:
    # Call the encoder in a safe, explicit way depending on its type.
    def _call_encoder(layer, texts):
        # If it's a Keras Layer instance, call with a tf.constant positional arg.
        try:
            is_keras_layer = isinstance(layer, tf.keras.layers.Layer)
        except Exception:
            is_keras_layer = False
        if is_keras_layer:
            print("[debug] Calling encoder as Keras layer")
            t = tf.constant(list(texts) if isinstance(texts, (list, tuple)) else [texts], dtype=tf.string)
            return layer(t)
        elif callable(layer):
            print("[debug] Calling encoder as Python callable/wrapper")
            return layer(texts)
        else:
            raise TypeError("Unsupported encoder type: %r" % type(layer))

    out = _call_encoder(q_layer, [question])
    # The TF layer may return a tensor, or a tuple/list containing a tensor
    if isinstance(out, (tuple, list)):
        out = out[0]
    # Convert to numpy vector and use first row
    if hasattr(out, "numpy"):
        q_vec = out.numpy()[0]
    else:
        # fallback: assume it's already a numpy array
        q_vec = np.array(out)[0]
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
    main()
if __name__ == "__main__":
    main()
                    # PT wrapper returns numpy array directly
                    out = q_layer([question])
                    q_vec = np.array(out)[0]

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
                q_layer, emb, answers, encoder_mode = load_artifacts(repo_root)
                print(f"Using encoder mode: {encoder_mode}")
                results = rank_answers(
                    q_layer, emb, answers, args.question, args.topk, encoder_mode=encoder_mode
                )
                for i, (score, ans) in enumerate(results, 1):
                    print(f"{i}. ({score:.3f}) {ans}")


            if __name__ == "__main__":
                main()
