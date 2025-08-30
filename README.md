# AGRISENSEFULL-STACK

AIML BASED SMART AGRICULTURE SOLUTION

## How to run

- Backend (FastAPI/uvicorn):

  - Python 3.9+ recommended
  - Install deps: `pip install -r agrisense_app/backend/requirements.txt`
  - Run: `uvicorn agrisense_app.backend.main:app --reload --port 8004`

- Frontend (Vite/React):
  - Node.js 18+ recommended
  - `cd agrisense_app/frontend/farm-fortune-frontend-main`
  - `npm install`
  - `npm run dev` (serves http://localhost:8080)
  - Dev proxy: the frontend uses `/api/*` and Vite forwards to `http://127.0.0.1:8004` (see `vite.config.ts`).
  - Optional: create `.env.local` with `VITE_API_URL=http://127.0.0.1:8004` to bypass proxy.
  - Build: `npm run build` → backend will serve `/ui` from the built `dist/`

Environment:

- Create a `.env` at repo root for local tweaks; backend loads it automatically via `python-dotenv`.
- CORS: override allowed origins with `ALLOWED_ORIGINS` (comma-separated). Defaults to `*` in dev.

Note: Large trained models are managed with Git LFS or excluded from Git to keep the repo lightweight.
