## Quick orientation — what this repo is

AgriSense is a full-stack FastAPI + Vite app for smart irrigation and crop recommendation. The main runtime pieces are:

- Backend: `agrisense_app/backend/main.py` (FastAPI app; mounted at `uvicorn agrisense_app.backend.main:app`).
- Core logic: `agrisense_app/backend/engine.py` (RecoEngine implements water/fertilizer rules, optional ML blending).
- Persistence: `agrisense_app/backend/data_store.py` (SQLite sensor DB + helper functions).
- Optional Flask storage UI: `agrisense_app/backend/storage_server.py` (mounted under `/storage` when available).
- Edge & MQTT: `agrisense_pi_edge_minimal` (edge reader) and `agrisense_app/backend/mqtt_bridge.py` + `mqtt_publish.py` (MQTT integration).
- Frontend: `agrisense_app/frontend/farm-fortune-frontend-main` (Vite + React). Built assets served under `/ui` by the backend.

## High-value facts for an AI agent (concrete, code-linked)

- API surface and examples live in `backend/main.py` — useful endpoints: `/recommend`, `/ingest`, `/edge/ingest`, `/tank/level`, `/irrigation/start`, `/alerts` and `/reco/log`.
- Engine behavior: `RecoEngine.recommend(reading: Dict)` returns a dict with `water_liters`, `fert_*_g`, `tips`, and `expected_savings_liters` — see numeric calculation and ML blending in `engine.py`.
- ML models are optional. The engine auto-loads `water_model.keras` / `fert_model.keras` or `.joblib` equivalents in the backend folder. To avoid loading heavy libs in tests/dev set `AGRISENSE_DISABLE_ML=1`.
- Edge normalization: `edge_ingest` and `edge_capture` accept flexible keys (e.g., `moisture_pct` or `soil_moisture`, `temp_c` or `temperature_c`) — follow the normalization logic in `main.py` when synthesizing sensor payloads.
- Admin guard: requests that mutate system state use `X-Admin-Token` header checked against `AGRISENSE_ADMIN_TOKEN` (see `AdminGuard` in `main.py`).
- Storage of crop lists and labels: `crop_labels.json`, `india_crop_dataset.csv`, and `sikkim_crop_dataset.csv` are the canonical sources for crop metadata and UI lists.

## Developer workflows and commands (exact)

- Run backend (dev):
  - Ensure Python 3.9+ and venv activated; install: `pip install -r agrisense_app/backend/requirements.txt` (dev deps are in `requirements-dev.txt`).
  - Start: `uvicorn agrisense_app.backend.main:app --reload --port 8004`.
  - VS Code task available: "Run Backend (Uvicorn)" (workspace tasks in this repo).
- Run frontend (dev):
  - cd `agrisense_app/frontend/farm-fortune-frontend-main` → `npm install` → `npm run dev` (Vite proxies `/api/*` → `http://127.0.0.1:8004`).
  - To serve built UI from backend: `npm run build` then open `http://127.0.0.1:8004/ui`.
- Tests / CI:
  - Unit/smoke tests: `pytest -q scripts/test_backend_inprocess.py scripts/test_edge_endpoints.py`.
  - CI runs tests with `AGRISENSE_DISABLE_ML=1` to avoid TF overhead (see `.github/workflows/ci.yml`).
- Train models (optional): `agrisense_app/scripts/train_models.py` and TF training at `agrisense_app/backend/tf_train.py` (only needed if you plan to regenerate `.keras` artifacts).

## Project-specific conventions & pitfalls

- Prefer lightweight, defensive imports: many modules lazily import TF/Flask and fallback gracefully if not installed. When modifying imports, keep this pattern to avoid breaking local dev.
- Use environment toggles for heavy behavior: `AGRISENSE_DISABLE_ML`, `AGRISENSE_ADMIN_TOKEN`, `AGRISENSE_ALERT_ON_RECOMMEND`, and `ALLOWED_ORIGINS` are respected in `main.py` and `engine.py`.
- Persisted files and large models live in `agrisense_app/backend/` but are excluded from git (LFS or ignored). Don’t assume ML artifacts are present in CI/dev unless explicitly added.
- Sensor payloads are normalized in `main.py` — when generating test fixtures, use the same field names the code accepts (see `edge_ingest` for variations).

## Integration points to be aware of

- MQTT: `agrisense_app/backend/mqtt_bridge.py` subscribes and writes readings; `mqtt_publish.py` is used by API endpoints to send valve commands. Broker config via `MQTT_BROKER`, `MQTT_PORT`, `MQTT_TOPIC`.
- Weather caching: `weather.py` writes to `weather_cache.csv`; admin endpoint `/admin/weather/refresh` triggers fetch.
- Edge Reader: optional module `agrisense_pi_edge_minimal.edge.reader.SensorReader` may be present; code guards for its absence. When present, `/edge/capture` will use it.

## When you modify code — quick rules for AI edits

- Keep ML import and model-loading guarded by `AGRISENSE_DISABLE_ML` to keep tests fast.
- When changing API shapes, update the examples in `scripts/test_backend_inprocess.py` to keep CI stable.
- If you touch persistence (`data_store.py`), be conservative: it owns schema and migrations are manual (SQLite `sensors.db`).

## Where to look first (entry points for analysis)

- `agrisense_app/backend/main.py` — API, error shapes, middleware, CORS, mount points.
- `agrisense_app/backend/engine.py` — core recommendation algorithm and ML blending.
- `agrisense_app/backend/data_store.py` — DB schema + helpers used across tests and endpoints.
- `agrisense_app/backend/mqtt_bridge.py`, `mqtt_publish.py` — device/edge integration.
- `agrisense_app/frontend/farm-fortune-frontend-main` — frontend dev, proxy behavior and build output expectations.

If anything above is unclear or you want more examples (sample sensor payloads, test fixtures, or common refactor patterns), tell me which area to expand and I will iterate.
