# Run locally

Backend
- Python 3.9+
- Install: `pip install -r agrisense_app/backend/requirements.txt`
- Run: `uvicorn agrisense_app.backend.main:app --reload --port 8004`

Frontend (dev)
- Node 18+
- `cd agrisense_app/frontend/farm-fortune-frontend-main`
- (optional) `.env` → `VITE_API_URL=http://127.0.0.1:8004`
- `npm install`
- `npm run dev` → http://localhost:8080

Frontend (build + serve from backend)
- `npm run build` (emits `dist/`)
- Start backend again; browse http://127.0.0.1:8004/ui# Run Guide

Backend (FastAPI/Uvicorn):
- Python 3.9+
- Create and activate venv, then install requirements in `agrisense_app/backend/requirements.txt`.
- Run: `python agrisense_app/backend/main.py` or `uvicorn agrisense_app.backend.main:app --reload`.

Frontend (Vite + React + TS):
- From `agrisense_app/frontend`, run `npm install` then `npm run dev`.

Notes:
- Large model artifacts are ignored in git to avoid GitHub file size limits.
- Provide `.env` locally if needed; it's ignored by git.
