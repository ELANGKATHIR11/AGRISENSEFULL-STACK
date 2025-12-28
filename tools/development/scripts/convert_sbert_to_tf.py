"""Download a sentence-transformer, wrap it and export as a TF SavedModel, and build NPZ artifacts.

Usage:
  .venv\\Scripts\\python.exe scripts\\convert_sbert_to_tf.py --model sentence-transformers/all-MiniLM-L6-v2
"""
import argparse
from pathlib import Path
import numpy as np
import json
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Provide types for the language server when available
    try:  # pragma: no cover - type checking only
        from sentence_transformers import SentenceTransformer  # type: ignore
    except Exception:  # pragma: no cover
        pass


def convert_and_build(model_name: str, out_dir: Path, csv_path: Path):
    # Lazy import heavy libs with runtime check
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "The 'sentence-transformers' package is required. "
            "Install it in the project's virtualenv with: .venv\\Scripts\\python.exe -m pip install sentence-transformers"
        ) from e

    try:
        import tensorflow as tf  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "TensorFlow is required to export a SavedModel. Install it in the project's virtualenv, e.g.: "
            ".venv\\Scripts\\python.exe -m pip install tensorflow"
        ) from e

    print("Downloading model:", model_name)
    s = SentenceTransformer(model_name)

    # Create a simple TF wrapper
    class Wrapper(tf.Module):
        def __init__(self, model):
            super().__init__()
            self._pt = model

        @tf.function(input_signature=[tf.TensorSpec(shape=[None], dtype=tf.string, name="text")])  # type: ignore
        def serve(self, texts):
            # SentenceTransformer expects list[str]
            strs = [t.decode("utf-8") if isinstance(t, bytes) else str(t) for t in texts.numpy()]
            emb = self._pt.encode(strs, convert_to_numpy=True)
            emb = emb.astype('float32')
            # ensure L2-normalized
            n = np.linalg.norm(emb, axis=1, keepdims=True)
            n[n == 0] = 1.0
            emb = emb / n
            return tf.convert_to_tensor(emb)

    # Export SavedModel
    wrapper = Wrapper(s)
    saved_dir = out_dir / "chatbot_question_encoder"
    if saved_dir.exists():
        print("Removing existing saved model at", saved_dir)
        import shutil

        shutil.rmtree(saved_dir)
    print("Saving SavedModel to", saved_dir)
    tf.saved_model.save(wrapper, str(saved_dir), signatures={'serve': wrapper.serve})

    # Build artifacts: compute embeddings for CSV
    import pandas as pd
    df = pd.read_csv(csv_path)
    questions = df['question'].fillna('').astype(str).tolist()
    answers = df['answer'].fillna('').astype(str).tolist()
    print(f"Computing embeddings for {len(questions)} QA pairs")
    # Use the sentence-transformers model directly for batch encoding
    q_emb = s.encode(questions, convert_to_numpy=True, show_progress_bar=True)
    a_emb = s.encode(answers, convert_to_numpy=True, show_progress_bar=True)
    # normalize
    def l2norm(x):
        n = np.linalg.norm(x, axis=1, keepdims=True)
        n[n == 0] = 1.0
        return (x / n).astype(np.float32)

    q_emb = l2norm(q_emb)
    a_emb = l2norm(a_emb)

    q_npz = out_dir / 'chatbot_q_index.npz'
    a_npz = out_dir / 'chatbot_index.npz'
    qa_json = out_dir / 'chatbot_qa_pairs.json'
    print('Saving q index to', q_npz)
    np.savez_compressed(q_npz, embeddings=q_emb, questions=np.array(questions, dtype=object))
    print('Saving answer index to', a_npz)
    np.savez_compressed(a_npz, embeddings=a_emb, answers=np.array(answers, dtype=object))
    print('Saving QA json to', qa_json)
    with qa_json.open('w', encoding='utf-8') as f:
        json.dump({'questions': questions, 'answers': answers}, f, ensure_ascii=False, indent=2)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--model', default='sentence-transformers/all-MiniLM-L6-v2')
    p.add_argument('--out-dir', default='agrisense_app/backend')
    p.add_argument('--csv', default='agrisense_app/backend/chatbot_merged_clean.csv')
    return p.parse_args()


if __name__ == '__main__':
    args = parse_args()
    convert_and_build(args.model, Path(args.out_dir), Path(args.csv))
