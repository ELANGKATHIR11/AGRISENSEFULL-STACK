"""
Train a QA retrieval chatbot model (bi-encoder) on available datasets.

Datasets used (if present):
- KisanVaani (CSV): <repo_root>/KisanVaani_agriculture_qa.csv
- Soil QA (CSV): <repo_root>/Agriculture-Soil-QA-Pairs-Dataset/qna-dataset-farmgenie-soil-v2.csv
- Agrisense curated (CSV): d:/downloads/agrisense_chatbot_dataset.csv (Windows default path)

Outputs (saved under backend):
- agrisense_app/backend/chatbot_question_encoder.keras
- agrisense_app/backend/chatbot_answer_encoder.keras
- agrisense_app/backend/chatbot_index.npz (embeddings)
- agrisense_app/backend/chatbot_index.json (texts + ids)

Usage (PowerShell):
  .venv\\Scripts\\python.exe AGRISENSEFULL-STACK\\scripts\\train_chatbot.py -e 3 -bs 256
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import List, Tuple
import random

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras  # type: ignore
from tensorflow.keras import layers  # type: ignore


def load_datasets(repo_root: Path) -> pd.DataFrame:
    # Prefer pre-cleaned merged CSV if available
    merged = repo_root / "agrisense_app" / "backend" / "chatbot_merged_clean.csv"
    if merged.exists():
        df = pd.read_csv(merged)
        cols = {str(c).strip().lower(): c for c in df.columns}
        q = cols.get("question") or cols.get("questions") or cols.get("q")
        a = cols.get("answer") or cols.get("answers") or cols.get("a")
        if q and a:
            df = df.rename(columns={q: "question", a: "answer"})[["question", "answer"]]
            df["source"] = df.get("source", "Merged")
            df["question"] = df["question"].astype(str).str.strip()
            df["answer"] = df["answer"].astype(str).str.strip()
            df = df[(df["question"] != "") & (df["answer"] != "")]
            df.drop_duplicates(subset=["question", "answer"], inplace=True)
            df.drop_duplicates(subset=["question"], inplace=True)
            return df

    frames: List[pd.DataFrame] = []
    # Support both workspace root and project folder layouts
    roots = [repo_root]
    proj = repo_root / "AGRISENSEFULL-STACK"
    if proj.exists():
        roots.append(proj)

    # 1) KisanVaani prepared CSV
    kisan_csv = next(
        (
            r / "KisanVaani_agriculture_qa.csv"
            for r in roots
            if (r / "KisanVaani_agriculture_qa.csv").exists()
        ),
        None,
    )
    if kisan_csv and kisan_csv.exists():
        df = pd.read_csv(kisan_csv)
        cols = {c.lower(): c for c in df.columns}
        q = cols.get("question")
        a = cols.get("answer")
        if q and a:
            df = df.rename(columns={q: "question", a: "answer"})[["question", "answer"]]
            df["source"] = "KisanVaani"
            frames.append(df)

    # 2) Soil QA CSV from Hugging Face clone
    soil_csv = None
    for r in roots:
        c1 = (
            r
            / "Agriculture-Soil-QA-Pairs-Dataset"
            / "qna-dataset-farmgenie-soil-v2.csv"
        )
        if c1.exists():
            soil_csv = c1
            break
    if soil_csv is not None and soil_csv.exists():
        df = pd.read_csv(soil_csv)
        # Columns typically: index, ANSWER, QUESTION.question, QUESTION.paragraph
        # Prefer QUESTION.question as the question text; ANSWER as answer
        mapping = {}
        for col in df.columns:
            cl = col.strip().lower()
            if cl in (
                "question",
                "question.question",
                "questions",
                "question_text",
                "q",
            ):
                mapping[col] = "question"
            elif cl in ("answer", "answers", "a"):
                mapping[col] = "answer"
            elif cl == "question.paragraph" or cl == "question_context":
                # optional context not used directly
                pass
        # If mapping is empty, try known names
        if not mapping:
            if "QUESTION.question" in df.columns and "ANSWER" in df.columns:
                mapping = {"QUESTION.question": "question", "ANSWER": "answer"}
        if mapping:
            df = df.rename(columns=mapping)
            # drop unnamed index column(s)
            df = df[[c for c in df.columns if not str(c).lower().startswith("unnamed")]]
            if set(["question", "answer"]).issubset(df.columns):
                df = df[["question", "answer"]]
                df["source"] = "SoilQA"
                frames.append(df)

    # 3) Agrisense curated CSV (downloaded path)
    curated_csv = Path("D:/downloads/agrisense_chatbot_dataset.csv")
    if curated_csv.exists():
        df = pd.read_csv(curated_csv)
        cols = {c.lower(): c for c in df.columns}
        q = cols.get("question")
        a = cols.get("answer")
        if q and a:
            df = df.rename(columns={q: "question", a: "answer"})[["question", "answer"]]
            df["source"] = "Curated"
            frames.append(df)

    # 4) Farming FAQ assistant CSVs in repo root
    for fname in [
        "Farming_FAQ_Assistant_Dataset.csv",
        "Farming_FAQ_Assistant_Dataset (2).csv",
    ]:
        fpath = next((r / fname for r in roots if (r / fname).exists()), None)
        if fpath and fpath.exists():
            try:
                df = pd.read_csv(fpath)
                cols = {str(c).strip().lower(): c for c in df.columns}
                q = cols.get("question")
                a = cols.get("answer")
                if q and a:
                    df = df.rename(columns={q: "question", a: "answer"})[
                        ["question", "answer"]
                    ]
                    df["source"] = "FarmingFAQ"
                    frames.append(df)
            except Exception:
                pass

    # 5) Generic data_core.csv (try to map question/answer)
    data_core = next(
        (r / "data_core.csv" for r in roots if (r / "data_core.csv").exists()), None
    )
    if data_core and data_core.exists():
        try:
            df = pd.read_csv(data_core)
            cols = {str(c).strip().lower(): c for c in df.columns}
            q = cols.get("question") or cols.get("questions") or cols.get("q")
            a = cols.get("answer") or cols.get("answers") or cols.get("a")
            if q and a:
                df = df.rename(columns={q: "question", a: "answer"})[
                    ["question", "answer"]
                ]
                df["source"] = "DataCore"
                frames.append(df)
        except Exception:
            pass

    # 6) RAG-augmented CSV at project root
    rag_csv = next(
        (r / "rag_qa_gemini.csv" for r in roots if (r / "rag_qa_gemini.csv").exists()),
        None,
    )
    if rag_csv and rag_csv.exists():
        try:
            df = pd.read_csv(rag_csv)
            cols = {str(c).strip().lower(): c for c in df.columns}
            q = cols.get("question")
            a = cols.get("answer")
            if q and a:
                df = df.rename(columns={q: "question", a: "answer"})[
                    ["question", "answer"]
                ]
                df["source"] = "RAGGemini"
                frames.append(df)
        except Exception:
            pass

    if not frames:
        raise FileNotFoundError(
            "No datasets found. Ensure at least one CSV is present."
        )

    df_all = pd.concat(frames, ignore_index=True)
    # Basic cleaning
    df_all["question"] = df_all["question"].astype(str).str.strip()
    df_all["answer"] = df_all["answer"].astype(str).str.strip()
    df_all = df_all[(df_all["question"] != "") & (df_all["answer"] != "")]
    df_all.drop_duplicates(subset=["question", "answer"], inplace=True)
    # Optional: Drop obvious trivial duplicates that appear many times in Farming FAQ
    df_all.drop_duplicates(subset=["question"], inplace=True)
    return df_all


def build_biencoder(
    vocab_size: int = 50000, seq_len: int = 96, emb_dim: int = 256
) -> Tuple[keras.Model, keras.Model]:
    # Shared TextVectorization
    vectorizer = layers.TextVectorization(
        max_tokens=vocab_size,
        output_mode="int",
        output_sequence_length=seq_len,
        standardize="lower_and_strip_punctuation",
        name="text_vectorizer",
    )

    def make_encoder(name: str) -> keras.Model:
        inp = keras.Input(shape=(), dtype=tf.string, name=f"{name}_text")
        x = vectorizer(inp)
        x = layers.Embedding(vocab_size, emb_dim, name=f"{name}_embed")(x)
        x = layers.GlobalAveragePooling1D()(x)
        x = layers.Dense(emb_dim, activation="relu", name=f"{name}_proj")(x)
        # L2 normalize for cosine similarity using a Keras layer
        x = layers.UnitNormalization(axis=-1, name=f"{name}_l2norm")(x)
        return keras.Model(inp, x, name=f"{name}_encoder")

    q_encoder = make_encoder("question")
    a_encoder = make_encoder("answer")

    # attach vectorizer to question encoder for adaptation later
    q_encoder.text_vectorizer = vectorizer  # type: ignore[attr-defined]
    a_encoder.text_vectorizer = vectorizer  # type: ignore[attr-defined]
    return q_encoder, a_encoder


class BiEncoderTrainer(keras.Model):
    def __init__(
        self, q_encoder: keras.Model, a_encoder: keras.Model, temperature: float = 0.05
    ):
        super().__init__()
        self.q_encoder = q_encoder
        self.a_encoder = a_encoder
        self.temperature = temperature

    def train_step(self, data):
        (q_texts, a_texts), _ = data
        batch_size = tf.shape(q_texts)[0]  # type: ignore
        with tf.GradientTape() as tape:
            q_emb = self.q_encoder(q_texts, training=True)
            a_emb = self.a_encoder(a_texts, training=True)
            # cosine sim: dot product since vectors are L2-normalized
            logits = tf.matmul(q_emb, a_emb, transpose_b=True) / self.temperature
            labels = tf.range(batch_size)
            loss1 = tf.keras.losses.sparse_categorical_crossentropy(  # type: ignore
                labels, logits, from_logits=True
            )
            # symmetric loss (answers->questions)
            loss2 = tf.keras.losses.sparse_categorical_crossentropy(  # type: ignore
                labels, tf.transpose(logits), from_logits=True
            )
            loss = tf.reduce_mean(loss1 + loss2) / 2.0

        train_vars = (
            self.q_encoder.trainable_variables + self.a_encoder.trainable_variables
        )
        grads = tape.gradient(loss, train_vars)
        self.optimizer.apply_gradients(zip(grads, train_vars))  # type: ignore
        return {"loss": loss}

    def test_step(self, data):
        (q_texts, a_texts), _ = data
        batch_size = tf.shape(q_texts)[0]  # type: ignore
        q_emb = self.q_encoder(q_texts, training=False)
        a_emb = self.a_encoder(a_texts, training=False)
        logits = tf.matmul(q_emb, a_emb, transpose_b=True) / self.temperature
        labels = tf.range(batch_size)
        loss1 = tf.keras.losses.sparse_categorical_crossentropy(  # type: ignore
            labels, logits, from_logits=True
        )
        loss2 = tf.keras.losses.sparse_categorical_crossentropy(  # type: ignore
            labels, tf.transpose(logits), from_logits=True
        )
        loss = tf.reduce_mean(loss1 + loss2) / 2.0
        # simple recall@1 metric
        preds = tf.argmax(logits, axis=1, output_type=tf.int32)
        r1 = tf.reduce_mean(tf.cast(tf.equal(preds, labels), tf.float32))
        return {"loss": loss, "recall_at_1": r1}


def _tokenize_basic(text: str) -> List[str]:
    return [t for t in text.strip().split() if t]


_STOPWORDS = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "in",
    "on",
    "for",
    "of",
    "to",
    "and",
}


_SYNONYMS = {
    "fertilizer": ["fertiliser", "manure"],
    "pesticide": ["insecticide", "spray"],
    "soil": ["earth"],
    "crop": ["plant"],
    "water": ["irrigate", "watering"],
}


def augment_question(text: str, prob: float = 0.3) -> str:
    """Light, safe augmentation: random dropout/swap/synonym.
    Applied with probability per transform; multiple can apply.
    """
    toks = _tokenize_basic(text)
    if not toks:
        return text
    # Random dropout of a non-critical token
    if random.random() < prob and len(toks) > 4:
        idxs = [i for i, t in enumerate(toks) if t.lower() not in _STOPWORDS]
        if idxs:
            del toks[random.choice(idxs)]
    # Random swap of adjacent tokens
    if random.random() < prob and len(toks) > 3:
        i = random.randrange(0, len(toks) - 1)
        toks[i], toks[i + 1] = toks[i + 1], toks[i]
    # Random synonym replacement
    if random.random() < prob:
        ixs = list(range(len(toks)))
        random.shuffle(ixs)
        for i in ixs:
            base = toks[i].lower().strip(",.?!")
            if base in _SYNONYMS:
                toks[i] = random.choice(_SYNONYMS[base])
                break
    return " ".join(toks)


def augment_dataframe(
    df: pd.DataFrame, repeats: int = 1, prob: float = 0.3
) -> pd.DataFrame:
    if repeats <= 0:
        return df
    aug_rows = []
    for _ in range(repeats):
        q_aug = [augment_question(q, prob) for q in df["question"].astype(str).tolist()]
        aug_rows.append(
            pd.DataFrame(
                {
                    "question": q_aug,
                    "answer": df["answer"].values,
                    "source": df.get("source", "Aug"),
                }
            )
        )
    df_aug = pd.concat([df] + aug_rows, ignore_index=True)
    df_aug.drop_duplicates(subset=["question", "answer"], inplace=True)
    return df_aug


def make_tf_datasets(
    df: pd.DataFrame,
    batch_size: int = 256,
    val_frac: float = 0.05,
    shuffle: int = 10000,
):
    df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)
    n = len(df)
    n_val = max(1, int(n * val_frac))
    df_train = df.iloc[:-n_val]
    df_val = df.iloc[-n_val:]

    train = tf.data.Dataset.from_tensor_slices(
        (df_train["question"].values, df_train["answer"].values)
    )
    val = tf.data.Dataset.from_tensor_slices(
        (df_val["question"].values, df_val["answer"].values)
    )
    # In-batch negatives require aligned pairs; labels are implicit, so dummy zeros
    train = (
        train.shuffle(shuffle, seed=42)
        .batch(batch_size)
        .map(lambda q, a: ((q, a), tf.zeros_like(q)))
    )
    val = val.batch(batch_size).map(lambda q, a: ((q, a), tf.zeros_like(q)))
    return train, val, df_train, df_val


def adapt_vectorizer(encoder: keras.Model, texts: List[str]) -> None:
    # The encoder holds reference to the shared vectorizer
    vectorizer = getattr(encoder, "text_vectorizer")
    assert vectorizer is not None
    vectorizer.adapt(tf.data.Dataset.from_tensor_slices(texts).batch(512))


def save_index(a_encoder: keras.Model, answers: List[str], out_dir: Path) -> None:
    ds = tf.data.Dataset.from_tensor_slices(answers).batch(512)
    embs = []
    for batch in ds:
        embs.append(a_encoder(batch, training=False).numpy())
    emb = np.vstack(embs)
    # Save numpy and metadata
    out_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_dir / "chatbot_index.npz", embeddings=emb)
    meta = {"answers": answers}
    (out_dir / "chatbot_index.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", "-e", type=int, default=8)
    parser.add_argument("--batch-size", "-bs", type=int, default=256)
    parser.add_argument("--vocab", type=int, default=50000)
    parser.add_argument("--seq-len", type=int, default=96)
    parser.add_argument("--temperature", type=float, default=0.05)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument(
        "--augment", action="store_true", help="Enable question augmentation"
    )
    parser.add_argument("--no-augment", dest="augment", action="store_false")
    parser.set_defaults(augment=True)
    parser.add_argument(
        "--aug-repeats",
        type=int,
        default=1,
        help="How many augmented copies per example",
    )
    parser.add_argument(
        "--aug-prob",
        type=float,
        default=0.3,
        help="Probability for each augmentation op",
    )
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    repo_root = script_path.parents[2]
    backend_dir = repo_root / "AGRISENSEFULL-STACK" / "agrisense_app" / "backend"
    if not backend_dir.exists():
        # Alternate layout: we are already inside AGRISENSEFULL-STACK
        backend_dir = script_path.parents[1] / "agrisense_app" / "backend"

    print("Loading datasets...")
    df_all = load_datasets(repo_root)
    print(
        f"Total pairs: {len(df_all)} from sources: {sorted(df_all['source'].unique().tolist())}"
    )

    # Optional augmentation on the question side
    if args.augment:
        random.seed(42)
        df_all = augment_dataframe(
            df_all,
            repeats=max(0, args.aug_repeats),
            prob=max(0.0, min(1.0, args.aug_prob)),
        )

    # Build datasets
    train_ds, val_ds, df_train, df_val = make_tf_datasets(
        df_all, batch_size=args.batch_size
    )

    # Build model
    q_encoder, a_encoder = build_biencoder(vocab_size=args.vocab, seq_len=args.seq_len)
    # Adapt vectorizer on combined corpus (questions + answers)
    corpus = (
        pd.concat([df_train["question"], df_train["answer"]], ignore_index=True)
        .astype(str)
        .tolist()
    )
    print("Adapting vectorizer on corpus...")
    adapt_vectorizer(q_encoder, corpus)

    model = BiEncoderTrainer(q_encoder, a_encoder, temperature=float(args.temperature))
    model.compile(optimizer=keras.optimizers.Adam(float(args.lr), clipnorm=1.0))

    print("Training...")
    callbacks = [
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=2, min_lr=1e-5, verbose=1
        ),
        keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=3, restore_best_weights=True
        ),
    ]
    history = model.fit(
        train_ds, validation_data=val_ds, epochs=args.epochs, callbacks=callbacks
    )
    print(
        {
            k: (float(v[-1]) if isinstance(v, list) else float(v))
            for k, v in history.history.items()
        }
    )

    # Evaluate Recall@K on held-out validation
    def eval_recall_at_k(q_enc, a_enc, df_val: pd.DataFrame, ks=(1, 3, 5, 10)):
        if len(df_val) == 0:
            return {}
        q_vecs = q_enc(tf.constant(df_val["question"].tolist()))
        a_vecs = a_enc(tf.constant(df_val["answer"].tolist()))
        if isinstance(q_vecs, (list, tuple)):
            q_vecs = q_vecs[0]
        if isinstance(a_vecs, (list, tuple)):
            a_vecs = a_vecs[0]
        q = q_vecs.numpy()
        a = a_vecs.numpy()
        sims = q @ a.T
        labels = np.arange(len(df_val))
        metrics = {}
        for k in ks:
            topk = np.argsort(-sims, axis=1)[:, :k]
            hits = (topk == labels[:, None]).any(axis=1).mean()
            metrics[f"recall@{k}"] = float(hits)
        return metrics

    val_metrics = eval_recall_at_k(q_encoder, a_encoder, df_val)
    print({"val": val_metrics})
    # Persist metrics for tracking
    metrics_path = backend_dir / "chatbot_metrics.json"
    try:
        payload = {
            "val": val_metrics,
            "total_pairs": int(len(df_all)),
            "train_pairs": int(len(df_train)),
            "val_pairs": int(len(df_val)),
            "epochs": int(args.epochs),
            "batch_size": int(args.batch_size),
            "vocab": int(args.vocab),
            "seq_len": int(args.seq_len),
        }
        metrics_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Wrote metrics -> {metrics_path}")
    except Exception as e:
        print(f"Failed to write metrics: {e}")

    # Export encoders as standalone models (string -> embedding)
    print("Saving encoders and index...")
    out_dir = backend_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # Freeze vectorizer into the model graph by wrapping call
    def exportable(encoder: keras.Model, name: str) -> keras.Model:
        inp = keras.Input(shape=(), dtype=tf.string, name="text")
        out = encoder(inp)
        return keras.Model(inp, out, name=name)

    q_export = exportable(q_encoder, "chatbot_question_encoder")
    a_export = exportable(a_encoder, "chatbot_answer_encoder")
    # Export as TensorFlow SavedModel directories for robustness
    q_export.export(str(out_dir / "chatbot_question_encoder"))
    a_export.export(str(out_dir / "chatbot_answer_encoder"))

    # Build index on unique answers from full dataset
    answers = df_all["answer"].astype(str).drop_duplicates().tolist()
    save_index(a_export, answers, out_dir)
    print("Done.")


if __name__ == "__main__":
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    main()
