# AGRISENSEFULL-STACK
AIML BASED SMART AGRICULTURE SOLUTION 

## How to run

- Backend (FastAPI/uvicorn):
	- Python 3.9+ recommended
	- Install deps: `pip install -r agrisense_app/agrisense_app/agrisense_app/backend/requirements.txt`
	- Run: `python agrisense_app/agrisense_app/agrisense_app/backend/main.py` or `uvicorn agrisense_app.agrisense_app.agrisense_app.backend.main:app --reload`

- Frontend (Vite/React):
	- Node.js 18+ recommended
	- `cd agrisense_app/agrisense_app/agrisense_app/frontend`
	- `npm install`
	- `npm run dev`

Note: Large trained models are managed with Git LFS or excluded from Git to keep the repo lightweight.
