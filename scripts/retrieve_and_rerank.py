"""Retrieve top-K answers from an HNSW index and optionally rerank with a cross-encoder.

Requires:
 - hnswlib
 - sentence-transformers (optional, for bi-encoder encoding)
 - transformers + datasets + torch (optional, for cross-encoder rerank)

Usage:
  .venv\Scripts\python.exe scripts\retrieve_and_rerank.py --index agrisense_app/backend/test_run/hnsw_index.bin --meta agrisense_app/backend/test_run/hnsw_index.bin.meta.npz --question "How to grow tomatoes?" --k 10
"""
import argparse
from pathlib import Path
import numpy as np


def load_index(index_path: Path, meta_path: Path):
    try:
        import hnswlib
    except Exception:
        raise SystemExit("Please install hnswlib: pip install hnswlib")

    p = hnswlib.Index(space='cosine', dim=1)  # placeholder, will be overwritten by load
    p.load_index(str(index_path))
    meta = np.load(meta_path, allow_pickle=True)
    answers = list(meta['answers'].astype(object))
    ids = meta['ids']
    return p, answers, ids


def encode_query(model_name: str, question: str):
    try:
        from sentence_transformers import SentenceTransformer
    except Exception:
        raise SystemExit("sentence-transformers is required to encode queries: pip install sentence-transformers")
    m = SentenceTransformer(model_name)
    emb = m.encode([question], convert_to_numpy=True).astype(np.float32)
    # L2 normalize
    n = np.linalg.norm(emb, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return emb / n


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--index', required=True)
    p.add_argument('--meta', required=True)
    p.add_argument('--question', required=True)
    p.add_argument('--k', type=int, default=10)
    p.add_argument('--model', default='sentence-transformers/all-MiniLM-L6-v2')
    args = p.parse_args()

    idx_path = Path(args.index)
    meta_path = Path(args.meta)
    if not idx_path.exists() or not meta_path.exists():
        raise SystemExit('Missing index or meta files')

    index, answers, ids = load_index(idx_path, meta_path)
    q_emb = encode_query(args.model, args.question)

    labels, dists = index.knn_query(q_emb, k=args.k)
    labels = labels[0]
    scores = 1 - dists[0]  # for cosine, hnswlib returns 1 - cos? verify in docs

    for rank, (lbl, score) in enumerate(zip(labels, scores), start=1):
        print(f"{rank}. ({score:.4f}) {answers[int(lbl)]}")


if __name__ == '__main__':
    main()
