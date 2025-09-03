"""Exact (brute-force) nearest-neighbor retrieval using precomputed NPZ artifacts.

This script does not require external ANN libraries. It loads a TF encoder
(preferably the .keras file) and the `chatbot_index.npz` / `chatbot_qa_pairs.json`
artifacts and computes exact dot-product scores (assumes embeddings are L2-normalized).

Usage:
  .venv\Scripts\python.exe scripts\exact_nn_retrieve.py --dir agrisense_app/backend/test_run --question "How to grow tomatoes?" --topk 5
"""
from pathlib import Path
import argparse
import json
import numpy as np


def load_encoder(dir_path: Path):
    # Prefer the .keras file if present (loads cleanly with tf.keras)
    try:
        import tensorflow as tf
    except Exception as e:
        raise SystemExit("TensorFlow is required for encoding queries: " + str(e))

    keras_path = dir_path / "chatbot_question_encoder.keras"
    saved_dir = dir_path / "chatbot_question_encoder"

    if keras_path.exists():
        try:
            m = tf.keras.models.load_model(str(keras_path))
            return m, "keras"
        except Exception:
            pass

    if saved_dir.exists():
        try:
            # load as saved_model and use its 'serve' signature if present
            sm = tf.saved_model.load(str(saved_dir))
            # prefer callable signature
            if hasattr(sm, 'serve'):
                sig = sm.serve
                return sig, 'savedmodel'
            else:
                # try default signatures
                try:
                    fn = sm.signatures.get('serving_default')
                    if fn is not None:
                        return fn, 'savedmodel'
                except Exception:
                    pass
        except Exception:
            pass

    raise SystemExit(f"No TF encoder found in {dir_path}. Run training or build artifacts first.")


def encode_text(encoder, mode, text: str):
    import tensorflow as tf
    if mode == 'keras':
        out = encoder.predict(tf.constant([text], dtype=tf.string), verbose=0)
        return np.array(out)[0]
    elif mode == 'savedmodel':
        # many exported SavedModels accept a single positional tensor arg
        try:
            out = encoder(tf.constant([text], dtype=tf.string))
        except Exception:
            # some signatures expect keyword args; try common name 'text'
            try:
                out = encoder(text=tf.constant([text], dtype=tf.string))
            except Exception as e:
                raise SystemExit(f"SavedModel signature call failed: {e}")
        # the returned object might be a tensor or dict
        if isinstance(out, dict):
            # pick first value
            out = list(out.values())[0]
        if hasattr(out, 'numpy'):
            return out.numpy()[0]
        return np.array(out)[0]
    else:
        raise TypeError("Unsupported encoder mode: " + str(mode))


def l2norm(x: np.ndarray):
    n = np.linalg.norm(x, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return x / n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', default='agrisense_app/backend/test_run', help='Artifact directory containing index and encoder')
    ap.add_argument('--question', '-q', required=True)
    ap.add_argument('--topk', '-k', type=int, default=5)
    args = ap.parse_args()

    base = Path(args.dir)
    idx_npz = base / 'chatbot_index.npz'
    qa_json = base / 'chatbot_qa_pairs.json'

    if not idx_npz.exists() or not qa_json.exists():
        raise SystemExit(f"Missing artifacts in {base}. Expected: {idx_npz}, {qa_json}")

    enc, mode = load_encoder(base)
    print(f"Loaded encoder (mode={mode}) from {base}")

    data = np.load(idx_npz, allow_pickle=True)
    a_embs = data['embeddings'].astype(np.float32)
    # ensure L2-normalized
    a_embs = l2norm(a_embs)

    qa = json.loads(qa_json.read_text(encoding='utf-8'))
    answers = qa.get('answers', [])

    q_vec = encode_text(enc, mode, args.question)
    # ensure L2-normalized
    if q_vec.ndim == 1:
        q_vec = q_vec / (np.linalg.norm(q_vec) + 1e-12)
    else:
        q_vec = q_vec[0] / (np.linalg.norm(q_vec[0]) + 1e-12)

    scores = a_embs @ q_vec
    topk_idx = np.argsort(-scores)[: args.topk]

    for rank, i in enumerate(topk_idx, start=1):
        print(f"{rank}. ({scores[i]:.4f}) {answers[i]}")


if __name__ == '__main__':
    main()
