# AgriSense Project Blueprint — Rebuild, Operate, and Deploy from Scratch

This blueprint is a complete, practical manual to recreate AgriSense end-to-end: data, ML, backend API, frontend, optional edge/IoT integration, and Azure deployment. It’s written to be hands-on—follow the steps to stand up a working system.

---

## 1) System Overview

AgriSense is a smart farming assistant that:

-   Ingests sensor readings (soil moisture, pH, EC, temperature, NPK when available)
-   Computes irrigation and fertilizer recommendations using rules + optional ML + climate adjustment (ET0)
-   Controls irrigation via MQTT to edge controllers
-   Tracks tank levels and rainwater usage
-   Serves a web UI (Vite/React) and a minimal mobile client
-   Can be deployed to Azure Container Apps with IaC (Bicep) and `azd`

Key components

-   Backend API: FastAPI at `agrisense_app/backend/main.py`
-   Engine: `agrisense_app/backend/engine.py` with `config.yaml` crop config and optional ML/joblib models
-   Data store: SQLite (`agrisense_app/backend/data_store.py`)
-   Weather/ET0: `agrisense_app/backend/weather.py`, `agrisense_app/backend/et0.py`
-   Edge & MQTT: `agrisense_app/backend/mqtt_publish.py`, `agrisense_pi_edge_minimal/edge/*`
-   Frontend: `agrisense_app/frontend/farm-fortune-frontend-main`
-   Infra: `infra/bicep/main.bicep` + `azure.yaml`, containerized by `Dockerfile`
-   Chatbot (legacy): retrieval endpoint `/chatbot/ask` with saved encoders and `/chatbot/metrics` for Recall@K (optional)
-   RAG Chat (modern):
    -   `POST /chat/ingest` builds FAISS artifacts from a CSV (SentenceTransformers + L2-normalized embeddings), writing `index.faiss`, `meta.json`, `model_name.txt` under `qa_rag_workspace/storage` (or `RAG_STORAGE_DIR`).
    -   `POST /chat/reload` resets in-memory caches and reloads the retriever.
    -   `POST /chat/ask` answers with guaranteed exact/normalized dataset matching first, then retrieval; responses include `sources`.

Chatbot training datasets (canonical location: `data/`)

-   The project now keeps CSV datasets under a top-level `data/` directory. Scripts have been updated to be compatible with either the legacy root placement or the new `data/` directory.
-   Files you may find in `data/` include:
    -   `KisanVaani_agriculture_qa.csv`
    -   `Farming_FAQ_Assistant_Dataset.csv` and `Farming_FAQ_Assistant_Dataset (2).csv`
    -   `data_core.csv` (auto-mapped columns)
    -   `weather_cache.csv`

Notes:

-   Use `scripts/_data_paths.py`'s `find_data_file(repo_root, name)` helper to programmatically locate datasets from scripts and tooling.
-   A `scripts/propose_reorg.ps1` helper prints `git mv` suggestions (non-destructive) if you want to move legacy CSVs into `data/` while keeping history.

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

-   Windows, macOS, or Linux
-   Python 3.9+ (recommend venv)
-   Node.js 18+ (for frontend)
-   Git

Container & cloud (optional)

-   Docker
-   Azure CLI and Azure Developer CLI (`azd`)
-   Azure subscription

---

## 3) Repository Layout

-   `agrisense_app/backend/` — FastAPI app, engine, datasets, models, storage, MQTT, weather
-   `agrisense_app/frontend/farm-fortune-frontend-main/` — Vite/React UI
-   `agrisense_pi_edge_minimal/` — Minimal edge agent (optional)
-   `mobile/` — Minimal Expo app
-   `infra/bicep/` — Azure infra (Container Apps, ACR, identity, logs)
-   `Dockerfile` — Multi-stage frontend + backend image
-   `azure.yaml` — `azd` service config
-   `scripts/` and `agrisense_app/scripts/` — smoke tests, training, utilities
-   Chatbot artifacts: `agrisense_app/backend/chatbot_question_encoder/`, `chatbot_answer_encoder/`, `chatbot_index.npz`, `chatbot_index.json`, metrics `chatbot_metrics.json`

---

## 4) Datasets

Included CSVs (root or backend directory):

-   `agrisense_app/backend/india_crop_dataset.csv` — Primary catalog for crop names and properties used by UI and crop cards
-   `sikkim_crop_dataset.csv` — Optional supplement for region-specific crops

Columns (union across datasets; not all are required) used by UI and chatbot crop facts:

