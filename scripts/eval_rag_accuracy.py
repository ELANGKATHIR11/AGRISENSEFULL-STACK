import json
import time
from pathlib import Path

import faiss  # type: ignore
import numpy as np  # type: ignore
import pandas as pd  # type: ignore
from sentence_transformers import SentenceTransformer  # type: ignore


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    storage = repo / "qa_rag_workspace" / "storage"
    csv_path = repo / "qa_rag_workspace" / "data" / "dataset.csv"

    if not storage.exists():
        raise SystemExit(f"Storage not found: {storage}")
    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    model_name = (storage / "model_name.txt").read_text(encoding="utf-8").strip()
    index = faiss.read_index(str(storage / "index.faiss"))
    with open(storage / "meta.json", "r", encoding="utf-8") as f:
        meta = json.load(f)

    df = pd.read_csv(csv_path)
    questions = df["question"].astype(str).tolist()

    encoder = SentenceTransformer(model_name)
    B = 256
    vecs = []
    t0 = time.time()
    for i in range(0, len(questions), B):
        batch = questions[i : i + B]
        v = encoder.encode(
            batch, convert_to_numpy=True, normalize_embeddings=True
        ).astype("float32")
        vecs.append(v)
    qmat = np.vstack(vecs)

    # Top-1 and Top-5 recall against meta rows
    D1, I1 = index.search(qmat, 1)
    D5, I5 = index.search(qmat, 5)

    top1 = 0
    top5 = 0
    mismatches = []
    for j in range(len(questions)):
        q = questions[j].strip()
        # top-1
        i1 = int(I1[j][0])
        m1 = str(meta[i1].get("question", "")).strip()
        if m1 == q:
            top1 += 1
        else:
            mismatches.append((j, q[:80], m1[:80]))
        # top-5
        if any(str(meta[int(k)].get("question", "")).strip() == q for k in I5[j]):
            top5 += 1

    t = time.time() - t0
    total = len(questions)
    out = {
        "total_rows": total,
        "top1_exact_match": top1,
        "top1_acc_pct": round(top1 / total * 100, 2),
        "top5_recall_pct": round(top5 / total * 100, 2),
        "encode_search_time_s": round(t, 1),
    }
    print(out)
    if mismatches:
        print("examples:", mismatches[:5])


if __name__ == "__main__":
    main()
