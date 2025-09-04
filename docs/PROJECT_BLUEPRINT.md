# AgriSense Project Blueprint — Rebuild, Operate, and Deploy from Scratch

This blueprint is a complete, practical manual to recreate AgriSense end-to-end: data, ML, backend API, frontend, optional edge/IoT integration, and Azure deployment. It’s written to be hands-on—follow the steps to stand up a working system.

---

## What’s new (Sep 2025 — updated Sep 04, 2025)

- Data reorg & compatibility:
  - Project CSV datasets have been consolidated under a top-level `data/` directory to make dataset management explicit and predictable.
  - A compatibility helper `scripts/_data_paths.py` was added with `find_data_file(repo_root, name)` which lets existing scripts transparently locate CSVs in either the legacy root location or the new `data/` folder.
  - A preview helper `scripts/propose_reorg.ps1` prints recommended `git mv` commands (non-destructive) for moving files while preserving history.
- Chatbot tuning and hot-reload:
  - `/chatbot/reload` refreshes artifacts and applies env tuning without restart.
  - Hot-reloadable envs: `CHATBOT_ALPHA`, `CHATBOT_MIN_COS` for lexical/embedding balance and min confidence.
  - LLM reranking remains optional and disabled unless API keys are provided.
- Scripts & tooling updates:
  - Updated scripts to use the centralized data lookup: `scripts/train_chatbot.py`, `scripts/train_chatbot_lgbm.py`, `scripts/build_chatbot_qindex.py`, `scripts/compute_chatbot_metrics.py`, `scripts/clean_merge_qa.py`.
  - New/updated utilities: `scripts/eval_chatbot_http.py`, `scripts/rag_augment_qa.py`, and `scripts/build_chatbot_qindex.py` (index building for HTTP evaluation).
  - Added small repo hygiene files: `CONTRIBUTING.md` and a basic `.editorconfig`.
- Documentation & READMEs:
  - Added `data/README.md` (dataset index) and `models/README.md` (model artifact guidance).
  - Top-level `README.md` updated to point to `docs/REPO_STRUCTURE.md` and the new `data/` conventions.
- Security & git hygiene:
  - Large model artifacts remain gitignored; consider Git LFS for any model files you want tracked.
  - CSV moves were performed on branch `reorg/move-datasets` using `git mv` so file history is preserved.

---

## 1) System Overview

AgriSense is a smart farming assistant that:

- Ingests sensor readings (soil moisture, pH, EC, temperature, NPK when available)
- Computes irrigation and fertilizer recommendations using rules + optional ML + climate adjustment (ET0)
- Controls irrigation via MQTT to edge controllers
- Tracks tank levels and rainwater usage
- Serves a web UI (Vite/React) and a minimal mobile client
- Answers farmer questions via a lightweight retrieval Chatbot endpoint (/chatbot/ask) using saved encoders, hybrid re-ranking, crop facts, and latest readings
- Can be deployed to Azure Container Apps with IaC (Bicep) and `azd`

Key components

- Backend API: FastAPI at `agrisense_app/backend/main.py`
- Engine: `agrisense_app/backend/engine.py` with `config.yaml` crop config and optional ML/joblib models
- Data store: SQLite (`agrisense_app/backend/data_store.py`) by default, optional MongoDB (`agrisense_app/backend/data_store_mongo.py`) via env switch
- Weather/ET0: `agrisense_app/backend/weather.py`, `agrisense_app/backend/et0.py`
- Edge & MQTT: `agrisense_app/backend/mqtt_publish.py`, `agrisense_pi_edge_minimal/edge/*`
- Frontend: `agrisense_app/frontend/farm-fortune-frontend-main`
- Frontend Chatbot page: `src/pages/Chatbot.tsx` (route `/chat`) wired to `/chatbot/ask`
- Chatbot artifacts (under backend): `chatbot_question_encoder/`, `chatbot_answer_encoder/`, `chatbot_index.npz`, `chatbot_index.json`, and metrics `chatbot_metrics.json`
  - Optional question-side artifacts: `chatbot_q_index.npz` and `chatbot_qa_pairs.json`
