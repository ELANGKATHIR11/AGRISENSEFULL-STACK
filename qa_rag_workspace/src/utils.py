import json, os
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

def load_encoder(model_name: str):
    return SentenceTransformer(model_name)

def build_embeddings(encoder, texts: List[str]) -> np.ndarray:
    # L2-normalized float32 for cosine via inner product
    embs = encoder.encode(texts, convert_to_numpy=True, normalize_embeddings=True).astype("float32")
    return embs

def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatIP:
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # cosine similarity (on normalized vectors)
    index.add(embeddings)
    return index

def save_index(index: faiss.Index, path: str):
    faiss.write_index(index, path)

def load_index(path: str) -> faiss.Index:
    return faiss.read_index(path)

def save_meta(meta: List[Dict[str, Any]], path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

def load_meta(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)