-   `Crop` or `crop` — Crop name (string)
-   `Crop_Category` or `category` — Category (e.g., Cereal, Vegetable, Spice)
-   `pH_Min`/`pH_Max` or `ph_min`/`ph_max` — Acceptable soil pH range
-   `Temperature_Min_C`/`Temperature_Max_C` or `temperature_min_c`/`temperature_max_c`
-   `Growth_Duration_days` or `growth_days`
-   `Water_Requirement_mm` or `water_need_l_per_m2` — used to bucket Low/Medium/High water needs
-   `Growing_Season` or `season`

Crop labels for UI (optional)

-   `agrisense_app/backend/crop_labels.json` — `{ "crops": ["rice", "wheat", ...] }`

Dataset override (crop suggestions)

-   Env `AGRISENSE_DATASET` or `DATASET_CSV` sets dataset path for `SmartFarmingRecommendationSystem` used by `/suggest_crop`.

---

## 5) ML Models

Artifacts (optional for runtime)

-   Water requirement: `agrisense_app/backend/water_model.keras` or `water_model.joblib`
-   Fertilizer adjustment: `agrisense_app/backend/fert_model.keras` or `fert_model.joblib`
-   Additional models for classification/yield (e.g., `crop_tf.keras`, `yield_tf.keras`) may exist but are not required to operate core API.

Runtime behavior

-   By default (especially in containers), ML is disabled: `AGRISENSE_DISABLE_ML=1` (engine falls back to rules + ET0)
-   If enabled and artifacts exist, engine blends ML predictions with rule outputs

Training

-   See `agrisense_app/scripts/train_models.py` (or `tf_train.py`, `tf_train_crops.py`, `synthetic_train.py`) as references
-   Typical pattern: prepare feature matrix `[moisture, temp, ec, ph, soil_ix, kc]` → train regressor → save `.joblib` or Keras `.keras`
-   Keep models alongside backend for simple loading

---

## 6) Backend API (FastAPI)

Entrypoint

-   `agrisense_app/backend/main.py` — `FastAPI(title="Agri-Sense API", version="0.2.0")`
-   Runs on port 8004 by default

Core endpoints (selected)

-   `GET /health`, `/live`, `/ready` — health checks
-   `POST /ingest` — store a `SensorReading`
-   `POST /recommend` — compute `Recommendation` (does not persist by default)
-   `GET /recent?zone_id=Z1&limit=50` — recent readings
-   `GET /plants` — available crop list for UI (from config + datasets)
-   `GET /crops` — detailed crop cards assembled from datasets
-   `POST /edge/ingest` — flexible payload from ESP32/edge with aliases (soil_moisture, temp_c, ec_mScm, tank_percent, ...)
-   `POST /irrigation/start|stop` — publish MQTT commands, log valve events
-   `POST /tank/level`, `GET /tank/status` — tank telemetry and status
-   `POST /rainwater/log`, `GET /rainwater/recent|summary` — rainwater ledger
-   `GET /alerts`, `POST /alerts`, `POST /alerts/ack` — alert log and ack
-   `POST /admin/reset|weather/refresh|notify` — admin utilities (guarded by token if set)
-   `GET /metrics` — lightweight counters and uptime
-   `GET /version` — app name and version

RAG Chat (modern)

-   `POST /chat/ingest` — Build FAISS artifacts from a CSV. Body keys (all optional):
    -   `csv_path` (default `qa_rag_workspace/data/dataset.csv`)
    -   `text_cols` (list of columns to concatenate for answer text; default auto-detected [Question, Answer])
    -   `model_name` (default `sentence-transformers/all-MiniLM-L6-v2`)
    -   `storage_dir` (default `qa_rag_workspace/storage` or env `RAG_STORAGE_DIR`)
    -   Response: `{ ok: boolean, rows: number, storage: string }`
-   `POST /chat/reload` — Reload retriever/caches. Response: `{ ok: true }`
-   `POST /chat/ask` — `{ message: string, top_k?: number }` → `{ answer: string, sources?: string[] }`
    -   Behavior: exact & normalized dataset matching first (100% coverage for ingested questions), then retrieval fallback.

Models

-   `SensorReading` fields: `zone_id`, `plant`, `soil_type`, `area_m2`, `ph`, `moisture_pct`, `temperature_c`, `ec_dS_m`, optional `n_ppm`, `p_ppm`, `k_ppm`
-   `Recommendation` fields (and extras): `water_liters`, `fert_n_g/p_g/k_g`, `notes`, `expected_savings_liters`, `expected_cost_saving_rs`, `expected_co2e_kg`, plus helpful extras (water_per_m2_l, buckets, cycles, suggested_runtime_min, assumed_flow_lpm, fertilizer_equivalents, target_moisture_pct, `water_source`)