- Infra: `infra/bicep/main.bicep` + `azure.yaml`, containerized by `Dockerfile`
- Actionable tips & analytics: server-side generation of detailed tips and persistence for insights

ASCII map

```text
[Edge Sensors/ESP32] --HTTP/MQTT--> [FastAPI Backend] --SQLite--> [Data]
                                  \-- serves --> [Frontend /ui]
                                  \-- MQTT --> [Valves/Actuators]
                                  \-- (Azure) Container Apps + ACR + Logs
```

---

## 2) Prerequisites

Local development

- Windows, macOS, or Linux
- Python 3.9+ (recommend venv)
- Node.js 18+ (for frontend)
- Git

Container & cloud (optional)

- Docker
- Azure CLI and Azure Developer CLI (`azd`)
- Azure subscription

---

## 3) Repository Layout

- `agrisense_app/backend/` — FastAPI app, engine, datasets, models, storage, MQTT, weather
- `agrisense_app/frontend/farm-fortune-frontend-main/` — Vite/React UI
- `agrisense_pi_edge_minimal/` — Minimal edge agent (optional)
- `mobile/` — Minimal Expo app
- `infra/bicep/` — Azure infra (Container Apps, ACR, identity, logs)
- `Dockerfile` — Multi-stage frontend + backend image
- `azure.yaml` — `azd` service config
- `scripts/` and `agrisense_app/scripts/` — smoke tests, training, utilities

- `data/` — canonical location for CSV datasets (see §4). Scripts search both the legacy root and `data/` via `scripts/_data_paths.py` for compatibility.

---

## 4) Datasets

Included CSVs (root or backend directory):

- `agrisense_app/backend/india_crop_dataset.csv` — Primary catalog for crop names and properties used by UI and crop cards
- `sikkim_crop_dataset.csv` — Optional supplement for region-specific crops

Chatbot training CSVs (if present at repo root):

- `KisanVaani_agriculture_qa.csv` — normalized KisanVaani QA
- `Farming_FAQ_Assistant_Dataset.csv` — FAQ pairs (Question, Answer)
- `Farming_FAQ_Assistant_Dataset (2).csv` — alt FAQ pairs (Question, Answer)
- `data_core.csv` — generic pairs; columns auto-mapped among [question|questions|q] and [answer|answers|a]
- `agriculture-qa-english-only/data/train-00000-of-00001.parquet` — Parquet QA source; see `scripts/prepare_kisan_qa_csv.py`

Columns (union across datasets; not all are required):

- `Crop` or `crop` — Crop name (string)
- `Crop_Category` or `category` — Category (e.g., Cereal, Vegetable, Spice)
- `pH_Min`/`pH_Max` or `ph_min`/`ph_max` — Acceptable soil pH range
- `Temperature_Min_C`/`Temperature_Max_C` or `temperature_min_c`/`temperature_max_c`
- `Growth_Duration_days` or `growth_days`
- `Water_Requirement_mm` or `water_need_l_per_m2` — used to bucket Low/Medium/High water needs
- `Growing_Season` or `season`

Crop labels for UI (optional)

- `agrisense_app/backend/crop_labels.json` — `{ "crops": ["rice", "wheat", ...] }`

Dataset override (crop suggestions)

- Env `AGRISENSE_DATASET` or `DATASET_CSV` sets dataset path for `SmartFarmingRecommendationSystem` used by `/suggest_crop`.

---

## 5) ML Models

Artifacts (optional for runtime)

- Water requirement: `agrisense_app/backend/water_model.keras` or `water_model.joblib`
- Fertilizer adjustment: `agrisense_app/backend/fert_model.keras` or `fert_model.joblib`
- Additional models for classification/yield (e.g., `crop_tf.keras`, `yield_tf.keras`) may exist but are not required to operate core API.

Chatbot (retrieval) training

