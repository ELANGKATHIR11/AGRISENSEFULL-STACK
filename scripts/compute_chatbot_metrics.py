r"""
Compute chatbot retrieval metrics (Recall@K) using saved encoders and datasets.
No training is performed; this reads datasets, loads SavedModel encoders,
computes embeddings, evaluates Recall@{1,3,5,10}, and writes
agrisense_app/backend/chatbot_metrics.json where the API expects it.

Usage (PowerShell):
    .venv\Scripts\python.exe AGRISENSEFULL-STACK\scripts\compute_chatbot_metrics.py --sample 1000
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.layers import TFSMLayer  # type: ignore


def load_datasets(repo_root: Path) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    # KisanVaani CSV
    kisan_csv = repo_root / "KisanVaani_agriculture_qa.csv"
    if kisan_csv.exists():
        df = pd.read_csv(kisan_csv)
        cols = {c.lower(): c for c in df.columns}
        q = cols.get("question")
        a = cols.get("answer")
        if q and a:
            df = df.rename(columns={q: "question", a: "answer"})[["question", "answer"]]
            df["source"] = "KisanVaani"
            frames.append(df)
    # Soil QA CSV
    soil_csv = (
        repo_root
        / "Agriculture-Soil-QA-Pairs-Dataset"
        / "qna-dataset-farmgenie-soil-v2.csv"
    )
    if soil_csv.exists():
        df = pd.read_csv(soil_csv)
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
        if not mapping and "QUESTION.question" in df.columns and "ANSWER" in df.columns:
            mapping = {"QUESTION.question": "question", "ANSWER": "answer"}
        if mapping:
            df = df.rename(columns=mapping)
            df = df[[c for c in df.columns if not str(c).lower().startswith("unnamed")]]
            if set(["question", "answer"]).issubset(df.columns):
                df = df[["question", "answer"]]
                df["source"] = "SoilQA"
                frames.append(df)
    # Curated CSV
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
    # Farming FAQ assistant CSVs in repo root
    for fname in [
        "Farming_FAQ_Assistant_Dataset.csv",
        "Farming_FAQ_Assistant_Dataset (2).csv",
    ]:
        fpath = repo_root / fname
        if fpath.exists():
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
    # Generic data_core.csv
    data_core = repo_root / "data_core.csv"
    if data_core.exists():
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
    if not frames:
        raise FileNotFoundError(
            "No datasets found. Ensure at least one CSV is present."
        )
    df_all = pd.concat(frames, ignore_index=True)
    df_all["question"] = df_all["question"].astype(str).str.strip()
    df_all["answer"] = df_all["answer"].astype(str).str.strip()
    df_all = df_all[(df_all["question"] != "") & (df_all["answer"] != "")]
    df_all.drop_duplicates(subset=["question", "answer"], inplace=True)
    df_all.drop_duplicates(subset=["question"], inplace=True)
    return df_all


def compute_recall_at_k(
    q_enc: TFSMLayer, a_enc: TFSMLayer, df: pd.DataFrame, ks=(1, 3, 5, 10)
) -> dict:
    if len(df) == 0:
        return {}
    q_vecs = q_enc(tf.constant(df["question"].tolist()))
    a_vecs = a_enc(tf.constant(df["answer"].tolist()))
    if isinstance(q_vecs, (list, tuple)):
        q_vecs = q_vecs[0]
    if isinstance(a_vecs, (list, tuple)):
        a_vecs = a_vecs[0]
    q = q_vecs.numpy()
    a = a_vecs.numpy()
    # Normalize for cosine similarity (encoders should already l2-normalize, but do again for safety)
    q = q / (np.linalg.norm(q, axis=1, keepdims=True) + 1e-12)
    a = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-12)
    sims = q @ a.T
    labels = np.arange(len(df))
    metrics = {}
    for k in ks:
        topk = np.argsort(-sims, axis=1)[:, :k]
        hits = (topk == labels[:, None]).any(axis=1).mean()
        metrics[f"recall@{k}"] = float(hits)
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sample", type=int, default=1000, help="Max pairs to evaluate for speed"
    )
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    repo_root = script_path.parents[2]
    backend_dir = repo_root / "AGRISENSEFULL-STACK" / "agrisense_app" / "backend"
    if not backend_dir.exists():
        backend_dir = script_path.parents[1] / "agrisense_app" / "backend"

    df_all = load_datasets(repo_root)
    # Keep aligned pairs; sample for speed
    df_eval = df_all.sample(
        n=min(args.sample, len(df_all)), random_state=42
    ).reset_index(drop=True)

    qenc_dir = backend_dir / "chatbot_question_encoder"
    aenc_dir = backend_dir / "chatbot_answer_encoder"
    if not (qenc_dir.exists() and aenc_dir.exists()):
        raise FileNotFoundError("Saved encoders not found under backend/")

    q_layer = TFSMLayer(str(qenc_dir), call_endpoint="serve")
    a_layer = TFSMLayer(str(aenc_dir), call_endpoint="serve")

    metrics = compute_recall_at_k(q_layer, a_layer, df_eval)
    payload = {
        "val": metrics,
        "eval_pairs": int(len(df_eval)),
        "total_pairs": int(len(df_all)),
        "note": "Computed from saved encoders without retraining",
    }
    out = backend_dir / "chatbot_metrics.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote metrics -> {out}")


if __name__ == "__main__":
    import os

    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    main()
