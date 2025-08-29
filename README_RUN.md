# Run Guide

Backend (FastAPI/Uvicorn):
- Python 3.9+
- Create and activate venv, then install requirements in `agrisense_app/backend/requirements.txt`.
- Run: `python agrisense_app/backend/main.py` or `uvicorn agrisense_app.backend.main:app --reload`.

Frontend (Vite + React + TS):
- From `agrisense_app/frontend`, run `npm install` then `npm run dev`.

Notes:
- Large model artifacts are ignored in git to avoid GitHub file size limits.
- Provide `.env` locally if needed; it's ignored by git.
