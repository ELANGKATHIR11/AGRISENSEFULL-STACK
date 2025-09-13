# Run locally

Backend

- Python 3.9+
- Install: `pip install -r agrisense_app/backend/requirements.txt`
- Run: `uvicorn agrisense_app.backend.main:app --reload --port 8004`

MongoDB (optional)

- To store data in MongoDB instead of the default SQLite file, set these environment variables:
  - `AGRISENSE_DB=mongo`
  - `AGRISENSE_MONGO_URI=mongodb://localhost:27017` (or your URI)
  - `AGRISENSE_MONGO_DB=agrisense` (optional; defaults to `agrisense`)
- All existing endpoints work unchanged; only the storage backend switches.

Frontend (dev)

- Node 18+
- `cd agrisense_app/frontend/farm-fortune-frontend-main`
- `npm install`
- `npm run dev` → <http://localhost:8080>
- API calls are proxied via Vite: frontend uses `/api/...` and Vite forwards to the backend at `http://127.0.0.1:8004` (see `vite.config.ts`).
- If you prefer not to use the proxy, set `.env.local` with `VITE_API_URL=http://127.0.0.1:8004` and the app will call that base directly.

Frontend (build + serve from backend)

- `npm run build` (emits `dist/`)
- Start backend again; browse <http://127.0.0.1:8004/ui>

## Run Guide

Backend (FastAPI/Uvicorn):

- Python 3.9+
- Create and activate venv, then install requirements in `agrisense_app/backend/requirements.txt`.
- Run: `python agrisense_app/backend/main.py` or `uvicorn agrisense_app.backend.main:app --reload`.

Frontend (Vite + React + TS):

- From `agrisense_app/frontend`, run `npm install` then `npm run dev`.

Notes:

- Large model artifacts are ignored in git to avoid GitHub file size limits.
- Provide `.env` locally if needed; it's ignored by git. You can place the MongoDB env vars above in `.env`.
- CORS can be restricted by setting `ALLOWED_ORIGINS` (comma-separated) in env; defaults to `*` in dev.

## Train models (optional)

You can run without any ML models (rules + ET0 only), or train and enable them.

Quick labels + classic ML artifacts (scikit-learn):

- Task: "Train ML Models" (see VS Code tasks)
- Or run: Python script `agrisense_app/scripts/train_models.py` (regenerates `crop_labels.json` and classic `.joblib` models under `agrisense_app/backend/`)

TensorFlow models (water/fertilizer):

- Script: `agrisense_app/backend/tf_train.py`
- Produces `water_model.keras` and `fert_model.keras` next to the backend. The engine will auto-load these if `AGRISENSE_DISABLE_ML` is not set.

Notes:

- In containers or constrained environments, set `AGRISENSE_DISABLE_ML=1` to skip loading models.
- `requirements.txt` includes TensorFlow. For lighter dev installs, use `requirements-dev.txt` (no TF) and keep ML disabled.

## Chatbot (QA) – run and evaluate

- Artifacts: `agrisense_app/backend/chatbot_*.npz/json/keras`
- Quick health check: `GET http://127.0.0.1:8004/health`
- Ask: `POST http://127.0.0.1:8004/chatbot/ask` with body `{ "question":"...", "top_k":3 }`
- Reload artifacts at runtime: `POST /chatbot/reload`
- Metrics file: `agrisense_app/backend/chatbot_metrics.json`
- Evaluate via HTTP:
  - From `AGRISENSEFULL-STACK/`: `python scripts/eval_chatbot_http.py --sample 100 --top_k 3`
  - Writes failures to `agrisense_app/backend/chatbot_eval_failures.json`
- Tuning via `agrisense_app/backend/.env`:
  - `CHATBOT_ALPHA`, `CHATBOT_MIN_COS`, `CHATBOT_DEFAULT_TOPK`, `CHATBOT_BM25_WEIGHT`, `CHATBOT_POOL_MIN`, `CHATBOT_POOL_MULT`
  - Optional: `CHATBOT_ENABLE_QMATCH=1` to enable exact/fuzzy dataset question match
  - Optional: `CHATBOT_ENABLE_CROP_FACTS=1` for generic crop facts fallback when confidence is low
