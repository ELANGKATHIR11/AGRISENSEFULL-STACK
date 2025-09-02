# AGRISENSEFULL-STACK

AIML BASED SMART AGRICULTURE SOLUTION

See `PROJECT_DOCUMENTATION.md` for the full system architecture, API reference, configs, and deployment guide.

## How to run

- Backend (FastAPI/uvicorn):

  - Python 3.9+ recommended
  - Install deps: `pip install -r agrisense_app/backend/requirements.txt`
  - Run: `uvicorn agrisense_app.backend.main:app --reload --port 8004`

- Frontend (Vite/React):
  - Node.js 18+ recommended
  - `cd agrisense_app/frontend/farm-fortune-frontend-main`
  - `npm install`
  - `npm run dev` (serves [http://localhost:8080](http://localhost:8080))
  - Dev proxy: the frontend uses `/api/*` and Vite forwards to `http://127.0.0.1:8004` (see `vite.config.ts`).
  - Optional: create `.env.local` with `VITE_API_URL=http://127.0.0.1:8004` to bypass proxy.
  - Build: `npm run build` → backend will serve `/ui` from the built `dist/`

Environment:

- Create a `.env` at repo root for local tweaks; backend loads it automatically via `python-dotenv`.
- CORS: override allowed origins with `ALLOWED_ORIGINS` (comma-separated). Defaults to `*` in dev.

Note: Large trained models are managed with Git LFS or excluded from Git to keep the repo lightweight.

## Chatbot (QA) status

- Current pipeline accuracy (HTTP eval, 100-sample set, top_k=3): acc@1 ≈ 98.0%
- Artifacts live in `agrisense_app/backend/` (question/answer encoders, indices, metrics).
- Evaluate locally:
  - Run backend on port 8004
  - From repo root: `python AGRISENSEFULL-STACK/scripts/eval_chatbot_http.py --sample 100 --top_k 3`
- Tuning knobs via backend `.env` (same folder):
  - `CHATBOT_ALPHA` (blend dense vs lexical)
  - `CHATBOT_MIN_COS` (confidence threshold)
  - `CHATBOT_DEFAULT_TOPK`, `CHATBOT_BM25_WEIGHT`, `CHATBOT_POOL_MIN`, `CHATBOT_POOL_MULT`
  - Optional: `CHATBOT_ENABLE_QMATCH=1` to allow exact/fuzzy question match shortcuts
