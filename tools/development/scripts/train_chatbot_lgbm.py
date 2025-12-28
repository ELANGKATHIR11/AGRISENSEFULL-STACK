"""
Train a LightGBM ranker on top of simple NLP features (TF-IDF + cosine + Jaccard)
using all available QA datasets. Saves a model to backend for optional re-ranking.

Usage (PowerShell):
  .venv\\Scripts\\python.exe AGRISENSEFULL-STACK\\scripts\\train_chatbot_lgbm.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics.pairwise import cosine_similarity
import lightgbm as lgb
import joblib


def load_datasets(repo_root: Path) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    # KisanVaani
    kv = repo_root / "KisanVaani_agriculture_qa.csv"
    if kv.exists():
        df = pd.read_csv(kv)
        cols = {c.lower(): c for c in df.columns}
        q, a = cols.get("question"), cols.get("answer")
        if q and a:
            df = df.rename(columns={q: "question", a: "answer"})[["question", "answer"]]
            df["source"] = "KisanVaani"
            frames.append(df)
    # Soil QA
    soil = (
        repo_root
        / "Agriculture-Soil-QA-Pairs-Dataset"
        / "qna-dataset-farmgenie-soil-v2.csv"
    )
    if soil.exists():
        df = pd.read_csv(soil)
        mapping = {}
        for c in df.columns:
            cl = str(c).lower().strip()
            if cl in (
                "question",
                "question.question",
                "questions",
                "q",
                "question_text",
            ):
                mapping[c] = "question"
            elif cl in ("answer", "answers", "a"):
                mapping[c] = "answer"
        if not mapping and "QUESTION.question" in df.columns and "ANSWER" in df.columns:
            mapping = {"QUESTION.question": "question", "ANSWER": "answer"}
        if mapping:
            df = df.rename(columns=mapping)
            df = df[[c for c in df.columns if not str(c).lower().startswith("unnamed")]]
            if set(["question", "answer"]).issubset(df.columns):
                df = df[["question", "answer"]]
                df["source"] = "SoilQA"
                frames.append(df)
    # Curated
    curated = Path("D:/downloads/agrisense_chatbot_dataset.csv")
    if curated.exists():
        df = pd.read_csv(curated)
        cols = {c.lower(): c for c in df.columns}
        q, a = cols.get("question"), cols.get("answer")
        if q and a:
            df = df.rename(columns={q: "question", a: "answer"})[["question", "answer"]]
            df["source"] = "Curated"
            frames.append(df)
    # Farming FAQ
    for fname in [
        "Farming_FAQ_Assistant_Dataset.csv",
        "Farming_FAQ_Assistant_Dataset (2).csv",
    ]:
        p = repo_root / fname
        if p.exists():
            try:
                df = pd.read_csv(p)
                cols = {str(c).strip().lower(): c for c in df.columns}
                q, a = cols.get("question"), cols.get("answer")
                if q and a:
                    df = df.rename(columns={q: "question", a: "answer"})[
                        ["question", "answer"]
                    ]
                    df["source"] = "FarmingFAQ"
                    frames.append(df)
            except Exception:
                pass
    # data_core.csv
    dc = repo_root / "data_core.csv"
    if dc.exists():
        try:
            df = pd.read_csv(dc)
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
        raise FileNotFoundError("No datasets found for LightGBM training")
    df = pd.concat(frames, ignore_index=True)
    df["question"] = df["question"].astype(str).str.strip()
    df["answer"] = df["answer"].astype(str).str.strip()
    df = df[(df["question"] != "") & (df["answer"] != "")]
    df.drop_duplicates(subset=["question", "answer"], inplace=True)
    df.drop_duplicates(subset=["question"], inplace=True)
    return df


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))


def main() -> None:
    script_path = Path(__file__).resolve()
    repo_root = script_path.parents[2]
    backend_dir = repo_root / "AGRISENSEFULL-STACK" / "agrisense_app" / "backend"
    if not backend_dir.exists():
        backend_dir = script_path.parents[1] / "agrisense_app" / "backend"

    df = load_datasets(repo_root)
    # Build a corpus of answers to rank
    answers = df["answer"].tolist()
    # TF-IDF on answers
    vec = TfidfVectorizer(max_features=80000, ngram_range=(1, 2), lowercase=True)
    a_mat = vec.fit_transform(answers)

    # Create supervised pairs: positive is (q, its own answer), negatives are sampled others
    pairs: List[Tuple[str, str, int]] = []
    rng = np.random.default_rng(42)
    for i, row in df.iterrows():
        q = row["question"]
        a_pos = row["answer"]
        pairs.append((q, a_pos, 1))
        # sample 3 negatives
        neg_idx = rng.choice(len(df), size=3, replace=False)
        for j in neg_idx:
            if j == i:
                continue
            pairs.append((q, answers[j], 0))

    pq, pa, y = zip(*pairs)
    # Features
    q_mat = vec.transform(pq)
    pa_mat = vec.transform(pa)
    # Cosine sim in TF-IDF space
    cos = (q_mat.multiply(pa_mat)).sum(axis=1)  # type: ignore
    cos = np.asarray(cos).ravel().astype(np.float32)

    # Jaccard on tokens (cheap proxy for lexical overlap)
    def toks(s: str) -> set[str]:
        return set("".join(ch if ch.isalnum() else " " for ch in s.lower()).split())

    jac = np.array(
        [jaccard(toks(q), toks(a)) for q, a in zip(pq, pa)], dtype=np.float32
    )
    X = np.vstack([cos, jac]).T
    y_arr = np.array(y, dtype=np.int32)

    X_train, X_val, y_train, y_val = train_test_split(
        X, y_arr, test_size=0.1, random_state=42
    )
    dtrain = lgb.Dataset(X_train, label=y_train)
    dval = lgb.Dataset(X_val, label=y_val, reference=dtrain)

    params = {
        "objective": "binary",
        "metric": ["auc"],
        "learning_rate": 0.05,
        "num_leaves": 63,
        "feature_fraction": 0.9,
        "bagging_fraction": 0.8,
        "bagging_freq": 1,
        "verbose": -1,
    }
    booster = lgb.train(
        params,
        dtrain,
        num_boost_round=500,
        valid_sets=[dtrain, dval],
        valid_names=["train", "val"],
        callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)],
    )

    out_dir = backend_dir
    joblib.dump(
        {
            "model": booster,
            "vectorizer": vec,
        },
        out_dir / "chatbot_lgbm_ranker.joblib",
    )
    print(f"Saved LightGBM ranker -> {out_dir / 'chatbot_lgbm_ranker.joblib'}")


if __name__ == "__main__":
    main()