Static UI

-   `/ui` serves the built frontend (Vite `dist/` copied under `agrisense_app/frontend/farm-fortune-frontend-main/dist`)
-   Any `/api/*` path redirects to same path without `/api` prefix (proxy convenience)

Admin guard

-   Header `x-admin-token` must match env `AGRISENSE_ADMIN_TOKEN` when set
-   Secure ingestion in production by requiring this token on `/chat/ingest` and `/chat/reload` invocations from the Admin UI.

CORS and compression

-   CORS origins: env `ALLOWED_ORIGINS` (CSV), default `*`
-   GZip middleware enabled for responses > 500 bytes

---

## 7) Recommendation Engine

Config and defaults

-   `agrisense_app/backend/config.yaml` defines plants (kc, ph window, water_factor), soil multipliers, defaults, target NPK ppm, and energy/cost factors
-   Soil multipliers (engine constant): `sand=1.10`, `loam=1.00`, `clay=0.90`

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

-   Based on latest tank volume vs required liters: returns `tank` or `groundwater`

---

## 8) Storage (SQLite)

Location

-   Default: `agrisense_app/backend/sensors.db`
-   Override: `AGRISENSE_DB_PATH` or `AGRISENSE_DATA_DIR` (directory)

Tables (created on demand)

-   `readings(ts, zone_id, plant, soil_type, area_m2, ph, moisture_pct, temperature_c, ec_dS_m, n_ppm, p_ppm, k_ppm)`
-   `reco_history(ts, zone_id, plant, water_liters, expected_savings_liters, fert_n_g, fert_p_g, fert_k_g, yield_potential, water_source?)`
-   `tank_levels(ts, tank_id, level_pct, volume_l, rainfall_mm)`
-   `valve_events(ts, zone_id, action, duration_s, status)`
-   `alerts(ts, zone_id, category, message, sent)`
-   `rainwater_harvest(ts, tank_id, collected_liters, used_liters)`

Retention & persistence

-   Local file persists by default
-   In Azure Container Apps, the default EmptyDir is ephemeral; use Azure Files for persistence (see §12)

---

## 9) Edge & MQTT Integration (Optional)

MQTT publisher

-   `agrisense_app/backend/mqtt_publish.py`
-   Env: `MQTT_BROKER` (default `localhost`), `MQTT_PORT` (1883), `MQTT_PREFIX` (default `agrisense`)
-   Topic: `<PREFIX>/<zone_id>/command`
-   Payloads:
    -   `{ "action": "start", "duration_s": <int> }`
    -   `{ "action": "stop" }`

Edge ingest

-   `POST /edge/ingest` accepts flexible keys:
    -   moisture: `moisture_pct` or `soil_moisture` or `moisture`
    -   temperature: `temperature_c` or `temp_c` or `temperature`
    -   EC: `ec_dS_m` or `ec_mScm` or `ec` (mS/cm → dS/m 1:1)
    -   Tank: `tank_percent`, optional `tank_id`, `tank_volume_l`, `rainfall_mm`

Edge reader (optional server-side capture)

-   If `agrisense_pi_edge_minimal` is available, `POST /edge/capture` can read a sample and compute a recommendation

---

## 10) Frontend & Mobile

Frontend (Vite/React)

-   Dev server: `agrisense_app/frontend/farm-fortune-frontend-main`
    -   `npm install`
    -   `npm run dev`
-   Build for backend serving
    -   `npm run build` → outputs `dist/`
    -   Backend will serve `/ui` from `.../farm-fortune-frontend-main/dist`
-   API base
    -   Use Vite proxy to backend at `http://127.0.0.1:8004`
    -   Or set `.env.local` `VITE_API_URL=http://127.0.0.1:8004`

Mobile (Expo)

