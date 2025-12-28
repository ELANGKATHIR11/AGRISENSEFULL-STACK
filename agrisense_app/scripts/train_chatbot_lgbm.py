"""
Train or update the LightGBM re-ranker using available QA data (including augmented paraphrases).

Inputs (auto-discovered if present):
  - agrisense_app/backend/chatbot_augmented_qa.csv (from augment_qa_with_llm.py)
  - agrisense_app/backend/combined_agri_dataset.csv (fallback/general)

Outputs:
  - agrisense_app/backend/chatbot_lgbm_ranker.joblib (overwritten)

Features:
  - TF-IDF cosine similarity between question and answer texts (proxy) and/or question vs. question for pairs
  - Token Jaccard similarity

Labels:
  - Supervision via distant labeling: Original question vs. its own answer considered positive; others sampled as negatives.

Usage (PowerShell):
  .venv\\Scripts\\python.exe agrisense_app\\scripts\\train_chatbot_lgbm.py --limit 6000 --negatives 3
"""

from __future__ import annotations

import argparse
import csv
import os
import random
from typing import List, Tuple

import joblib  # type: ignore
import numpy as np  # type: ignore


def _read_aug_csv(path: str) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            q = (r.get("question") or "").strip()
            a = (r.get("answer") or "").strip()
            if q and a:
                pairs.append((q, a))
    return pairs


def _read_combined_csv(path: str) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        # Heuristic mapping
        lower_cols = [c.lower() for c in (reader.fieldnames or [])]
        q_idx = None
        a_idx = None
        for i, c in enumerate(lower_cols):
            if q_idx is None and c in ("question", "query", "prompt", "text"):
                q_idx = i
            if a_idx is None and c in ("answer", "response", "label"):
                a_idx = i
        if q_idx is None or a_idx is None:
            # fallback: first two columns
            q_idx, a_idx = 0, 1
        for r in reader:
            vals = list(r.values())
            if len(vals) < 2:
                continue
            q = str(vals[q_idx]).strip()
            a = str(vals[a_idx]).strip()
            if q and a:
                pairs.append((q, a))
    return pairs


def _tokenize(s: str) -> List[str]:
    import re

    return [t for t in re.sub(r"[^a-z0-9]+", " ", s.lower()).split() if t]


def _jaccard(a: List[str], b: List[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 0.0
    return len(sa & sb) / float(len(sa | sb))


def _build_pairs(
    pairs: List[Tuple[str, str]], negatives_per_pos: int, limit: int
) -> Tuple[List[str], List[str], np.ndarray]:
    # Build pairwise (query, candidate question) with labels 1 for true source question, 0 for negatives
    queries: List[str] = []
    cands: List[str] = []
    labels: List[int] = []

    pool_q = [q for q, _ in pairs]
    for i, (q, a) in enumerate(pairs[:limit]):
        # Positive: (q, q)
        queries.append(q)
        cands.append(q)
        labels.append(1)
        # Negatives: sample random different questions
        for _ in range(negatives_per_pos):
            neg = q
            tries = 0
            while neg == q and tries < 10:
                neg = random.choice(pool_q)
                tries += 1
            queries.append(q)
            cands.append(neg)
            labels.append(0)
    return queries, cands, np.array(labels, dtype=np.int32)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--aug_csv",
        default=os.path.join(
            "AGRISENSEFULL-STACK",
            "agrisense_app",
            "backend",
            "chatbot_augmented_qa.csv",
        ),
    )
    parser.add_argument(
        "--combined_csv",
        default=os.path.join(
            "AGRISENSEFULL-STACK",
            "agrisense_app",
            "backend",
            "combined_agri_dataset.csv",
        ),
    )
    parser.add_argument(
        "--out_bundle",
        default=os.path.join(
            "AGRISENSEFULL-STACK",
            "agrisense_app",
            "backend",
            "chatbot_lgbm_ranker.joblib",
        ),
    )
    parser.add_argument("--limit", type=int, default=6000)
    parser.add_argument("--negatives", type=int, default=3)
    args = parser.parse_args()

    data_pairs: List[Tuple[str, str]] = []
    if os.path.isfile(args.aug_csv):
        print(f"[lgbm] Loading augmented QA from {args.aug_csv}")
        data_pairs.extend(_read_aug_csv(args.aug_csv))
    if os.path.isfile(args.combined_csv):
        print(f"[lgbm] Loading combined dataset from {args.combined_csv}")
        data_pairs.extend(_read_combined_csv(args.combined_csv))
    if not data_pairs:
        print("[lgbm] No training data found. Aborting.")
        return

    random.shuffle(data_pairs)
    print(f"[lgbm] Total QA pairs: {len(data_pairs)}")

    # Build pairwise training examples (query, candidate question) with labels
    queries, cands, labels = _build_pairs(data_pairs, args.negatives, args.limit)
    print(f"[lgbm] Built {len(labels)} pairwise examples")

    # Vectorize with TF-IDF
    from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
    from sklearn.model_selection import train_test_split  # type: ignore
    from lightgbm import LGBMClassifier  # type: ignore

    vectorizer = TfidfVectorizer(min_df=2, max_features=50000, ngram_range=(1, 2))
    Xq = vectorizer.fit_transform(queries)
    Xc = vectorizer.transform(cands)

    # Cosine similarity between query and candidate question in TF-IDF space
    # sim = (Xq * Xc.T).diagonal() / (||Xq|| * ||Xc||); but for speed, use row-wise norms
    import numpy as np

    def _row_norms(mat):
        return np.sqrt(mat.multiply(mat).sum(axis=1)).A1 + 1e-12

    nq = _row_norms(Xq)
    nc = _row_norms(Xc)
    dot = (Xq.multiply(Xc)).sum(axis=1).A1  # type: ignore
    tfidf_cos = dot / (nq * nc)

    # Token Jaccard
    toks_q = [_tokenize(s) for s in queries]
    toks_c = [_tokenize(s) for s in cands]
    jacc = np.array([_jaccard(a, b) for a, b in zip(toks_q, toks_c)], dtype=np.float32)

    # Assemble feature matrix
    X = np.vstack([tfidf_cos, jacc]).T.astype(np.float32)
    y = labels.astype(np.int32)

    Xtr, Xva, ytr, yva = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = LGBMClassifier(
        n_estimators=400,
        max_depth=-1,
        learning_rate=0.05,
        num_leaves=63,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
        n_jobs=-1,
    )

    # Early stopping via callbacks in sklearn API
    callbacks = []
    try:
        import lightgbm as lgb  # type: ignore

        callbacks = [lgb.early_stopping(stopping_rounds=40, verbose=False)]
    except Exception:
        pass

    clf.fit(Xtr, ytr, eval_set=[(Xva, yva)], callbacks=callbacks)

    bundle = {
        "model": clf,
        "vectorizer": vectorizer,
        "features": ["tfidf_cos", "jaccard"],
        "version": 1,
    }

    out_dir = os.path.dirname(args.out_bundle)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    joblib.dump(bundle, args.out_bundle)
    print(f"[lgbm] Saved bundle to {args.out_bundle}")


if __name__ == "__main__":
    main()
