"""Build an HNSW (approximate nearest neighbor) index from chatbot_index.npz.

This script requires `hnswlib` (pip install hnswlib). On Windows that package
usually has wheels available.

Usage:
  .venv\Scripts\python.exe scripts\build_hnsw_index.py --dir agrisense_app/backend/test_run --out agrisense_app/backend/test_run/hnsw_index.bin

Outputs:
 - {out}  (binary hnsw index file)
 - {out}.meta.npz (contains 'answers' array and 'ids')
"""
import argparse
from pathlib import Path
import numpy as np


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dir", required=True, help="Directory containing chatbot_index.npz")
    p.add_argument("--out", required=True, help="Output index file path (.bin)")
    p.add_argument("--space", default="cosine", help="Distance space: 'l2' or 'cosine'")
    p.add_argument("--ef_construction", type=int, default=200)
    p.add_argument("--M", type=int, default=16)
    args = p.parse_args()

    src = Path(args.dir)
    idx_npz = src / "chatbot_index.npz"
    if not idx_npz.exists():
        raise SystemExit(f"Missing {idx_npz}; run build_chatbot_artifacts or train script first")

    data = np.load(idx_npz, allow_pickle=True)
    emb = data["embeddings"].astype(np.float32)
    answers = list(data["answers"].astype(object))

    try:
        import hnswlib
    except Exception as e:
        raise SystemExit(
            "hnswlib is required but not installed. Install with: pip install hnswlib"
            + f"\nOriginal error: {e}"
        )

    num_elements, dim = emb.shape
    print(f"Building HNSW index: n={num_elements}, dim={dim}, space={args.space}")

    p = hnswlib.Index(space=args.space, dim=dim)
    p.init_index(max_elements=num_elements, ef_construction=args.ef_construction, M=args.M)
    ids = np.arange(num_elements)
    p.add_items(emb, ids)
    p.set_ef(50)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    print("Saving index to", out_path)
    p.save_index(str(out_path))

    meta_path = out_path.with_suffix(out_path.suffix + ".meta.npz")
    print("Saving meta to", meta_path)
    np.savez_compressed(meta_path, answers=np.array(answers, dtype=object), ids=ids)

    print("HNSW index build complete.")


if __name__ == '__main__':
    main()
