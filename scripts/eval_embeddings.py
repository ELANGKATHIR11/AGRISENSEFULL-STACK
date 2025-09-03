"""Evaluate question->answer retrieval metrics from NPZ artifacts.

Usage:
    Use your venv Python to run this script, for example:
        .venv/Scripts/python.exe scripts/eval_embeddings.py --dir agrisense_app/backend/test_run

This script loads `chatbot_q_index.npz` and `chatbot_index.npz` from the provided
directory, computes cosine similarity (dot product if vectors are L2-normalized),
and prints recall@1/5/10 and MRR.
"""
import argparse
import numpy as np
from pathlib import Path


def load_npz(path: Path):
    data = np.load(path, allow_pickle=True)
    return data


def compute_metrics(q_embs, a_embs, questions, answers, ks=(1,5,10)):
    # assume embeddings are L2-normalized -> cosine similarity = dot
    sims = np.matmul(q_embs, a_embs.T)
    n = sims.shape[0]

    ranks = np.argsort(-sims, axis=1)

    recall_at_k = {}
    for k in ks:
        hits = 0
        for i in range(n):
            topk = ranks[i, :k]
            # check if the exact answer string appears in topk
            if any(answers[j] == answers[i] for j in topk):
                hits += 1
        recall_at_k[k] = hits / n

    # MRR
    rr_sum = 0.0
    for i in range(n):
        rank_list = ranks[i]
        # find first position where answer matches
        found = None
        for pos, idx in enumerate(rank_list, start=1):
            if answers[idx] == answers[i]:
                found = pos
                break
        if found is None:
            rr = 0.0
        else:
            rr = 1.0 / found
        rr_sum += rr
    mrr = rr_sum / n

    return recall_at_k, mrr


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dir", default="agrisense_app/backend/test_run")
    args = p.parse_args()

    out = Path(args.dir)
    q_npz = out / "chatbot_q_index.npz"
    a_npz = out / "chatbot_index.npz"

    if not q_npz.exists() or not a_npz.exists():
        raise SystemExit(f"Missing artifacts in {out}. Expected: {q_npz}, {a_npz}")

    qd = load_npz(q_npz)
    ad = load_npz(a_npz)

    q_embs = qd["embeddings"].astype(np.float32)
    a_embs = ad["embeddings"].astype(np.float32)

    questions = list(qd.get("questions", []))
    answers = list(ad.get("answers", []))

    if len(questions) != q_embs.shape[0] or len(answers) != a_embs.shape[0]:
        print("Warning: length mismatch between texts and embeddings")

    recall, mrr = compute_metrics(q_embs, a_embs, questions, answers)

    print("Evaluation results:")
    for k, v in recall.items():
        print(f"  recall@{k}: {v:.4f}")
    print(f"  MRR: {mrr:.4f}")


if __name__ == '__main__':
    main()
