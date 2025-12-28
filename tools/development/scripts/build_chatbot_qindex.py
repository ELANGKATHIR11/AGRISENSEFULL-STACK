"""
Build a question-side index for the chatbot from available QA CSVs.
This improves matching user questions to known dataset questions and returns
the aligned dataset answers directly.

Outputs (under backend):
- chatbot_q_index.npz (embeddings for questions)
- chatbot_qa_pairs.json (questions + answers arrays in the same order)

Usage (PowerShell):
  .venv\\Scripts\\python.exe AGRISENSEFULL-STACK\\scripts\\build_chatbot_qindex.py --sample 5000
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import List
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.layers import TFSMLayer  # type: ignore


def load_datasets(repo_root: Path) -> pd.DataFrame:
    # Reuse logic similar to train_chatbot.py/compute_chatbot_metrics.py but minimal
    frames: List[pd.DataFrame] = []
    roots = [repo_root, repo_root / "AGRISENSEFULL-STACK"]
    # KisanVaani
    for r in roots:
        f = r / "KisanVaani_agriculture_qa.csv"
        if f.exists():
            df = pd.read_csv(f)
            cols = {c.lower(): c for c in df.columns}
            q = cols.get("question")
            a = cols.get("answer")
            if q and a:
                frames.append(
                    df.rename(columns={q: "question", a: "answer"})[
                        ["question", "answer"]
                    ]
                )
            break
    # Soil QA
    for r in roots:
        f = (
            r
            / "Agriculture-Soil-QA-Pairs-Dataset"
            / "qna-dataset-farmgenie-soil-v2.csv"
        )
        if f.exists():
            df = pd.read_csv(f)
            mapping = {}
            for col in df.columns:
                cl = str(col).strip().lower()
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
            if (
                not mapping
                and "QUESTION.question" in df.columns
                and "ANSWER" in df.columns
            ):
                mapping = {"QUESTION.question": "question", "ANSWER": "answer"}
            if mapping:
                df = df.rename(columns=mapping)
                df = df[
                    [c for c in df.columns if not str(c).lower().startswith("unnamed")]
                ]
                if set(["question", "answer"]).issubset(df.columns):
                    frames.append(df[["question", "answer"]])
            break
    # Farming FAQ
    for fname in (
        "Farming_FAQ_Assistant_Dataset.csv",
        "Farming_FAQ_Assistant_Dataset (2).csv",
    ):
        for r in roots:
            f = r / fname
            if f.exists():
                try:
                    df = pd.read_csv(f)
                    cols = {str(c).strip().lower(): c for c in df.columns}
                    q = cols.get("question")
                    a = cols.get("answer")
                    if q and a:
                        frames.append(
                            df.rename(columns={q: "question", a: "answer"})[
                                ["question", "answer"]
                            ]
                        )
                except Exception:
                    pass
    # data_core.csv
    for r in roots:
        f = r / "data_core.csv"
        if f.exists():
            try:
                df = pd.read_csv(f)
                cols = {str(c).strip().lower(): c for c in df.columns}
                q = cols.get("question") or cols.get("questions") or cols.get("q")
                a = cols.get("answer") or cols.get("answers") or cols.get("a")
                if q and a:
                    frames.append(
                        df.rename(columns={q: "question", a: "answer"})[
                            ["question", "answer"]
                        ]
                    )
            except Exception:
                pass
    if not frames:
        raise FileNotFoundError("No QA datasets found to build question index.")
    df = pd.concat(frames, ignore_index=True)
    df["question"] = df["question"].astype(str).str.strip()
    df["answer"] = df["answer"].astype(str).str.strip()
    df = df[(df["question"] != "") & (df["answer"] != "")]
    df.drop_duplicates(subset=["question", "answer"], inplace=True)
    df.drop_duplicates(subset=["question"], inplace=True)
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sample", type=int, default=0, help="Optional cap on number of QA pairs"
    )
    args = parser.parse_args()

    script = Path(__file__).resolve()
    repo_root = script.parents[2]
    backend = repo_root / "AGRISENSEFULL-STACK" / "agrisense_app" / "backend"
    if not backend.exists():
        backend = script.parents[1] / "agrisense_app" / "backend"

    qenc_dir = backend / "chatbot_question_encoder"
    if not qenc_dir.exists():
        raise FileNotFoundError(
            "chatbot_question_encoder SavedModel not found; run train_chatbot.py first"
        )

    print("Loading QA datasets...")
    df = load_datasets(repo_root)
    if args.sample and args.sample > 0:
        df = df.sample(n=min(args.sample, len(df)), random_state=42).reset_index(
            drop=True
        )
    print(f"Pairs: {len(df)}")

    q_layer = TFSMLayer(str(qenc_dir), call_endpoint="serve")
    ds = tf.data.Dataset.from_tensor_slices(df["question"].astype(str).tolist()).batch(
        512
    )
    embs: List[np.ndarray] = []  # type: ignore[name-defined]
    for batch in ds:
        vec = q_layer(batch)
        if isinstance(vec, (list, tuple)):
            vec = vec[0]
        embs.append(vec.numpy())
    q_emb = np.vstack(embs)
    # l2 normalize
    q_emb = q_emb / (np.linalg.norm(q_emb, axis=1, keepdims=True) + 1e-12)

    np.savez_compressed(backend / "chatbot_q_index.npz", embeddings=q_emb)
    (backend / "chatbot_qa_pairs.json").write_text(
        json.dumps(
            {"questions": df["question"].tolist(), "answers": df["answer"].tolist()},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print("Wrote chatbot_q_index.npz and chatbot_qa_pairs.json")


if __name__ == "__main__":
    import os

    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    main()
