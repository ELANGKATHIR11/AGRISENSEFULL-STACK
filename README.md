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
	- (optional) create `.env` with `VITE_API_URL=http://127.0.0.1:8004`
	- `npm run dev` (serves http://localhost:8080)
	- Build: `npm run build` → backend will serve `/ui` from the built `dist/`

Note: Large trained models are managed with Git LFS or excluded from Git to keep the repo lightweight.