-   `mobile/` provides a minimal app and API client in `mobile/lib/api.ts`
-   Intended as a starter; adapt endpoints as needed

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
# Modern RAG flow
curl -X POST http://127.0.0.1:8004/chat/ingest -H "Content-Type: application/json" -d '{}'
curl -X POST http://127.0.0.1:8004/chat/reload -H "Content-Type: application/json" -d '{}'
curl -X POST http://127.0.0.1:8004/chat/ask -H "Content-Type: application/json" -d '{"message":"According to Simpson (1983), what is the basis of agriculture?","top_k":3}'
# Legacy examples
curl -X POST http://127.0.0.1:8004/chatbot/ask -H "Content-Type: application/json" -d '{"question":"Tell me about carrot","top_k":3}'
curl http://127.0.0.1:8004/chatbot/metrics
curl -X POST http://127.0.0.1:8004/recommend -H "Content-Type: application/json" -d '{
  "plant":"tomato","soil_type":"loam","area_m2":100,
  "ph":6.5,"moisture_pct":35,"temperature_c":28,"ec_dS_m":1.0
}'
```

Train the chatbot (optional)

```powershell
.venv\Scripts\python.exe scripts\train_chatbot.py -e 8 -bs 256 --vocab 50000 --seq-len 96 --temperature 0.05 --lr 5e-4 --augment --aug-repeats 1 --aug-prob 0.35
.venv\Scripts\python.exe scripts\compute_chatbot_metrics.py --sample 2000
```

---

## 12) Containerization & Azure Deployment

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

-   Azure Container Registry (ACR)
-   Container Apps Environment (CAE)
-   Managed identity with AcrPull
-   Log Analytics workspace
-   Container App (public ingress, port 8004)

Configuration (Bicep)

-   `infra/bicep/main.bicep` sets env vars: `ALLOWED_ORIGINS`, `AGRISENSE_DISABLE_ML`, `AGRISENSE_DATA_DIR=/data`, `PORT`
-   Default volume is `EmptyDir` mounted at `/data` → ephemeral

Persistence (recommended change)

-   Replace EmptyDir with Azure Files volume to persist SQLite across revisions
-   Steps (high-level):
    1. Create Storage Account + File Share in Bicep
    2. Add secret and `azureFile` volume in Container App template
    3. Mount at `/data` (keep `AGRISENSE_DATA_DIR=/data`)

---

## 13) Configuration & Environment Variables

Core

-   `ALLOWED_ORIGINS` — CSV of origins for CORS (default `*`)
-   `PORT` — backend port (default `8004`)

Data/DB

-   `AGRISENSE_DATA_DIR` — directory for DB and caches (e.g., `/data`)
-   `AGRISENSE_DB_PATH` — explicit path to SQLite (overrides directory)

ML & datasets

-   `AGRISENSE_DISABLE_ML` — `1` to skip ML model loading
-   `AGRISENSE_DATASET` or `DATASET_CSV` — dataset for `/suggest_crop`

Weather/ET0

-   `AGRISENSE_LAT`, `AGRISENSE_LON` — coordinates
-   `AGRISENSE_TMAX_C`, `AGRISENSE_TMIN_C`, `AGRISENSE_DOY` — override ET0 inputs
-   `AGRISENSE_WEATHER_CACHE` — path to `weather_cache.csv`

Irrigation/Tank

-   `AGRISENSE_TANK_LOW_PCT` — low-level threshold for alerts (default 20)
-   `AGRISENSE_TANK_CAP_L` — capacity liters (for status)

Admin/Security

-   `AGRISENSE_ADMIN_TOKEN` — required header `x-admin-token` for admin endpoints

MQTT

-   `MQTT_BROKER`, `MQTT_PORT`, `MQTT_PREFIX`

Notifications

-   `AGRISENSE_NOTIFY_CONSOLE` — default `1`
-   `AGRISENSE_NOTIFY_TWILIO`, `AGRISENSE_TWILIO_SID`, `AGRISENSE_TWILIO_TOKEN`, `AGRISENSE_TWILIO_FROM`, `AGRISENSE_TWILIO_TO`
-   `AGRISENSE_NOTIFY_WEBHOOK_URL`

---

## 14) Testing & Validation

Smoke tests

-   `agrisense_app/scripts/api_smoke_client.py` and `scripts/test_backend_inprocess.py`
-   Basic manual checks: `/health`, `/ready`, `/metrics`, simple `/recommend`

Quality gates (suggested)

-   Lint/type-check with Pyright (repo contains `pyrightconfig.json`)
-   Optional: mypy/ruff
-   Automated tests in CI (`.github/workflows/ci.yml` exists; extend as needed)

---

## 15) Troubleshooting

-   404 for `/ui`: ensure frontend is built into `.../farm-fortune-frontend-main/dist` or run Vite dev
-   TensorFlow import errors: set `AGRISENSE_DISABLE_ML=1` or use `requirements-dev.txt`
-   No data persisted on Azure: configure Azure Files volume (EmptyDir is ephemeral)
-   MQTT commands not received: check broker address/port, topic prefix, and network egress
-   Admin endpoints unauthorized: set `AGRISENSE_ADMIN_TOKEN` and include `x-admin-token` header

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

-   See repository root for license (if provided)
-   Built with FastAPI, Uvicorn, NumPy/Pandas/Scikit-Learn/TensorFlow (optional), Vite/React
-   Azure Bicep & `azd` for easy cloud deployment
-   Azure Bicep & `azd` for easy cloud deployment