- Scripts: `scripts/train_chatbot.py` (train bi-encoder), `scripts/compute_chatbot_metrics.py` (Recall@K), `scripts/prepare_kisan_qa_csv.py` (utility)
- Inputs: the CSVs listed in §4 (question/answer columns auto-mapped)
- Outputs under backend:
  - `agrisense_app/backend/chatbot_question_encoder/` (SavedModel)
  - `agrisense_app/backend/chatbot_answer_encoder/` (SavedModel)
  - `agrisense_app/backend/chatbot_index.npz` + `chatbot_index.json` (generated index)
  - `agrisense_app/backend/chatbot_metrics.json` (evaluation)
  - Optional: `agrisense_app/backend/chatbot_q_index.npz` and `chatbot_qa_pairs.json`
- Git hygiene: heavy artifacts above are gitignored; regenerate locally as needed

Train (PowerShell examples)

```powershell
# Quick run
.venv\Scripts\python.exe scripts\train_chatbot.py -e 6 -bs 256 --vocab 50000 --seq-len 96 --temperature 0.05 --lr 5e-4 --augment --aug-repeats 1 --aug-prob 0.35

# Longer run for better Recall@K
.venv\Scripts\python.exe scripts\train_chatbot.py -e 12 -bs 256 --vocab 60000 --seq-len 128 --temperature 0.05 --lr 5e-4 --augment --aug-repeats 2 --aug-prob 0.35

# Compute retrieval metrics (Recall@{1,3,5,10}) for the API
.venv\Scripts\python.exe scripts\compute_chatbot_metrics.py --sample 2000

# Build optional question index for HTTP eval/exact-match checks
.venv\Scripts\python.exe scripts\build_chatbot_qindex.py --sample 5000
```

Runtime behavior

- The backend `/chatbot/ask` endpoint loads the SavedModels, uses cosine similarity with hybrid lexical re-ranking, and returns top answers.
- `/chatbot/metrics` serves `chatbot_metrics.json`.
- `/chatbot/reload` hot-reloads artifacts and applies env tuning without restart.
- The backend auto-tunes retrieval blend and a low-confidence threshold from metrics.

Runtime behavior

- By default (especially in containers), ML is disabled: `AGRISENSE_DISABLE_ML=1` (engine falls back to rules + ET0)
- If enabled and artifacts exist, engine blends ML predictions with rule outputs

Training

- See `agrisense_app/scripts/train_models.py` (or `tf_train.py`, `tf_train_crops.py`, `synthetic_train.py`) as references
- Typical pattern: prepare feature matrix `[moisture, temp, ec, ph, soil_ix, kc]` → train regressor → save `.joblib` or Keras `.keras`
- Keep models alongside backend for simple loading

---

## 6) Backend API (FastAPI)

Entrypoint

- `agrisense_app/backend/main.py` — `FastAPI(title="Agri-Sense API", version="0.2.0")`
- Runs on port 8004 by default

Core endpoints (selected)

- `GET /health`, `/live`, `/ready` — health checks
- `POST /ingest` — store a `SensorReading`
- `POST /recommend` — compute `Recommendation` (does not persist by default)
- `GET /recent?zone_id=Z1&limit=50` — recent readings
- `GET /plants` — available crop list for UI (from config + datasets)
- `GET /crops` — detailed crop cards assembled from datasets
- `GET /soil/types` — available soil types sourced from backend config
- `POST /edge/ingest` — flexible payload from ESP32/edge with aliases (soil_moisture, temp_c, ec_mScm, tank_percent, ...)
- `POST /irrigation/start|stop` — publish MQTT commands, log valve events
- `POST /tank/level`, `GET /tank/status` — tank telemetry and status
- `POST /rainwater/log`, `GET /rainwater/recent|summary` — rainwater ledger
- `GET /alerts`, `POST /alerts`, `POST /alerts/ack` — alert log and ack
- `POST /admin/reset|weather/refresh|notify` — admin utilities (guarded by token if set)
- `GET /metrics` — lightweight counters and uptime
- `GET /version` — app name and version
- `POST /chatbot/ask` — retrieval Chatbot that answers irrigation/fertilizer/tank/crop questions using saved encoders and crop catalog with hybrid re-ranking and crop facts shortcut
- `POST /chatbot/reload` — refresh artifacts and configuration
- `GET /chatbot/metrics` — retrieval metrics (Recall@K) if computed and present
- IoT compatibility shims for external frontends:
  - `GET /sensors/recent?zone_id=Z1&limit=10` — simplified list of readings
  - `GET /recommend/latest?zone_id=Z1` — last recommendation summary

