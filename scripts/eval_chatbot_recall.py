"""Evaluate retrieval recall@k using saved chatbot artifacts.

Loads `agrisense_app/backend/chatbot_q_index.npz` and `agrisense_app/backend/chatbot_index.npz`.
Computes cosine similarity (assumes embeddings are L2-normalized) and reports recall@1/3/5/10.
Also prints a few sample queries and their top answers.
"""
import numpy as np
from pathlib import Path


def load_artifacts(base_dir: Path):
    q_npz = base_dir / "chatbot_q_index.npz"
    idx_npz = base_dir / "chatbot_index.npz"
    if not q_npz.exists() or not idx_npz.exists():
        raise SystemExit("Artifacts not found in %s" % base_dir)
    with np.load(q_npz, allow_pickle=True) as dq:
        q_emb = dq["embeddings"]
        q_texts = dq["questions"].tolist()
    with np.load(idx_npz, allow_pickle=True) as da:
        a_emb = da["embeddings"]
        a_texts = da["answers"].tolist()
    return q_emb, q_texts, a_emb, a_texts


def recall_at_k(q_emb, a_emb, k_values=(1, 3, 5, 10)):
    # assume rows are L2-normalized -> cosine = dot
    sims = q_emb @ a_emb.T
    n = sims.shape[0]
    recalls = {}
    # For each k, compute fraction where correct answer index (i) is in top-k for query i
    for k in k_values:
        count = 0
        for i in range(n):
            topk = np.argsort(-sims[i])[:k]
            if i in topk:
                count += 1
        recalls[k] = count / n
    return recalls


def sample_queries(q_texts, a_texts, sims, n=5):
    n_q = len(q_texts)
    import random
    for _ in range(n):
        i = random.randrange(n_q)
        row = sims[i]
        top_idx = np.argsort(-row)[:5]
        print("\nQuery:", q_texts[i])
        print("Expected answer (excerpt):", (a_texts[i][:200] + '...') if a_texts[i] else "(empty)")
        for r, idx in enumerate(top_idx, start=1):
            ans_excerpt = (a_texts[idx][:200] + '...') if a_texts[idx] else '(empty)'
            print(f"  Rank {r}: (idx={idx}) score={row[idx]:.4f} -> {ans_excerpt}")


def main():
    base = Path("agrisense_app/backend")
    q_emb, q_texts, a_emb, a_texts = load_artifacts(base)
    print("Loaded q_emb.shape=", q_emb.shape, "a_emb.shape=", a_emb.shape)
    # compute sims
    sims = q_emb @ a_emb.T
    recalls = recall_at_k(q_emb, a_emb, k_values=(1, 3, 5, 10))
    print("Recall@k:")
    for k, v in recalls.items():
        print(f"  @{k}: {v:.4f}")

    print("\nSample queries and top-5 answers:")
    sample_queries(q_texts, a_texts, sims, n=6)


if __name__ == '__main__':
    main()
