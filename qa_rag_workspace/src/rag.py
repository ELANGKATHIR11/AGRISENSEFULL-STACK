import os
from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

# Support both package-relative and direct file loading
try:
    from .utils import load_index, load_meta  # type: ignore
except Exception:
    # Fallback: import utils.py by path when this module is loaded via importlib.util.spec_from_file_location
    import importlib.util as _importlib_util  # type: ignore
    import pathlib as _pathlib  # type: ignore

    _utils_path = _pathlib.Path(__file__).resolve().parent / "utils.py"
    _spec = _importlib_util.spec_from_file_location("qa_rag_utils", str(_utils_path))
    if _spec is None or _spec.loader is None:
        raise
    _mod = _importlib_util.module_from_spec(_spec)  # type: ignore[arg-type]
    _spec.loader.exec_module(_mod)  # type: ignore
    load_index = getattr(_mod, "load_index")
    load_meta = getattr(_mod, "load_meta")

STORAGE_DIR = os.environ.get("RAG_STORAGE_DIR", "storage")


class Retriever:
    def __init__(self, index_path: str, meta_path: str, model_name: str):
        self.index = load_index(index_path)
        self.meta = load_meta(meta_path)
        self.encoder = SentenceTransformer(model_name)

    def search(self, query: str, top_k: int = 3) -> List[Tuple[float, Dict[str, Any]]]:
        q_vec = self.encoder.encode(
            [query], convert_to_numpy=True, normalize_embeddings=True
        ).astype("float32")
        D, I = self.index.search(q_vec, top_k)
        hits = []
        for score, idx in zip(D[0], I[0]):
            row = self.meta[int(idx)]
            hits.append((float(score), row))
        return hits


def synthesize_answer(query: str, hits: List[Tuple[float, Dict[str, Any]]]) -> str:
    """
    If OPENAI_API_KEY is set, combine retrieved rows into a concise answer with the OpenAI API.
    Otherwise, fallback to best row's 'answer' field.
    """
    key = os.environ.get("OPENAI_API_KEY")
    if not key or len(hits) == 0:
        # Fallback: return best answer directly
        return (
            hits[0][1].get("answer", "Sorry, I couldn't find an answer.")
            if hits
            else "No results."
        )
    try:
        from openai import OpenAI

        client = OpenAI(api_key=key)
        context_blocks = []
        for score, row in hits:
            ctx = []
            if "question" in row:
                ctx.append(f"Q: {row['question']}")
            if "answer" in row:
                ctx.append(f"A: {row['answer']}")
            for k, v in row.items():
                if k not in ("question", "answer") and isinstance(v, str) and v:
                    ctx.append(f"{k}: {v}")
            context_blocks.append("\n".join(ctx))
        context = "\n\n---\n\n".join(context_blocks)
        prompt = f"""You are a helpful agriculture and general Q/A assistant.
Use the CONTEXT to answer the USER QUESTION succinctly in 2-4 sentences. If the answer is in a row, prefer its 'answer' field.
If unsure, say you don't have enough info.

USER QUESTION:
{query}

CONTEXT:
{context}
"""
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        # On any failure, fallback
        return (
            hits[0][1].get("answer", "Sorry, I couldn't find an answer.")
            if hits
            else "No results."
        )