Models

- `SensorReading` fields: `zone_id`, `plant`, `soil_type`, `area_m2`, `ph`, `moisture_pct`, `temperature_c`, `ec_dS_m`, optional `n_ppm`, `p_ppm`, `k_ppm`
- `Recommendation` fields (and extras): `water_liters`, `fert_n_g/p_g/k_g`, `notes`, `tips`, `expected_savings_liters`, `expected_cost_saving_rs`, `expected_co2e_kg`, plus helpful extras (water_per_m2_l, buckets, cycles, suggested_runtime_min, assumed_flow_lpm, fertilizer_equivalents, target_moisture_pct, `water_source`)

Static UI

- `/ui` serves the built frontend (Vite `dist/` copied under `agrisense_app/frontend/farm-fortune-frontend-main/dist`)
- Any `/api/*` path redirects to same path without `/api` prefix (proxy convenience)

Admin guard

- Header `x-admin-token` must match env `AGRISENSE_ADMIN_TOKEN` when set

CORS and compression

- CORS origins: env `ALLOWED_ORIGINS` (CSV), default `*`
- GZip middleware enabled for responses > 500 bytes

---

## 7) Recommendation Engine

Config and defaults

- `agrisense_app/backend/config.yaml` defines plants (kc, ph window, water_factor), soil multipliers, defaults, target NPK ppm, and energy/cost factors
- Soil multipliers (engine constant): `sand=1.10`, `loam=1.00`, `clay=0.90`

Computation outline

1. Normalize/clamp inputs and capture notes
2. Select plant config (and merge optional crop parameters from `crop_parameters.yaml`)
3. Baseline water per m² via kc, soil, moisture, temperature
4. Optional ET0 adjustment (Hargreaves) using `AGRISENSE_LAT`/Tmin/Tmax or from weather cache
5. Optional ML blend (if models loaded): mix TF/sklearn prediction with baseline
6. Fertilizer needs via targets minus measured NPK across area, plus equivalents (urea/DAP/MOP)
7. Compute cost/CO2 savings vs a naïve baseline, runtime minutes, buckets, cycles
8. Return recommendation with guidance notes

Water source selection

- Based on latest tank volume vs required liters: returns `tank` or `groundwater`

Detailed actionable tips

- The engine generates concrete, farmer-friendly tips when parameters deviate from ideal ranges (pH, moisture, EC, N/P/K, temperature, soil type).
- Tips are parameter-aware (e.g., suggest approximate lime/sulfur amounts scaled by area, irrigation cycle splits by soil type, urea/DAP/MOP grams based on deficits) and included in the `Recommendation.tips` array.
- Tips use ASCII-friendly text for broad terminal compatibility.

---

## 8) Storage (SQLite)

Location

- Default: `agrisense_app/backend/sensors.db`
- Override: `AGRISENSE_DB_PATH` or `AGRISENSE_DATA_DIR` (directory)

Tables (created on demand)

