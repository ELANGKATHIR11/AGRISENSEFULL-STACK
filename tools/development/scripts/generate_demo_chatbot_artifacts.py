"""Generate minimal chatbot artifacts for local integration smoke tests.

This script writes two files into the backend folder:
- chatbot_index.npz (a tiny numpy archive)
- chatbot_qa_pairs.json (a small QA list)

Run this with the project virtualenv Python.
"""
from pathlib import Path
import json


def _write_to(backend: Path):
    backend.mkdir(parents=True, exist_ok=True)

    # Write QA JSON (answers list expected by backend)
    qa = [
        {"question": "Tell me about carrot", "answer": "Carrot is a root vegetable high in beta-carotene."},
        {"question": "How to grow tomatoes?", "answer": "Tomatoes need full sun, regular water and fertile soil."}
    ]
    (backend / "chatbot_qa_pairs.json").write_text(json.dumps({"answers": [q["answer"] for q in qa]} if False else qa, indent=2), encoding="utf-8")

    # Write chatbot_index.json containing the answers list as expected by loader
    meta = {"version": "demo", "created_by": "generate_demo_chatbot_artifacts.py", "answers": [q["answer"] for q in qa]}
    (backend / "chatbot_index.json").write_text(json.dumps(meta), encoding="utf-8")

    # Create a numpy archive with an 'embeddings' array and optional ids
    try:
        import numpy as np
        # Create deterministic small embeddings: 2 answers x 8-dim
        embeddings = np.array([
            [0.1 * i for i in range(8)],
            [0.2 * i for i in range(8)],
        ], dtype=np.float32)
        ids = np.arange(len(embeddings), dtype=np.int32)
        np.savez_compressed(backend / "chatbot_index.npz", embeddings=embeddings, ids=ids)
        print(f"Wrote: {backend / 'chatbot_index.npz'}")
    except Exception:
        # Fallback: write a small binary placeholder (not ideal)
        (backend / "chatbot_index.npz").write_bytes(b"embeddings_placeholder")
        print("numpy not available; wrote placeholder chatbot_index.npz")


def main():
    # Potential backend locations to support both workspace-layout variants
    repo = Path(__file__).resolve().parents[3]
    candidate_backends = [
        Path("D:/AGRISENSE FULL-STACK/agrisense_app/backend"),
        repo / "agrisense_app" / "backend",
    ]

    written = []
    for b in candidate_backends:
        try:
            _write_to(b)
            written.append(str(b))
        except Exception as e:
            print(f"Failed to write artifacts to {b}: {e}")

    if written:
        print("Wrote demo chatbot artifacts to:")
        for p in written:
            print(" -", p)
    else:
        print("No backend directories found to write artifacts.")


if __name__ == '__main__':
    main()
