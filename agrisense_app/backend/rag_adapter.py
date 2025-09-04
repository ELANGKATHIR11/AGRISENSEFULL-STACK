import os
import json
import importlib.util
import re
from pathlib import Path
from typing import List, Dict, Any, Optional


def _load_rag_module():
    """Dynamically load qa_rag_workspace/src/rag.py as a module."""
    repo_root = Path(__file__).resolve().parents[2]
    rag_path = repo_root / "qa_rag_workspace" / "src" / "rag.py"
    if not rag_path.exists():
        raise FileNotFoundError(f"RAG source not found at {rag_path}")
    spec = importlib.util.spec_from_file_location("qa_rag_rag", str(rag_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Failed to load spec for {rag_path}")
    rag_mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert rag_mod is not None
    spec.loader.exec_module(rag_mod)  # type: ignore
    return rag_mod


def _normalize_q(text: str) -> str:
    """Case/punctuation/whitespace-insensitive normalization for matching."""
    try:
        t = str(text).strip().lower()
        # Collapse whitespace (including non-breaking spaces)
        t = re.sub(r"[\s\u00A0]+", " ", t)
        # Remove non-alphanumerics except spaces and apostrophes
        t = re.sub(r"[^a-z0-9\s']+", "", t)
        return " ".join(t.split())
    except Exception:
        return str(text).strip().lower()


class RAGService:
    """Adapter to qa_rag_workspace retriever with exact/normalized lookup."""

    def __init__(self) -> None:
        self._mod = None
        self._retriever = None
        self._qa_map: Optional[Dict[str, Dict[str, Any]]] = None
        self._qa_norm_map: Optional[Dict[str, Dict[str, Any]]] = None
        self._storage_path: Optional[Path] = None

    def _ensure_loaded(self) -> None:
        if self._mod is None:
            self._mod = _load_rag_module()
        if self._retriever is None:
            storage = os.environ.get(
                "RAG_STORAGE_DIR",
                str(
                    Path(__file__).resolve().parents[2] / "qa_rag_workspace" / "storage"
                ),
            )
            storage_path = Path(storage)
            self._storage_path = storage_path
            index_path = str(storage_path / "index.faiss")
            meta_path = str(storage_path / "meta.json")
            model_name_file = storage_path / "model_name.txt"
            if model_name_file.exists():
                model_name = model_name_file.read_text(encoding="utf-8").strip()
            else:
                model_name = "sentence-transformers/all-MiniLM-L6-v2"
            Retriever = getattr(self._mod, "Retriever", None)  # type: ignore[attr-defined]
            if Retriever is None:
                raise ImportError("RAG module missing 'Retriever' class")
            self._retriever = Retriever(index_path, meta_path, model_name)
            # Build QA maps from meta
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                exact: Dict[str, Dict[str, Any]] = {}
                normd: Dict[str, Dict[str, Any]] = {}
                for row in meta:
                    q = str(row.get("question", "")).strip()
                    if q:
                        exact[q] = row
                        nq = _normalize_q(q)
                        if nq and nq not in normd:
                            normd[nq] = row
                self._qa_map = exact
                self._qa_norm_map = normd
            except Exception:
                self._qa_map = {}
                self._qa_norm_map = {}

    def ask(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        self._ensure_loaded()
        assert self._retriever is not None
        hits = self._retriever.search(query, top_k=top_k)
        # Optional synthesis
        ans = None
        try:
            synth = getattr(self._mod, "synthesize_answer", None)
            if synth is not None:
                ans = synth(query, hits)
        except Exception:
            ans = None
        if ans is None:
            ans = hits[0][1].get("answer", "No result") if hits else "No result"
        # Collect sources
        sources: List[str] = []
        for score, row in hits:
            src = None
            for k in ("source", "file", "id", "dataset", "source_url"):
                v = row.get(k)
                if isinstance(v, str) and v:
                    src = v
                    break
            if not src:
                for k, v in row.items():
                    if k in ("question", "answer"):
                        continue
                    if isinstance(v, str) and v:
                        src = v
                        break
            if src and src not in sources:
                sources.append(str(src))
        return {"answer": ans, "sources": sources}

    def exact_lookup(self, query: str) -> Optional[Dict[str, Any]]:
        """Return dataset answer if question matches exactly or by normalization."""
        self._ensure_loaded()
        if not self._qa_map:
            return None
        key = str(query).strip()
        row = self._qa_map.get(key)
        if not row and self._qa_norm_map:
            row = self._qa_norm_map.get(_normalize_q(key))
        if not row:
            return None
        ans = str(row.get("answer", ""))
        sources: List[str] = []
        src = row.get("source") or row.get("dataset")
        if isinstance(src, str) and src:
            sources.append(src)
        return {"answer": ans, "sources": sources}


# Module-level lazy service
_RAG_SERVICE: Optional["RAGService"] = None


def get_rag_service() -> "RAGService":
    global _RAG_SERVICE
    if _RAG_SERVICE is None:
        _RAG_SERVICE = RAGService()
    return _RAG_SERVICE


def reset_rag_service() -> None:
    """Reset the cached RAG service to force reload on next access."""
    global _RAG_SERVICE
    _RAG_SERVICE = None
