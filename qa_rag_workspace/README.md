# RAG Q/A Chatbot — VS Code Workspace (Copilot Friendly)

A local **Retrieval-Augmented Generation** chatbot over your CSV dataset using **Sentence-Transformers + FAISS**.
- **Default:** fully local retrieval; final answer = best matching row's `answer`.
- **Optional:** LLM synthesis via `OPENAI_API_KEY` (combines top-k retrieved rows into a concise answer).

## Quickstart
```bash
pip install -r requirements.txt
python -m src.ingest --csv data/dataset.csv --text-cols question answer
streamlit run src/app.py
```

### Optional: LLM synthesis
Set your key (if you want the model to paraphrase/summarize retrieved context):
```bash
export OPENAI_API_KEY=sk-...
# then rerun
streamlit run src/app.py
```

## Project Layout
```
.
├─ data/
│  └─ dataset.csv          # your Q/A data
├─ storage/                # created by ingest (FAISS, meta, model name)
├─ src/
│  ├─ ingest.py            # build embeddings + FAISS index
│  ├─ rag.py               # retrieval and (optional) generator
│  ├─ app.py               # Streamlit UI
│  └─ utils.py
├─ .vscode/
│  ├─ launch.json          # one-click debug/run
│  └─ tasks.json           # build index & run app
├─ .devcontainer/
│  └─ devcontainer.json    # optional containerized dev
└─ requirements.txt
```

## CSV Schema
At minimum:
```
question,answer[,source,context,...]
```
You can pass **multiple** columns via `--text-cols` to improve retrieval.

## Notes
- Retrieval uses cosine similarity on **L2-normalized** embeddings (all-MiniLM-L6-v2).
- FAISS index + metadata are saved under `storage/`.
- ChromaDB is installed if you want to experiment; current pipeline uses FAISS by default.