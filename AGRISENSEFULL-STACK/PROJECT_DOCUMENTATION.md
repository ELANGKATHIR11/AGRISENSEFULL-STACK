# AgriSense Full-Stack Documentation

AIML-based smart agriculture platform providing real-time irrigation and fertilizer recommendations, crop suggestions, basic edge integration, and an intuitive web UI. This document explains the project end-to-end: architecture, requirements, configuration, APIs, data models, deployment, and operations.

> Repo root: `AGRISENSEFULL-STACK/`

---

## Table of contents

- Overview
- Quick start (local)
- Requirements
- Architecture overview
- Components
  - Backend (FastAPI)
  - Frontend (React + Vite)
  - Edge device (Minimal Pi agent)
  - Data store (SQLite)
  - ML models (scikit-learn + optional TensorFlow)
  - Messaging (MQTT, optional)
  - Notifications
  - Weather + ET0
- Configuration (environment variables)
- API reference (endpoints)
- Data contracts (Pydantic models)
- Database schema
- Frontend guide
- Edge integration guide
- Training ML models
- Deployment
  - Docker
  - Azure Container Apps (azd + Bicep)
- Security and privacy
- Observability and health
- Troubleshooting
- Roadmap and next steps

---

## Overview

AgriSense is a full-stack platform to assist farmers and growers with:

- Sensor-driven irrigation recommendations (liters, runtime, savings, CO2e)
- Fertilizer guidance (N, P, K grams and common equivalents)
- Crop suggestions based on soil and environment
- Optional integration with edge devices and MQTT-controlled valves
- A modern SPA UI served by the backend in production or via Vite in development

Core technologies:

- Backend: FastAPI (Python 3.9+), SQLite storage
- ML: scikit-learn models with optional TensorFlow Keras
- Frontend: React + Vite (TypeScript)
- Infra: Dockerfile, Azure Bicep templates, Azure Developer CLI (azd)

Key directories:

- `agrisense_app/backend/` — API, engine, models, storage
- `agrisense_app/frontend/farm-fortune-frontend-main/` — Web UI
- `agrisense_pi_edge_minimal/` — Minimal edge/IoT helper API and reader stub
- `infra/bicep/` — Azure Container Apps IaC
- `agrisense_app/scripts/` and `scripts/` — Utilities, tests, training

---

## Quick start (local)

- Backend
  - Python 3.9+
  - Install: `pip install -r agrisense_app/backend/requirements.txt`
  - Run: `uvicorn agrisense_app.backend.main:app --reload --port 8004`
