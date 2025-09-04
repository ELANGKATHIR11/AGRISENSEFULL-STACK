import argparse, os
import pandas as pd
from .utils import load_encoder, build_embeddings, build_faiss_index, save_index, save_meta

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def main():
    parser = argparse.ArgumentParser(description="Build FAISS index for RAG chatbot from a CSV dataset.")
    parser.add_argument("--csv", required=True, help="Path to CSV with columns like question, answer, ...")
    parser.add_argument("--text-cols", nargs="+", default=["question", "answer"], help="Columns to concatenate for retrieval.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="SentenceTransformer model name.")
    parser.add_argument("--storage", default="storage", help="Directory to save index and metadata.")
    args = parser.parse_args()

    os.makedirs(args.storage, exist_ok=True)

    df = pd.read_csv(args.csv)
    for col in args.text_cols:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in CSV. Available: {list(df.columns)}")

    combined_text = df[args.text_cols].astype(str).agg(' | '.join, axis=1).tolist()

    encoder = load_encoder(args.model)
    embs = build_embeddings(encoder, combined_text)

    index = build_faiss_index(embs)

    index_path = os.path.join(args.storage, "index.faiss")
    save_index(index, index_path)

    meta = df.to_dict(orient="records")
    meta_path = os.path.join(args.storage, "meta.json")
    save_meta(meta, meta_path)

    with open(os.path.join(args.storage, "model_name.txt"), "w", encoding="utf-8") as f:
        f.write(args.model)

    print(f"✅ Indexed {len(df)} rows")
    print(f"🗂  Saved index to: {index_path}")
    print(f"📝 Saved meta to:  {meta_path}")
    print(f"🔤 Model: {args.model}")

if __name__ == "__main__":
    main()