- `readings(ts, zone_id, plant, soil_type, area_m2, ph, moisture_pct, temperature_c, ec_dS_m, n_ppm, p_ppm, k_ppm)`
- `reco_history(ts, zone_id, plant, water_liters, expected_savings_liters, fert_n_g, fert_p_g, fert_k_g, yield_potential, water_source?, tips?)`
- `reco_tips(ts, zone_id, plant, tip, category)` — individual tips for analytics (categories: ph, moisture, ec, nitrogen, phosphorus, potassium, climate, other)
- `tank_levels(ts, tank_id, level_pct, volume_l, rainfall_mm)`
- `valve_events(ts, zone_id, action, duration_s, status)`
- `alerts(ts, zone_id, category, message, sent)`
- `rainwater_harvest(ts, tank_id, collected_liters, used_liters)`

Retention & persistence

- Local file persists by default
- In Azure Container Apps, the default EmptyDir is ephemeral; use Azure Files for persistence (see §12)

Recommendation snapshots & tips persistence

- `reco_history` additionally stores a joined `tips` string for context per snapshot.
- Each tip is also inserted into `reco_tips` with a lightweight heuristic category to enable filtering/analytics (e.g., Impact graphs).

---

## 9) Edge & MQTT Integration (Optional)

MQTT publisher

- `agrisense_app/backend/mqtt_publish.py`
- Env: `MQTT_BROKER` (default `localhost`), `MQTT_PORT` (1883), `MQTT_PREFIX` (default `agrisense`)
- Topic: `<PREFIX>/<zone_id>/command`
- Payloads:
  - `{ "action": "start", "duration_s": <int> }`
  - `{ "action": "stop" }`

Edge ingest

- `POST /edge/ingest` accepts flexible keys:
  - moisture: `moisture_pct` or `soil_moisture` or `moisture`
  - temperature: `temperature_c` or `temp_c` or `temperature`
  - EC: `ec_dS_m` or `ec_mScm` or `ec` (mS/cm → dS/m 1:1)
  - Tank: `tank_percent`, optional `tank_id`, `tank_volume_l`, `rainfall_mm`

Edge reader (optional server-side capture)

- If `agrisense_pi_edge_minimal` is available, `POST /edge/capture` can read a sample and compute a recommendation

---

## 10) Frontend & Mobile

Frontend (Vite/React)

- Dev server: `agrisense_app/frontend/farm-fortune-frontend-main`
  - `npm install`
  - `npm run dev`
- Build for backend serving
  - `npm run build` → outputs `dist/`
  - Backend will serve `/ui` from `.../farm-fortune-frontend-main/dist`
- API base
  - Use Vite proxy to backend at `http://127.0.0.1:8004`
  - Or set `.env.local` `VITE_API_URL=http://127.0.0.1:8004`

Recommend page enhancements

- Input form includes soil type (populated dynamically via `GET /soil/types`) and area (m²), with inline validation and submit disabled when invalid.
- The Recommendations view renders a “Detailed Tips” section, listing the actionable tips returned by the backend.
- Additional helpful fields shown include cycles, runtime, fertilizer equivalents, and best time to irrigate.

Mobile (Expo)

- `mobile/` provides a minimal app and API client in `mobile/lib/api.ts`
- Intended as a starter; adapt endpoints as needed

---

## 11) Run Locally (from scratch)

Python environment (PowerShell)

```powershell
# Create venv
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
# Install backend deps (lightweight dev set)
pip install --upgrade pip
pip install -r agrisense_app\backend\requirements-dev.txt
```

Start backend (port 8004)

```powershell
python -m uvicorn agrisense_app.backend.main:app --reload --port 8004
```

Frontend dev

```powershell
cd agrisense_app\frontend\farm-fortune-frontend-main
npm install
npm run dev
```

Smoke test (optional)

```powershell
# In another terminal
curl http://127.0.0.1:8004/health
curl -X POST http://127.0.0.1:8004/recommend -H "Content-Type: application/json" -d '{
  "plant":"tomato","soil_type":"loam","area_m2":100,
  "ph":6.5,"moisture_pct":35,"temperature_c":28,"ec_dS_m":1.0
}'
```

Train Chatbot (optional)