- Frontend (dev)
  - Node 18+
  - `cd agrisense_app/frontend/farm-fortune-frontend-main`
  - `npm install`
  - `npm run dev` ([http://localhost:8080](http://localhost:8080))
  - Dev proxy forwards `/api/*` → `http://127.0.0.1:8004`
- Frontend (prod)
  - `npm run build` → backend serves the built app at `http://127.0.0.1:8004/ui`

VS Code tasks (pre-wired):

- Run Backend (Uvicorn)
- Run Frontend (Vite)
- Train ML Models

---

## Requirements

- OS: Windows, macOS, or Linux (Windows is actively used during development)
- Backend
  - Python 3.9+
  - `agrisense_app/backend/requirements.txt` (notable: FastAPI, NumPy, pandas, scikit-learn, optional TensorFlow)
- Frontend
  - Node.js 18+
- Optional
  - Docker (for container builds)
  - Azure CLI + Azure Developer CLI (for cloud deployment)
  - MQTT broker (if using valve control)

Hardware (optional):

- Edge device (e.g., Raspberry Pi) with sensors for pH, moisture, etc. The repo includes a minimal stub for development.

---

## Architecture overview

High-level flow from sensors to insights and UI.

```mermaid
flowchart LR
    subgraph Edge[Edge / Field]
      S((Sensors)) --> R[SensorReader]
      R -->|/capture| EAPI[Edge API]
      R -. optional .-> MQTT[MQTT Broker]
    end

    subgraph Backend[Backend (FastAPI)]
      API[/REST API/] --> Engine[RecoEngine]
      Engine --> DB[(SQLite)]
      Engine --> ML[ML Models]
      API --> UI[Static UI /ui]
      API --> Notif[Notifications]
      API --> Weather[Weather + ET0]
      API -. optional .-> MQTT
    end

    UIClient[[Browser SPA]] -->|/ui, /api| API
    EAPI -->|/ingest, /recommend| API
```

Key data paths:

- Sensor readings are posted to `/ingest` and/or analyzed via `/recommend`
- Engine blends rules, ET0 adjustment, and optional ML to produce recommendations
- Snapshots, tank levels, valve events, and alerts are tracked in SQLite
- Frontend fetches from `/api` (dev proxy) or direct backend paths (prod)

---

## Components

### Backend (FastAPI)

- Entrypoint: `agrisense_app/backend/main.py`
- Core engine: `agrisense_app/backend/engine.py`
- Data models: `agrisense_app/backend/models.py`
- Persistence: `agrisense_app/backend/data_store.py` (SQLite file, configurable)
- Weather ET0: `agrisense_app/backend/weather.py` (optional Open-Meteo fetch)
- Optional Flask storage under `/storage` (mounted via WSGI when available)
- Static UI served from `/ui` when the frontend is built

Notable behavior:

- CORS: `ALLOWED_ORIGINS` env var (default `*` in dev)
- Lightweight `/metrics` with request counters and uptime
- Admin-protected endpoints guarded by header `x-admin-token` if `AGRISENSE_ADMIN_TOKEN` is set

### Frontend (React + Vite)

- Path: `agrisense_app/frontend/farm-fortune-frontend-main/`
- Dev proxy: `/api/*` → backend `http://127.0.0.1:8004` (see `vite.config.ts`)
- Production: built assets served by FastAPI under `/ui`

### Edge device (Minimal Pi agent)

- Path: `agrisense_pi_edge_minimal/edge/`
- Provides a tiny FastAPI service and a `SensorReader` stub
- Can relay captured readings to the backend (`/ingest`) and fetch `/recommend`
- Optional MQTT capture trigger supported in the edge agent

### Data store (SQLite)

- Default file: `sensors.db` located under `AGRISENSE_DB_PATH` or `${AGRISENSE_DATA_DIR}/sensors.db`, else next to backend code
- Tables: `readings`, `reco_history`, `tank_levels`, `valve_events`, `alerts`

### ML models (scikit-learn + optional TensorFlow)

- Primary ML for crop suggestions and yields: `smart_farming_ml.py`
- Engine optionally loads joblib or Keras models for water/fert predictions
- Disable heavyweight TF loading via `AGRISENSE_DISABLE_ML=1` (recommended for small containers)

### Messaging (MQTT, optional)

- `mqtt_publish.py` publishes valve open/close commands to `agrisense/<zone>/command`
- Configure via `MQTT_BROKER` and `MQTT_PORT`

### Notifications

- `notifier.py` supports console logging, generic webhook, and optional Twilio SMS
- Configure via env (e.g., `AGRISENSE_NOTIFY_WEBHOOK_URL`, Twilio credentials)

### Weather + ET0

- `weather.py` fetches daily Tmin/Tmax via Open-Meteo; computes ET0 (Hargreaves)
- Cache file (CSV) can be refreshed via `/admin/weather/refresh`
- Engine can incorporate ET0 into irrigation estimates

---

## Configuration (environment variables)

Common variables (all optional unless stated otherwise):

- `ALLOWED_ORIGINS`: CORS origins (comma-separated), default `*` in dev
- `AGRISENSE_ADMIN_TOKEN`: if set, admin endpoints require header `x-admin-token`
- `AGRISENSE_DATA_DIR`: directory for data (e.g., `/data` in containers)
- `AGRISENSE_DB_PATH`: explicit path to `sensors.db`; overrides `AGRISENSE_DATA_DIR`
- `AGRISENSE_DISABLE_ML`: set `1` to skip TensorFlow model loads
- `AGRISENSE_LAT`, `AGRISENSE_TMIN_C`, `AGRISENSE_TMAX_C`, `AGRISENSE_DOY`: adjust ET0 inputs
- `AGRISENSE_WEATHER_CACHE`: path for the weather CSV cache
- `AGRISENSE_NOTIFY_*`: see `notifier.py` for webhook/Twilio options
- `MQTT_BROKER`, `MQTT_PORT`: broker address for valve control

Frontend:

- `.env.local` with `VITE_API_URL=http://127.0.0.1:8004` to bypass proxy in dev

---

## API reference

Base URL

- Dev: `http://127.0.0.1:8004`
- Prod (Azure): Container App FQDN from deployment outputs

Routes

- Health and system
  - `GET /health` → `{status:"ok"}`
  - `GET /live` → liveness
  - `GET /ready` → readiness + ML load flags
  - `GET /metrics` → uptime and counters
  - `GET /version` → name/version
- Admin (guarded by `x-admin-token` when `AGRISENSE_ADMIN_TOKEN` set)
  - `POST /admin/reset` → wipe SQLite
  - `POST /admin/weather/refresh?lat&lon&days` → refresh Open-Meteo cache
  - `POST /admin/notify` → test notification
- Ingestion and recommendation
  - `POST /ingest` body: SensorReading → `{ok:true}`
  - `POST /recommend` body: SensorReading → Recommendation
  - `GET /recent?zone_id=Z1&limit=50` → readings list
- Crop assistance
  - `POST /suggest_crop` body: `{soil_type, ph, nitrogen, phosphorus, potassium, temperature, moisture, humidity, water_level}` → top crops
  - `GET /plants` → UI-friendly crop list with labels/categories
  - `GET /crops` → rich crop cards from dataset
- Recommendation history
  - `GET /reco/recent?zone_id=Z1&limit=200`
  - `POST /reco/log` → persist a provided recommendation snapshot
- Water tank and irrigation
  - `POST /tank/level` → persist tank level/volume/rainfall
  - `GET /tank/status?tank_id=T1`
  - `GET /valves/events?zone_id&limit`
  - `POST /irrigation/start` body: `{zone_id, duration_s?, force?}` → sends MQTT command if possible
  - `POST /irrigation/stop` body: `{zone_id}`
- Alerts
  - `GET /alerts?zone_id&limit`
  - `POST /alerts` body: `{zone_id, category, message, sent?}`
- Edge
  - `GET /edge/health` → whether edge module import is available
  - `POST /edge/capture` body: `{zone_id?}` → capture via local `SensorReader`, ingest, and return recommendation
- Static/UI
  - `GET /` → redirects to `/ui`
  - `GET /ui/*` → SPA assets (production)
  - `GET|POST|… /api/{path}` → redirects to `/{path}` (helps Vite dev proxy)

Sample payloads

SensorReading

```json
{
  "zone_id": "Z1",
  "plant": "tomato",
  "soil_type": "loam",
  "area_m2": 120,
  "ph": 6.5,
  "moisture_pct": 35.0,
  "temperature_c": 28.0,
  "ec_dS_m": 1.0,
  "n_ppm": 20,
  "p_ppm": 10,
  "k_ppm": 80
}
```

Recommendation (truncated example)

```json
{
  "water_liters": 720.5,
  "fert_n_g": 50.0,
  "fert_p_g": 20.0,
  "fert_k_g": 30.0,
  "expected_savings_liters": 180.0,
  "expected_cost_saving_rs": 0.9,
  "expected_co2e_kg": 0.13,
  "water_per_m2_l": 6.0,
  "irrigation_cycles": 1,
  "suggested_runtime_min": 36.0,
  "assumed_flow_lpm": 20.0,
  "best_time": "Early morning or late evening",
  "fertilizer_equivalents": {
    "urea_g": 30.0,
    "dap_g": 40.0,
    "mop_g": 25.0
  },
  "notes": [
    "Soil sufficiently moist; consider skipping irrigation today."
  ]
}
```

---

## Data contracts (Pydantic models)

`SensorReading`

- `zone_id: str = "Z1"`
- `plant: str = "generic"`
- `soil_type: str = "loam"`
- `area_m2: float = 100.0`
- `ph: float = 6.5`
- `moisture_pct: float = 35.0`
- `temperature_c: float = 28.0`
- `ec_dS_m: float = 1.0`
- `n_ppm?: float`
- `p_ppm?: float`
- `k_ppm?: float`
- `timestamp?: str (ISO8601)`

`Recommendation` (accepts extra fields for forward-compat)

- `water_liters: float`
- `fert_n_g: float`
- `fert_p_g: float`
- `fert_k_g: float`
- `notes: string[]`
- `expected_savings_liters: float`
- `expected_cost_saving_rs: float`
- `expected_co2e_kg: float`
- Optional extras: `water_per_m2_l`, `water_buckets_15l`, `irrigation_cycles`, `suggested_runtime_min`, `assumed_flow_lpm`, `best_time`, `fertilizer_equivalents`, `target_moisture_pct`

---

## Database schema

SQLite tables created on first use (`data_store.py`):

- `readings(ts, zone_id, plant, soil_type, area_m2, ph, moisture_pct, temperature_c, ec_dS_m, n_ppm, p_ppm, k_ppm)`
- `reco_history(ts, zone_id, plant, water_liters, expected_savings_liters, fert_n_g, fert_p_g, fert_k_g, yield_potential)`
- `tank_levels(ts, tank_id, level_pct, volume_l, rainfall_mm)`
- `valve_events(ts, zone_id, action, duration_s, status)`
- `alerts(ts, zone_id, category, message, sent)`

Persistence path:

- Default: `${AGRISENSE_DB_PATH}` or `${AGRISENSE_DATA_DIR}/sensors.db` else alongside backend code

---

## Frontend guide

- Dev
  - Start Vite dev server from `agrisense_app/frontend/farm-fortune-frontend-main`
  - API calls to `/api/*` are proxied to `http://127.0.0.1:8004`
- Build
  - `npm run build` produces `dist/`
  - Backend serves `/ui` from the built assets automatically when present
- Config
  - `vite.config.ts` sets base path `/ui/` in prod for correct asset resolution
  - Optionally set `VITE_API_URL` in `.env.local` to call backend directly

---

## Edge integration guide

- Minimal edge FastAPI at `agrisense_pi_edge_minimal/edge/api.py`
- Captures readings via `SensorReader` (stubbed) and posts to backend
- Backend also exposes `POST /edge/capture` to run `SensorReader` in-process on the server when the module is importable
- Optional MQTT trigger to force captures using a topic pattern `agrisense/+/capture_now`

---

## Training ML models

- Script: `agrisense_app/scripts/train_models.py`
  - Regenerates `crop_labels.json` from a dataset CSV
  - Trains scikit-learn models and persists artifacts: `yield_prediction_model.joblib`, `crop_classification_model.joblib`, `soil_encoder.joblib`, `crop_encoder.joblib`
  - Optional `--csv path/to/dataset.csv` to override the default `india_crop_dataset.csv`

Artifacts read at runtime by `smart_farming_ml.py`; TensorFlow models are also supported if present (`yield_tf.keras`, `crop_tf.keras`, with `crop_labels.json` metadata).

---

## Deployment

### Docker

- Dockerfile in repo root can be used to containerize backend (and serve UI when built)
- Ensure `AGRISENSE_DISABLE_ML=1` if you want lean images without TensorFlow
- Persist data by mounting a volume and setting `AGRISENSE_DATA_DIR=/data`

### Azure Container Apps (recommended)

- IaC: `infra/bicep/main.bicep` with parameters `infra/bicep/main.parameters.json`
- Developer workflow with Azure Developer CLI:
  - `azd auth login`
  - `azd init -e <env>`
  - `azd up` (provision + build + deploy)

What gets provisioned:

- Log Analytics workspace
- Container Apps Environment
- Azure Container Registry (ACR)
- User-assigned managed identity with AcrPull
- Container App with public ingress to `${PORT}` (default 8004)

Runtime configuration (see Bicep `env` section):

- `ALLOWED_ORIGINS`, `AGRISENSE_DISABLE_ML`, `AGRISENSE_DATA_DIR`, `PORT`
- Volume: ephemeral `EmptyDir` mounted at `/data`; switch to Azure Files for persistence if needed

Outputs include the public FQDN; open:

- `https://<FQDN>/ui`
- `https://<FQDN>/health`

---

## Security and privacy

- Admin endpoints require `x-admin-token` when `AGRISENSE_ADMIN_TOKEN` is set
- CORS should be restricted in production via `ALLOWED_ORIGINS`
- Secrets (e.g., Twilio) are passed via environment variables
- SQLite contains sensor readings and logs; treat the data directory as sensitive and consider encryption at rest for production setups
- If enabling MQTT control, secure your broker and topics (TLS, auth) to prevent unauthorized actuation

---

## Observability and health

- `GET /metrics` lightweight counters and uptime
- `GET /health`, `GET /live`, `GET /ready` for probes and diagnostics
- Azure: Container App logs flow to Log Analytics; use `az containerapp logs show` or Azure Portal

---

## Troubleshooting

- Backend won’t start (TensorFlow import error)
  - Set `AGRISENSE_DISABLE_ML=1` to run without TF; joblib models still work
- UI 404s under `/ui`
  - Ensure you built the frontend (`npm run build`) or use Vite dev server during development
- CORS errors in browser
  - Configure `ALLOWED_ORIGINS` to your frontend origin
- SQLite not persisting in containers
  - Mount a volume and set `AGRISENSE_DATA_DIR=/data` (or `AGRISENSE_DB_PATH`)
- MQTT commands not sent
  - Ensure `paho-mqtt` is installed and broker reachable; set `MQTT_BROKER`
- Weather cache missing
  - Call `/admin/weather/refresh` to build the CSV cache

---

## Roadmap and next steps

- Add authentication/roles for user-specific zones
- Replace SQLite with a managed DB for scale (PostgreSQL)
- Add Azure Files for durable storage in Container Apps
- Expand ML features with continuous training and telemetry
- Add CI/CD (GitHub Actions) to automate build/test/deploy
- Enhance edge agent to read real sensors and secure MQTT

---

## Appendix: Repo structure (selected)

```text
AGRISENSEFULL-STACK/
  agrisense_app/
    backend/
      main.py, engine.py, models.py, data_store.py, weather.py, notifier.py, mqtt_publish.py, config.yaml
      *.keras, *.joblib (model artifacts)
    frontend/
      farm-fortune-frontend-main/ (React + Vite app)
    scripts/
      train_models.py, smoke/tests utilities
  agrisense_pi_edge_minimal/
    edge/ (tiny FastAPI, reader stub, MQTT trigger)
  infra/
    bicep/ (Azure Container Apps IaC)
  Dockerfile, azure.yaml, README*.md
```

If you need this documentation exported as a PDF or split into separate docs (API, Ops, Architecture), we can add a docs/ folder and Docusaurus or MkDocs in a follow-up.
