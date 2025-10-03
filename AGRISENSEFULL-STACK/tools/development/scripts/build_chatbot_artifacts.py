"""Build chatbot artifacts from a CSV QA file.

Reads a CSV with columns: question,answer (header required).
Computes embeddings using the TF Keras encoder model at
`agrisense_app/backend/chatbot_question_encoder.keras` (if present).
Saves artifacts into `agrisense_app/backend/`:
 - chatbot_q_index.npz  (question embeddings + texts)
 - chatbot_index.npz    (answer embeddings + texts)
 - chatbot_qa_pairs.json (list of {question,answer,source})

Usage:
  .venv\\Scripts\\python.exe scripts\\build_chatbot_artifacts.py --csv agrisense_app/backend/chatbot_merged_clean.csv

This script uses batching to avoid OOM. If the encoder model isn't available,
it will exit with an informative message.
"""
import argparse
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd


def batch_iter(xs, batch_size=1024):
    for i in range(0, len(xs), batch_size):
        yield xs[i : i + batch_size]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", required=True, help="Path to QA CSV")
    p.add_argument("--out-dir", default="agrisense_app/backend", help="Where to write artifacts")
    p.add_argument("--model-path", default="agrisense_app/backend/chatbot_question_encoder.keras", help="TF Keras encoder path")
    p.add_argument("--batch-size", type=int, default=256)
    args = p.parse_args()

    csv_path = Path(args.csv)
    out_dir = Path(args.out_dir)
    model_path = Path(args.model_path)

    if not csv_path.exists():
        print(f"CSV file not found: {csv_path}")
        raise SystemExit(1)

    print("Loading CSV ->", csv_path)
    df = pd.read_csv(csv_path)
    # Expect columns: question, answer, source (source optional)
    if "question" not in df.columns or "answer" not in df.columns:
        print("CSV must contain 'question' and 'answer' columns")
        raise SystemExit(1)

    questions = df["question"].fillna("").astype(str).tolist()
    answers = df["answer"].fillna("").astype(str).tolist()
    sources = df["source"].fillna("").astype(str).tolist() if "source" in df.columns else [""] * len(questions)

    # Build QA pairs list
    qa_pairs = [{"question": q, "answer": a, "source": s} for q, a, s in zip(questions, answers, sources)]

    print(f"Read {len(qa_pairs)} QA pairs from CSV")

    # Ensure out dir exists
    out_dir.mkdir(parents=True, exist_ok=True)

    # Attempt to load a TF Keras encoder model. If missing or loading/prediction fails,
    # fall back to TF-IDF + TruncatedSVD embeddings (fast, deterministic) so we can
    # still build searchable artifacts.
    encoder = None
    try:
        import tensorflow as tf
    except Exception as e:
        print("TensorFlow import failed (will try TF-IDF fallback):", e)
        tf = None

    if tf is not None and model_path.exists():
        try:
            print("Loading encoder model from", model_path)
            encoder = tf.keras.models.load_model(str(model_path))  # type: ignore
        except Exception as e:
            print("Failed to load TF Keras encoder (will fallback to TF-IDF):", e)
            encoder = None
    else:
        if tf is None:
            print("TensorFlow not available — will use TF-IDF + TruncatedSVD fallback")
        else:
            print(f"Encoder model not found at {model_path}. Using TF-IDF + TruncatedSVD fallback.")

    # Helper: L2-normalize rows
    def l2norm(x: np.ndarray) -> np.ndarray:
        n = np.linalg.norm(x, axis=1, keepdims=True)
        n[n == 0] = 1.0
        return x / n

    # If we have a TF encoder, attempt to compute embeddings via batch predict.
    if encoder is not None:
        try:
            print("Computing question embeddings in batches (batch_size=", args.batch_size, ")")
            q_embs = []
            for batch in batch_iter(questions, args.batch_size):
                emb = encoder.predict(np.array(batch), verbose=0)
                q_embs.append(emb.astype(np.float32))
            q_embs = np.vstack(q_embs)
            print("Question embeddings shape:", q_embs.shape)

            print("Computing answer embeddings in batches")
            a_embs = []
            for batch in batch_iter(answers, args.batch_size):
                emb = encoder.predict(np.array(batch), verbose=0)
                a_embs.append(emb.astype(np.float32))
            a_embs = np.vstack(a_embs)
            print("Answer embeddings shape:", a_embs.shape)

            # Normalize
            q_embs = l2norm(q_embs)
            a_embs = l2norm(a_embs)
        except Exception as e:
            print("TF encoder failed at prediction time (falling back to TF-IDF):", e)
            encoder = None

    # If we don't have a working TF encoder, use TF-IDF + TruncatedSVD fallback
    if encoder is None:
        print("Building TF-IDF + TruncatedSVD embeddings fallback")
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.decomposition import TruncatedSVD
        except Exception as e:
            print("scikit-learn is required for TF-IDF fallback but import failed:", e)
            print("Please install scikit-learn (pip install scikit-learn) and retry.")
            raise

        # Fit TF-IDF on combined texts so both Q/A share the same feature space
        combined_texts = list(questions) + list(answers)
        print("Fitting TF-IDF vectorizer on", len(combined_texts), "documents")
        tfv = TfidfVectorizer(max_features=50000)
        X = tfv.fit_transform(combined_texts)
        print("TF-IDF matrix shape:", X.shape)

        # Choose components conservatively: <= min(n_samples-1, n_features-1, 256)
        n_samples, n_features = X.shape
        n_components = min(256, max(1, n_samples - 1), max(1, n_features - 1))
        if n_components < 1:
            n_components = 1
        print(f"Applying TruncatedSVD with n_components={n_components}")
        svd = TruncatedSVD(n_components=n_components)
        X_reduced = svd.fit_transform(X)
        X_reduced = X_reduced.astype(np.float32)

        # Split back to question and answer embeddings
        q_embs = X_reduced[: len(questions), :]
        a_embs = X_reduced[len(questions) : , :]

        # L2-normalize
        q_embs = l2norm(q_embs)
        a_embs = l2norm(a_embs)

    # Normalize embeddings (cosine similarity ready)
    def l2norm_final(x):
        n = np.linalg.norm(x, axis=1, keepdims=True)
        n[n == 0] = 1.0
        return x / n

    q_embs = l2norm_final(q_embs)
    a_embs = l2norm_final(a_embs)

    # Save artifacts
    q_index_path = out_dir / "chatbot_q_index.npz"
    idx_path = out_dir / "chatbot_index.npz"
    qa_json_path = out_dir / "chatbot_qa_pairs.json"

    # Save question-side index using backend's expected key names
    print("Saving question index to", q_index_path)
    # backend expects 'embeddings' and 'questions' keys in the q-index
    np.savez_compressed(q_index_path, embeddings=q_embs, questions=np.array(questions, dtype=object))

    # Save answer index using backend's expected key names
    print("Saving answer index to", idx_path)
    # backend expects 'embeddings' and 'answers' keys in the index
    np.savez_compressed(idx_path, embeddings=a_embs, answers=np.array(answers, dtype=object))

    # Save QA pairs JSON in the structure backend expects: {questions:[], answers:[]}
    print("Saving QA pairs JSON to", qa_json_path)
    qa_meta = {"questions": list(questions), "answers": list(answers)}
    try:
        # include sources if we have them
        if sources and len(sources) == len(questions):
            qa_meta["sources"] = list(sources)
    except Exception:
        pass
    with qa_json_path.open("w", encoding="utf-8") as f:
        json.dump(qa_meta, f, ensure_ascii=False, indent=2)

    print("Artifacts built successfully.")


if __name__ == "__main__":
    main()
