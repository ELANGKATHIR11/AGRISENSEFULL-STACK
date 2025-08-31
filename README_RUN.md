# Run locally

Backend

- Python 3.9+
- Install: `pip install -r agrisense_app/backend/requirements.txt`
- Run: `uvicorn agrisense_app.backend.main:app --reload --port 8004`

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
- Provide `.env` locally if needed; it's ignored by git.
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