```powershell
.venv\Scripts\python.exe scripts\train_chatbot.py -e 8 -bs 256 --vocab 50000 --seq-len 96 --temperature 0.05 --lr 5e-4 --augment --aug-repeats 1 --aug-prob 0.35
.venv\Scripts\python.exe scripts\compute_chatbot_metrics.py --sample 2000
curl http://127.0.0.1:8004/chatbot/metrics
curl -X POST http://127.0.0.1:8004/chatbot/ask -H "Content-Type: application/json" -d '{"question":"Which crop grows best in sandy soil?","top_k":3}'
```

---

## 12) Containerization & Azure Deployment

MongoDB (optional)

- Alternate persistence via `agrisense_app/backend/data_store_mongo.py`
- Enable with env `AGRISENSE_DB=mongo` (or `mongodb`)
- Connection envs: `AGRISENSE_MONGO_URI` (fallback `MONGO_URI`) and `AGRISENSE_MONGO_DB` (fallback `MONGO_DB`)
- The backend keeps the same public API regardless of store; switching requires no frontend changes

Docker (local)

```powershell
# Build multi-stage image
docker build -t agrisense:local .
# Run container (maps port 8004)
docker run --rm -p 8004:8004 -e AGRISENSE_DISABLE_ML=1 agrisense:local
```

Azure with `azd`

```powershell
azd auth login
azd init -e dev
azd up
```

Provisioned resources

- Azure Container Registry (ACR)
- Container Apps Environment (CAE)
- Managed identity with AcrPull
- Log Analytics workspace
- Container App (public ingress, port 8004)

Configuration (Bicep)

- `infra/bicep/main.bicep` sets env vars: `ALLOWED_ORIGINS`, `AGRISENSE_DISABLE_ML`, `AGRISENSE_DATA_DIR=/data`, `PORT`
- Default volume is `EmptyDir` mounted at `/data` → ephemeral

Persistence (recommended change)

- Replace EmptyDir with Azure Files volume to persist SQLite across revisions
- Steps (high-level):
  1. Create Storage Account + File Share in Bicep
  2. Add secret and `azureFile` volume in Container App template
  3. Mount at `/data` (keep `AGRISENSE_DATA_DIR=/data`)

---

## 13) Configuration & Environment Variables

Core

- `ALLOWED_ORIGINS` — CSV of origins for CORS (default `*`)
- `PORT` — backend port (default `8004`)

Data/DB

- `AGRISENSE_DATA_DIR` — directory for DB and caches (e.g., `/data`)
- `AGRISENSE_DB_PATH` — explicit path to SQLite (overrides directory)

ML & datasets

- `AGRISENSE_DISABLE_ML` — `1` to skip ML model loading
- `AGRISENSE_DATASET` or `DATASET_CSV` — dataset for `/suggest_crop`

Chatbot retrieval tuning (hot-reloadable)

- `CHATBOT_ALPHA` — Blend weight [0..1] between lexical and embedding similarity (e.g., 0.0 emphasizes lexical).
- `CHATBOT_MIN_COS` — Minimum cosine threshold for candidate acceptance.
- `CHATBOT_LLM_RERANK_TOPN`, `CHATBOT_LLM_BLEND` — Optional when LLM key present.
- `GEMINI_API_KEY`, `DEEPSEEK_API_KEY` — Optional keys; if unset, LLM reranking and LLM-based RAG stay disabled.

Weather/ET0

- `AGRISENSE_LAT`, `AGRISENSE_LON` — coordinates
- `AGRISENSE_TMAX_C`, `AGRISENSE_TMIN_C`, `AGRISENSE_DOY` — override ET0 inputs
- `AGRISENSE_WEATHER_CACHE` — path to `weather_cache.csv`

Irrigation/Tank

- `AGRISENSE_TANK_LOW_PCT` — low-level threshold for alerts (default 20)
- `AGRISENSE_TANK_CAP_L` — capacity liters (for status)

Admin/Security

- `AGRISENSE_ADMIN_TOKEN` — required header `x-admin-token` for admin endpoints

MQTT

