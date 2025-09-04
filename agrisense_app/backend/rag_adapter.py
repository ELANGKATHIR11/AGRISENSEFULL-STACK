import os
from pathlib import Path
import importlib.util
from typing import List, Dict, Any


def _load_rag_module():
    # Locate the qa_rag_workspace/src/rag.py relative to the repo root
    repo_root = Path(__file__).resolve().parents[2]
    rag_path = repo_root / "qa_rag_workspace" / "src" / "rag.py"
    if not rag_path.exists():
        raise FileNotFoundError(f"RAG source not found at {rag_path}")
    spec = importlib.util.spec_from_file_location("qa_rag_rag", str(rag_path))
    rag_mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(rag_mod)  # type: ignore
    return rag_mod


class RAGService:
    """Lightweight adapter around the RAG Retriever + synthesize_answer.

    Loads the QA Retriever implementation from `qa_rag_workspace/src/rag.py`
    using importlib. Uses env var `RAG_STORAGE_DIR` or the workspace default
    to locate index/meta/model_name files.
    """

    def __init__(self):
        self._mod = None
        self._retriever = None

    def _ensure_loaded(self):
        if self._mod is None:
            self._mod = _load_rag_module()
        if self._retriever is None:
            storage = os.environ.get(
                "RAG_STORAGE_DIR",
                str(Path(__file__).resolve().parents[2] / "qa_rag_workspace" / "storage"),
            )
            storage_path = Path(storage)
            index_path = str(storage_path / "index.faiss")
            meta_path = str(storage_path / "meta.json")
            model_name_file = storage_path / "model_name.txt"
            if model_name_file.exists():
                model_name = model_name_file.read_text(encoding="utf-8").strip()
            else:
                # fallback to a reasonable SentenceTransformer model
                model_name = "sentence-transformers/all-MiniLM-L6-v2"
            # Instantiate the Retriever
            self._retriever = self._mod.Retriever(index_path, meta_path, model_name)

    def ask(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        self._ensure_loaded()
        hits = self._retriever.search(query, top_k=top_k)
        # Prefer an LLM synthesis when the RAG synthesize_answer helper is available
        ans = None
        try:
            ans = self._mod.synthesize_answer(query, hits)
        except Exception:
            # graceful fallback to first hit answer
            if hits:
                ans = hits[0][1].get("answer", "No result")
            else:
                ans = "No result"

        sources: List[str] = []
        for score, row in hits:
            src = None
            for k in ("source", "file", "id", "dataset", "source_url"):
                if isinstance(row.get(k, None), str) and row.get(k):
                    src = row.get(k)
                    break
            if not src:
                # attempt to use any string-like metadata
                for k, v in row.items():
                    if k in ("question", "answer"):
                        continue
                    if isinstance(v, str) and v:
                        src = v
                        break
            if src and src not in sources:
                sources.append(str(src))

        return {"answer": ans, "sources": sources}


# Module-level lazy service
_RAG_SERVICE: RAGService | None = None


def get_rag_service() -> RAGService:
    global _RAG_SERVICE
    if _RAG_SERVICE is None:
        _RAG_SERVICE = RAGService()
    return _RAG_SERVICE
