from __future__ import annotations

import argparse
import csv
import json
import os
import random
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import TFSMLayer  # type: ignore


def load_all_qa(repo_root: Path) -> List[Tuple[str, str]]:
    # Reuse the loader in compute_chatbot_metrics to gather QA from existing datasets
    import importlib.util

    script = (
        repo_root / "AGRISENSEFULL-STACK" / "scripts" / "compute_chatbot_metrics.py"
    )
    if not script.exists():
        script = repo_root / "scripts" / "compute_chatbot_metrics.py"
    spec = importlib.util.spec_from_file_location("cbm", str(script))
    assert spec and spec.loader
    cbm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cbm)  # type: ignore
    df = cbm.load_datasets(repo_root)  # type: ignore
    df = df.drop_duplicates(subset=["question"]).reset_index(drop=True)
    return list(
        zip(df["question"].astype(str).tolist(), df["answer"].astype(str).tolist())
    )


def load_retriever(backend_dir: Path):
    qenc_dir = backend_dir / "chatbot_question_encoder"
    index_npz = backend_dir / "chatbot_index.npz"
    index_json = backend_dir / "chatbot_index.json"
    if not (qenc_dir.exists() and index_npz.exists() and index_json.exists()):
        raise FileNotFoundError("Missing chatbot encoders/index under backend/")
    q_layer = TFSMLayer(str(qenc_dir), call_endpoint="serve")
    with np.load(index_npz, allow_pickle=False) as data:
        a_emb = data["embeddings"]
    # Normalize
    a_emb = a_emb / (np.linalg.norm(a_emb, axis=1, keepdims=True) + 1e-12)
    with open(index_json, "r", encoding="utf-8") as f:
        meta = json.load(f)
    answers: List[str] = list(meta.get("answers", []))
    return q_layer, a_emb, answers


def retrieve(
    q_layer, a_emb: np.ndarray, answers: List[str], question: str, top_k: int = 6
) -> List[Tuple[str, float]]:
    q_vecs = q_layer(tf.constant([question]))
    if isinstance(q_vecs, (list, tuple)):
        q_vecs = q_vecs[0]
    q = q_vecs.numpy()
    q = q / (np.linalg.norm(q, axis=1, keepdims=True) + 1e-12)
    sims = (q @ a_emb.T)[0]
    idx = np.argsort(-sims)[:top_k]
    return [(answers[i], float(sims[i])) for i in idx]


def build_prompt(question: str, contexts: List[str]) -> str:
    ctx = "\n\n".join(f"- {c}" for c in contexts)
    prompt = (
        "You are an agronomy assistant. Answer the user's question ONLY using the provided context snippets.\n"
        "If the answer is not contained in the context, say 'I don't know based on the provided context.'\n"
        "Keep the answer concise and factual.\n\n"
        f"Question: {question}\n\nContext:\n{ctx}\n\nAnswer:"
    )
    return prompt


def ensure_gemini():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set in environment.")
    try:
        import google.generativeai as genai  # type: ignore
    except Exception:
        raise RuntimeError("google.generativeai not available; set up Gemini client or use fallback.")

    # The google.generativeai package has evolved; prefer using configure() + GenerativeModel when present
    configure_fn = getattr(genai, "configure", None)
    GenerativeModel = getattr(genai, "GenerativeModel", None)

    if configure_fn is None or GenerativeModel is None:
        # Try alternate / legacy client patterns
        try:
            # Some versions expose a client() factory
            client_factory = getattr(genai, "client", None)
            if client_factory is not None:
                client = client_factory(api_key=key)  # type: ignore
                model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
                return client.get_model(model_name)  # type: ignore
        except Exception:
            pass
        raise RuntimeError("Installed google.generativeai has unexpected API surface; cannot create Gemini model.")

    # Standard path
    configure_fn(api_key=key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    model = GenerativeModel(model_name)
    return model


def call_gemini(model, prompt: str, retries: int = 3, delay: float = 1.0) -> str:
    last_err: Exception | None = None
    for i in range(retries):
        try:
            resp = model.generate_content(prompt)
            text = getattr(resp, "text", None) or ""
            if not text and hasattr(resp, "candidates"):
                # fallback parse
                for c in getattr(resp, "candidates", []) or []:
                    parts = (
                        getattr(c, "content", {}).get("parts")
                        if hasattr(c, "content")
                        else None
                    )
                    if parts:
                        text = "\n".join(
                            str(p.get("text") or "")
                            for p in parts
                            if isinstance(p, dict)
                        )
                        if text:
                            break
            return text.strip()
        except Exception as e:
            last_err = e
            time.sleep(delay * (i + 1))
    raise RuntimeError(f"Gemini call failed: {last_err}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit", type=int, default=500, help="Max QA pairs to augment"
    )
    parser.add_argument("--top_k", type=int, default=6, help="contexts per question")
    parser.add_argument("--shuffle", action="store_true")
    parser.add_argument("--out", type=str, default="rag_qa_gemini.csv")
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    repo_root = script_path.parents[1]
    backend_dir = repo_root / "agrisense_app" / "backend"

    qa = load_all_qa(repo_root)
    if args.shuffle:
        random.Random(42).shuffle(qa)
    qa = qa[: args.limit]

    q_layer, a_emb, answers = load_retriever(backend_dir)
    model = ensure_gemini()

    out_path = (repo_root / args.out).resolve()
    out_tmp = out_path.with_suffix(".tmp.csv")
    done = 0
    with open(out_tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["question", "answer", "source"])  # header
        for i, (q, _gold) in enumerate(qa):
            try:
                ctx = [
                    c
                    for (c, s) in retrieve(q_layer, a_emb, answers, q, top_k=args.top_k)
                ]
                prompt = build_prompt(q, ctx)
                ans = call_gemini(model, prompt)
                if ans:
                    w.writerow([q, ans, "RAGGemini"])
                    done += 1
            except Exception:
                # skip on failures
                pass
            if (i + 1) % 20 == 0:
                print(f"[rag] processed {i+1}/{len(qa)} (written={done})")

    os.replace(out_tmp, out_path)
    print(f"Wrote RAG-augmented CSV -> {out_path} (rows={done})")


if __name__ == "__main__":
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    main()