- `MQTT_BROKER`, `MQTT_PORT`, `MQTT_PREFIX`

Notifications

- `AGRISENSE_NOTIFY_CONSOLE` — default `1`
- `AGRISENSE_NOTIFY_TWILIO`, `AGRISENSE_TWILIO_SID`, `AGRISENSE_TWILIO_TOKEN`, `AGRISENSE_TWILIO_FROM`, `AGRISENSE_TWILIO_TO`
- `AGRISENSE_NOTIFY_WEBHOOK_URL`

---

## 14) Testing & Validation

Smoke tests

- `agrisense_app/scripts/api_smoke_client.py` and `scripts/test_backend_inprocess.py`
- Basic manual checks: `/health`, `/ready`, `/metrics`, simple `/recommend`
- Chatbot: `/chatbot/metrics` and `/chatbot/ask` with a few sample queries
- HTTP eval: `.venv\Scripts\python.exe scripts\eval_chatbot_http.py --sample 100 --top_k 3`
- Optional q-index build: `.venv\Scripts\python.exe scripts\build_chatbot_qindex.py`

Quality gates (suggested)

- Lint/type-check with Pyright (repo contains `pyrightconfig.json`)
- Optional: mypy/ruff
- Automated tests in CI (`.github/workflows/ci.yml` exists; extend as needed)

---

## 15) Troubleshooting

- 404 for `/ui`: ensure frontend is built into `.../farm-fortune-frontend-main/dist` or run Vite dev
- TensorFlow import errors: set `AGRISENSE_DISABLE_ML=1` or use `requirements-dev.txt`
- No data persisted on Azure: configure Azure Files volume (EmptyDir is ephemeral)
- MQTT commands not received: check broker address/port, topic prefix, and network egress
- Admin endpoints unauthorized: set `AGRISENSE_ADMIN_TOKEN` and include `x-admin-token` header

Chatbot returns unrelated answers

- Merge and clean datasets, then rebuild artifacts: `train_chatbot.py` → `compute_chatbot_metrics.py` → (optional) `build_chatbot_qindex.py` → `POST /chatbot/reload`.
- Temporarily set `CHATBOT_ALPHA=0.0` and reload to emphasize lexical overlap.
- Inspect `agrisense_app/backend/chatbot_index.json` for coverage of your Q/A pairs.

---

## 16) Rebuild From Scratch — Minimal Path

1. Clone repo, create venv, install backend dev deps
2. Run backend on 8004
3. Start frontend dev (or build and let backend serve `/ui`)
4. Optionally connect an MQTT broker and an ESP32 publishing to `/edge/ingest`
5. Optionally train and enable ML models, or keep rules-only mode
6. Deploy to Azure with `azd up` when ready

You now have a complete, reproducible pathway from laptop to cloud.

---

## 17) Appendix: Reference Payloads

SensorReading (POST /recommend)

```json
{
  "zone_id": "Z1",
  "plant": "tomato",
  "soil_type": "loam",
  "area_m2": 100,
  "ph": 6.5,
  "moisture_pct": 35,
  "temperature_c": 28,
  "ec_dS_m": 1.0,
  "n_ppm": 20,
  "p_ppm": 10,
  "k_ppm": 80
}
```

Edge ingest (POST /edge/ingest)

```json
{
  "zone_id": "Z1",
  "soil_moisture": 33.2,
  "temp_c": 29.1,
  "ec_mScm": 1.1,
  "plant": "maize",
  "soil_type": "loam",
  "tank_percent": 42.5,
  "tank_id": "T1",
  "tank_volume_l": 500
}
```

Irrigation start (POST /irrigation/start)

```json
{ "zone_id": "Z1", "duration_s": 120, "force": false }
```

Explore `/docs` (Swagger) for more.

---

## 18) License & Credits

- See repository root for license (if provided)
- Built with FastAPI, Uvicorn, NumPy/Pandas/Scikit-Learn/TensorFlow (optional), Vite/React
- Azure Bicep & `azd` for easy cloud deployment
