# 🌾 AGRISENSE BLUEPRINT

> Authoritative, reproducible blueprint to recreate the AgriSense platform from scratch. Auto-generated sections will be maintained by `scripts/generate_blueprint.py` and a GitHub Action. Manually curated sections are clearly labeled.

---
## 1. EXECUTIVE SUMMARY (Manual)
AgriSense is a full-stack smart agriculture platform combining IoT sensing, ML-driven plant health analytics, irrigation optimization, and decision assistance. It supports crop disease detection (48+ crops), weed classification, crop recommendations, irrigation scheduling, and weather-informed advisory services. The system is modular, extensible, and edge-aware (Raspberry Pi + ESP32).

Core pillars:
- Real-time sensor ingestion & normalization
- Disease and weed detection (comprehensive multi-model logic)
- Crop growth and yield decision support
- Irrigation and fertigation recommendation engine
- Offline-capable edge adapters & MQTT integration
- Chatbot & knowledge-driven advisory (RAG-ready foundation)

---
## 2. TOP-LEVEL REPO STRUCTURE (Auto)
```
AGRISENSEFULL-STACK/
  agrisense_app/              # Core backend + frontend
  agrisense_pi_edge_minimal/  # Edge capture + config
  AGRISENSE_IoT/              # Expanded IoT stack (firmware + dashboards)
  tools/                      # Dev, testing, data & training utilities
  datasets/                   # Raw + processed datasets
  ml_models/                  # Trained artifacts
  documentation/              # Manuals / guides / architecture
  config/                     # Deployment + environment configs
  mobile/                     # (Future / optional) mobile assets
```

---
## 3. BACKEND ARCHITECTURE (Manual)
Technology: FastAPI + Python 3.9+, modular service-style layout. Lazy loading for heavy ML libs guarded by `AGRISENSE_DISABLE_ML`.

Key modules:
- `main.py`        → API surface, routing, CORS, admin guard
- `engine.py`      → Irrigation & fertilizer recommendation logic (+ optional ML blending)
- `disease_detection.py` + `comprehensive_disease_detector.py` → Full-spectrum disease inference & treatment synthesis
- `smart_weed_detector.py` → Crop vs weed classification
- `data_store.py`  → SQLite persistence (sensor readings, logs)
- `mqtt_bridge.py` / `mqtt_publish.py` → Device command + ingestion bridge
- `weather.py`     → External weather enrichment + caching
- `notifier.py`    → Alert and notification pipeline (extensible)
- `websocket_manager.py` → Real-time channel scaffolding

Design principles:
- Fail-open where possible (graceful degradation when ML artifacts absent)
- Explicit environment toggles for performance & platform adaptability
- Edge-first normalization for flexible sensor payload schema

---
## 4. FRONTEND ARCHITECTURE (Manual)
Stack: React + Vite (TypeScript optional). Proxies API via dev server to `http://127.0.0.1:8004`.
Served statically via backend under `/ui` when built.

Functional areas (expected UI features):
- Dashboard (sensor + weather + irrigation status)
- Disease Detection upload/analysis UI
- Weed Classification screen
- Crop recommendation wizard
- Chatbot (optional) interface
- Historical trends (time series plotting)

---
## 5. EDGE & IOT LAYER (Manual)
Components:
- ESP32 firmware (field sensor cluster)
- Raspberry Pi edge ingestion (`agrisense_pi_edge_minimal`)
- MQTT integration (broker configurable via env)

Edge flow:
```
[Sensors] -> ESP32 -> MQTT -> Backend / Edge Adapter -> Database -> Analytics / Recommendation
```
Edge fallback: When cloud unreachable, local buffering strategies can be added (future hook).

---
## 6. DATA FLOW & PIPELINES (Manual)
High-level lifecycle:
1. Sensor/edge ingestion (`/ingest` or `/edge/ingest`)
2. Normalization & persistence
3. Optional enrichment (weather, derived metrics)
4. User/API triggers analysis (`/recommend`, `/disease/detect`)
5. Engine or model inference
6. Recommendations + treatments returned & optionally logged
7. Alerts dispatched if thresholds met

Artifacts:
- `sensors.db` (SQLite) – time-series & event log
- Model files: `water_model.(keras|joblib)`, `fert_model.*`, disease/weed models
- Knowledge assets: `chatbot_qa_pairs.json`, encoders, ranking models

---
## 7. CORE ML COMPONENTS (Manual)
Disease Detection:
- Comprehensive rule + probabilistic logic (heuristics + pseudo-vision abstraction)
- Output: disease list, confidence, severity, treatment_plan (multilayer categories)

Weed Detector:
- ResNet / classical fallback
- Output: classification (weed|crop), species (if detectable), confidence

Irrigation/Fertilizer Recommendation:
- Hybrid deterministic + ML blending (if models present)
- Output: `water_liters`, `fert_*_g`, savings estimate, agronomic tips


---
## 17. RECENT CHANGES (October 2025) (Manual)

Summary of repository changes since the previous blueprint generation. This section is a succinct, human-friendly changelog capturing reorganizations, new features, and operational notes so operators and future maintainers can quickly understand update impact.

- Backend reorganization: backend code was restructured into `core/`, `api/`, `integrations/`, and `config/` subpackages under `agrisense_app/backend`. Key files moved or added: `core/engine.py`, `core/data_store.py`, `api/sensor_api.py`, `integrations/mqtt_bridge.py` and `integrations/mqtt_publish.py`.
- Development tools: Added `dev_launcher.py`, `cleanup_project.py`, `start_agrisense.py` and workspace tasks to simplify starting backend, frontend and smoke tests.
- ML & NLM/VLM integrations: Vision-Language (VLM) and Natural-Language (NLM) capabilities were added. New endpoints include `/api/vlm/status`, `/api/vlm/analyze` and existing disease/weed endpoints have VLM-enhanced paths with graceful fallbacks to classical detectors. Chatbot proxying to external NLM service is wired via `chatbot_service.py` with `NLM_SERVICE_URL` configuration.
- Chatbot tooling: Scripts to build and reload chatbot artifacts (`scripts/build_chatbot_artifacts.py`, `scripts/reload_chatbot.py`) and a lightweight HTTP smoke test (`scripts/chatbot_http_smoke.py`) were added.
- Tests & QA: Tests were reorganized and consolidated under `scripts/` and `tests/` (unit/integration/api). Important test utilities include `test_comprehensive_disease_detection.py`, `test_treatment_validation.py`, and `test_backend_integration.py`.
- Models & datasets: ML models and datasets reorganized under `ml_models/` and `datasets/` with category folders (disease_detection, weed_management, chatbot, core_models). A `ml_models/*/artifacts/metadata.json` convention was adopted for traceability.
- Environment management: split production and dev dependencies into `requirements.txt` and `requirements-dev.txt`. Added guarded ML loading via `AGRISENSE_DISABLE_ML` for faster development and safer CI runs.

Operational notes and run commands (Windows / PowerShell):

```
# Create & activate venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install deps (backend)
pip install -r agrisense_app/backend/requirements.txt
pip install -r agrisense_app/backend/requirements-dev.txt  # optional dev deps

# Start backend (fast, no ML)
$env:AGRISENSE_DISABLE_ML='1'; .venv\Scripts\python.exe -m uvicorn agrisense_app.backend.main:app --port 8004 --reload

# Start frontend (dev)
cd agrisense_app/frontend/farm-fortune-frontend-main
npm install
npm run dev

# Run HTTP smoke test (from repo root; backend must be running)
$env:AGRISENSE_DISABLE_ML='1'; .venv\Scripts\python.exe scripts\chatbot_http_smoke.py
```

---
## 18. CHANGELOG (October 02, 2025)

- 2025-10-02: Blueprint updated to record backend reorganization (core/api/integrations/config), new dev tooling (`dev_launcher.py`, `start_agrisense.*`), VLM & NLM integrations (endpoints + guarded deps), reorganized `ml_models/` and `datasets/`, added `requirements-dev.txt`, and added operational run commands for Windows PowerShell. (This summary integrates notes from `PROJECT_BLUEPRINT_UPDATED.md` and the repository's copilot instructions.)

---
Chatbot / Advisory (Optional):
- Sparse + dense retrieval encoders (SBERT planned integration)
- Reranking via LightGBM (`chatbot_lgbm_ranker.joblib`)

---
## 8. ENVIRONMENT VARIABLES (Auto)
<!-- AUTO:ENV_START -->
| Variable | Present |
|----------|---------|
| ACCESS_TOKEN_EXPIRE_MINUTES | yes |
| AGRISENSE_ADMIN_TOKEN | yes |
| AGRISENSE_ALERT_ON_RECOMMEND | yes |
| AGRISENSE_CHATBOT_ALPHA | yes |
| AGRISENSE_CHATBOT_BM25_WEIGHT | yes |
| AGRISENSE_CHATBOT_DEFAULT_TOPK | yes |
| AGRISENSE_CHATBOT_MIN_COS | yes |
| AGRISENSE_CHATBOT_TOPK_MAX | yes |
| AGRISENSE_DATASET | yes |
| AGRISENSE_DATA_DIR | yes |
| AGRISENSE_DB | yes |
| AGRISENSE_DB_PATH | yes |
| AGRISENSE_DISABLE_ML | yes |
| AGRISENSE_DISABLE_RATE_LIMITING | yes |
| AGRISENSE_DOY | yes |
| AGRISENSE_JWT_SECRET | yes |
| AGRISENSE_LAT | yes |
| AGRISENSE_LOG_RECO | yes |
| AGRISENSE_LON | yes |
| AGRISENSE_MODEL_PATH | yes |
| AGRISENSE_MONGO_DB | yes |
| AGRISENSE_MONGO_URI | yes |
| AGRISENSE_NOTIFY_WEBHOOK_URL | yes |
| AGRISENSE_SBERT_MODEL | yes |
| AGRISENSE_TANK_CAP_L | yes |
| AGRISENSE_TANK_LOW_PCT | yes |
| AGRISENSE_TMAX_C | yes |
| AGRISENSE_TMIN_C | yes |
| AGRISENSE_TWILIO_FROM | yes |
| AGRISENSE_TWILIO_SID | yes |
| AGRISENSE_TWILIO_TO | yes |
| AGRISENSE_TWILIO_TOKEN | yes |
| AGRISENSE_USE_PYTORCH_SBERT | yes |
| AGRISENSE_USE_TENSORFLOW_SERVING | yes |
| AGRISENSE_WEATHER_CACHE | yes |
| ALLOWED_ORIGINS | yes |
| CELERY_BROKER_URL | yes |
| CELERY_RESULT_BACKEND | yes |
| CHATBOT_ALPHA | yes |
| CHATBOT_BM25_WEIGHT | yes |
| CHATBOT_DEFAULT_TOPK | yes |
| CHATBOT_ENABLE_CROP_FACTS | yes |
| CHATBOT_ENABLE_QMATCH | yes |
| CHATBOT_LLM_BLEND | yes |
| CHATBOT_LLM_RERANK_TOPN | yes |
| CHATBOT_MIN_COS | yes |
| CHATBOT_POOL_MIN | yes |
| CHATBOT_POOL_MULT | yes |
| CHATBOT_TOPK_MAX | yes |
| DATABASE_URL | yes |
| DATASET_CSV | yes |
| DEEPSEEK_API_KEY | yes |
| DEEPSEEK_BASE_URL | yes |
| DEEPSEEK_MODEL | yes |
| GEMINI_API_KEY | yes |
| GEMINI_MODEL | yes |
| MONGO_DB | yes |
| MONGO_URI | yes |
| MQTT_BROKER | yes |
| MQTT_PORT | yes |
| MQTT_PREFIX | yes |
| MQTT_TOPIC | yes |
| REDIS_URL | yes |
| REFRESH_TOKEN_EXPIRE_DAYS | yes |
| SENDER_EMAIL | yes |
| SMTP_PASSWORD | yes |
| SMTP_PORT | yes |
| SMTP_SERVER | yes |
| SMTP_USERNAME | yes |
| SQL_DEBUG | yes |
| TANK_CAPACITY_L | yes |
| TANK_LOW_PCT | yes |
| TENSORFLOW_SERVING_URL | yes |
<!-- AUTO:ENV_END -->

---
## 9. API SURFACE (Auto)
Representative endpoints:
<!-- AUTO:API_START -->
| Method(s) | Path | Name | Summary |
|-----------|------|------|---------|
| GET | / | root |  |
| POST | /admin/notify | admin_notify |  |
| POST | /admin/reset | admin_reset | Erase all stored data. Irreversible. |
| POST | /admin/weather/refresh | admin_weather_refresh |  |
| GET | /alerts | get_alerts |  |
| POST | /alerts | post_alert |  |
| POST | /alerts/ack | alerts_ack |  |
| DELETE,GET,PATCH,POST,PUT | /api/{path:path} | api_prefix_redirect |  |
| POST | /chat/ask | chat_ask |  |
| GET | /chatbot/ask | chatbot_ask_get | GET alias for chatbot ask to simplify smoke testing via browser/tools. |
| POST | /chatbot/ask | chatbot_ask |  |
| GET | /chatbot/metrics | chatbot_metrics | Return saved evaluation metrics (e.g., Recall@K) if available. |
| POST | /chatbot/reload | chatbot_reload | Force reload of chatbot artifacts from disk (after retraining). |
| POST | /chatbot/tune | chatbot_tune | Adjust chatbot blending (alpha) and cosine threshold at runtime. |
| GET | /crops | get_crops_full |  |
| GET | /dashboard/summary | dashboard_summary | Compact summary for the main dashboard to reduce roundtrips. |
| POST | /disease/detect | detect_plant_disease | Detect plant diseases in uploaded image |
| GET | /docs | swagger_ui_html |  |
| GET | /docs/oauth2-redirect | swagger_ui_redirect |  |
| POST | /edge/capture | edge_capture | Capture a reading using the local SensorReader (if available), |
| GET | /edge/health | edge_health | Report basic availability of the optional Edge reader on the server. |
| POST | /edge/ingest | edge_ingest | Accept sensor payloads from ESP32 and normalize to SensorReading. |
| GET | /health | health |  |
| POST | /health/assess | comprehensive_health_assessment | Perform comprehensive plant health assessment including disease and weed analysis |
| GET | /health/enhanced | enhanced_health | Enhanced health check including all system components |
| GET | /health/status | get_health_system_status | Get status of plant health monitoring system |
| GET | /health/trends | get_health_trends | Get plant health trends from historical assessments |
| POST | /ingest | ingest |  |
| POST | /irrigation/start | irrigation_start |  |
| POST | /irrigation/stop | irrigation_stop |  |
| GET | /live | live |  |
| GET | /metrics | get_metrics | Prometheus metrics endpoint |
| GET | /openapi.json | openapi |  |
| GET | /plants | get_plants | Return a combined list of crops from config and dataset labels. |
| POST | /rainwater/log | rainwater_log |  |
| GET | /rainwater/recent | rainwater_recent_api |  |
| GET | /rainwater/summary | rainwater_summary_api |  |
| GET | /ready | ready |  |
| GET | /recent | get_recent |  |
| POST | /reco/log | log_reco_snapshot | Explicitly log a recommendation snapshot from the client. |
| GET | /reco/recent | get_reco_recent |  |
| POST | /recommend | recommend |  |
| GET | /recommend/latest | iot_recommend_latest | Synthesize a latest recommendation document compatible with AGRISENSE_IoT frontend. |
| GET | /redoc | redoc_html |  |
| GET | /sensors/recent | iot_sensors_recent | Return recent sensor readings as a bare list, matching AGRISENSE_IoT expectations. |
| GET | /simple-metrics | get_simple_metrics |  |
| GET | /soil/types | get_soil_types | Expose available soil types from config for data-driven selection in UI. |
| GET | /status/rate-limits | rate_limit_status | Get current rate limit status for the requesting client |
| GET | /status/tensorflow-serving | tensorflow_serving_status | Get TensorFlow Serving status and model information |
| GET | /status/websocket | websocket_status | Get WebSocket connection status |
|  | /storage | None |  |
| POST | /suggest_crop | suggest_crop | Suggest high-yield crops for a given soil type and optional conditions. |
| GET | /tank/history | get_tank_history | Return recent tank level rows for sparkline/history consumers. |
| POST | /tank/level | post_tank_level |  |
| GET | /tank/status | get_tank_status |  |
|  | /ui | frontend |  |
| GET | /ui/{path:path} | serve_spa |  |
| GET | /valves/events | get_valve_events |  |
| GET | /version | version |  |
| POST | /weed/analyze | analyze_weeds | Analyze weed infestation in field image using smart detection |
<!-- AUTO:API_END -->
(Full parameter schema auto-generated by script.)

---
## Recent Integrations: VLM & NLM

Summary of recent project changes enhancing vision-language and natural-language capabilities.

- VLM (Vision Language Model)
  - New files: `agrisense_app/backend/vlm_engine.py`, VLM test scripts under `scripts/` and a `VLM_INTEGRATION_SUMMARY.md` documenting setup and usage.
  - Endpoints added: `/api/vlm/status`, `/api/vlm/analyze`, and VLM-enhanced paths for `/api/disease/detect` and `/api/weed/analyze` (fallback to classical detectors when VLM unavailable).
  - Dependencies: optional computer-vision and transformers packages added to backend `requirements.txt` and guarded so the system runs with `AGRISENSE_DISABLE_ML=1`.
  - Tests: `scripts/test_vlm_integration.py` and `scripts/test_vlm_integration_clean.py` provide engine-level and endpoint smoke tests.

- NLM (Natural Language Model)
  - New/updated components: `agrisense_app/backend/chatbot_service.py` and wiring in `agrisense_app/backend/main.py` to route chat requests to the external NLM service.
  - Env var: `NLM_SERVICE_URL` (example: `http://localhost:8005`) used to configure the external NLM endpoint; present in backend `.env`.
  - Behavior: the backend proxies POST /chat (or `/chatbot/ask`) traffic to the NLM service and surfaces service errors with appropriate HTTP status codes.
  - Training helper: `scripts/train_nlm.py` writes artifacts into `agrisense_app/backend/ml_models/nlm/artifacts/` when run.

Notes and rollout guidance:
- Both integrations follow the repository's stability guarantees: optional ML dependencies, guarded imports, and deterministic fallbacks when models or services are unavailable.
- Recommended smoke tests (local):

```powershell
# VLM status
curl http://127.0.0.1:8004/api/vlm/status

# NLM (requires NLM service running at NLM_SERVICE_URL)
curl -X POST http://127.0.0.1:8004/chat -H "Content-Type: application/json" -d '{"message":"Hello"}'
```

Additions to the blueprint above will be regenerated by `scripts/generate_blueprint.py` on the next run; this section provides a human-friendly summary until then.

---
## 10. REPRODUCTION STEPS (Manual)
### 10.1. Prerequisites
- Python 3.9+
- Node.js 18+
- (Optional) MQTT broker (e.g., Mosquitto)
- (Optional) TensorFlow / GPU stack

### 10.2. Backend Setup
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r agrisense_app/backend/requirements.txt
# (Optional speed) set AGRISENSE_DISABLE_ML=1 during dev
uvicorn agrisense_app.backend.main:app --reload --port 8004
```

### 10.3. Frontend Setup
```bash
cd agrisense_app/frontend/farm-fortune-frontend-main
npm install
npm run dev
# Build for backend serving:
npm run build
```

### 10.4. Edge Adapter
```bash
cd agrisense_pi_edge_minimal
pip install -r requirements.txt
python -m edge.reader   # (Example entry)
```

### 10.5. Optional: Start MQTT Broker
```bash
# Example (Docker)
docker run -it -p 1883:1883 eclipse-mosquitto
```

---
## 11. TESTING & QA (Manual)
Run essential tests:
```bash
pytest -q scripts/test_comprehensive_disease_detection.py scripts/test_treatment_validation.py
```
Smoke (manual):
```bash
curl http://127.0.0.1:8004/health
```

---
## 12. DEPLOYMENT (Manual)
Recommended path:
1. Containerize backend (Uvicorn + Gunicorn optional)
2. Serve frontend static under `/ui`
3. Provision managed MQTT or bridge
4. Configure env secrets (admin token, origins)
5. Add monitoring (Prometheus or lightweight log scanning)

Scale-out strategies:
- Read replicas (SQLite -> Postgres migration path)
- Model server (TF Serving or ONNX Runtime)
- Task queue (Celery + Redis) for heavy processing

---
## 13. FAILURE & RESILIENCE (Manual)
Graceful degradation patterns:
- Missing ML models → deterministic fallbacks
- Weather API failure → cached or neutral values
- MQTT outage → local buffering (future enhancement)
- DB corruption → recreate schema + replay ingestion logs (optional extension)

---
## 14. SECURITY MODEL (Manual)
- Header token auth for admin endpoints: `X-Admin-Token`
- Input sanitation on ingestion and image endpoints
- CORS restricted via `ALLOWED_ORIGINS`
- Future: JWT & RBAC expansion, encrypted at-rest DB variant

---
## 15. PERFORMANCE OPTIMIZATIONS (Manual)
- Conditional ML loading (`AGRISENSE_DISABLE_ML`)
- Lightweight path for edge vs. full inference
- Cached weather & derived stats
- Batched DB writes (extension opportunity)
- Model warm-start on startup

---
## 16. AUTO-GENERATED SECTIONS DESIGN (Manual)
`generate_blueprint.py` will parse:
- FastAPI routes (introspect `app.routes`)
- Environment variables (regex scanning + os.getenv keys)
- Requirements (hash versions from `requirements.txt`)
- Model artifacts present (file existence)
- Dataset catalog (enumerate `datasets/` subdirs)

It will rewrite placeholder markers:
```
<!-- AUTO:API_START -->
| Method(s) | Path | Name | Summary |
|-----------|------|------|---------|
| GET | / | root |  |
| POST | /admin/notify | admin_notify |  |
| POST | /admin/reset | admin_reset | Erase all stored data. Irreversible. |
| POST | /admin/weather/refresh | admin_weather_refresh |  |
| GET | /alerts | get_alerts |  |
| POST | /alerts | post_alert |  |
| POST | /alerts/ack | alerts_ack |  |
| DELETE,GET,PATCH,POST,PUT | /api/{path:path} | api_prefix_redirect |  |
| POST | /chat/ask | chat_ask |  |
| GET | /chatbot/ask | chatbot_ask_get | GET alias for chatbot ask to simplify smoke testing via browser/tools. |
| POST | /chatbot/ask | chatbot_ask |  |
| GET | /chatbot/metrics | chatbot_metrics | Return saved evaluation metrics (e.g., Recall@K) if available. |
| POST | /chatbot/reload | chatbot_reload | Force reload of chatbot artifacts from disk (after retraining). |
| POST | /chatbot/tune | chatbot_tune | Adjust chatbot blending (alpha) and cosine threshold at runtime. |
| GET | /crops | get_crops_full |  |
| GET | /dashboard/summary | dashboard_summary | Compact summary for the main dashboard to reduce roundtrips. |
| POST | /disease/detect | detect_plant_disease | Detect plant diseases in uploaded image |
| GET | /docs | swagger_ui_html |  |
| GET | /docs/oauth2-redirect | swagger_ui_redirect |  |
| POST | /edge/capture | edge_capture | Capture a reading using the local SensorReader (if available), |
| GET | /edge/health | edge_health | Report basic availability of the optional Edge reader on the server. |
| POST | /edge/ingest | edge_ingest | Accept sensor payloads from ESP32 and normalize to SensorReading. |
| GET | /health | health |  |
| POST | /health/assess | comprehensive_health_assessment | Perform comprehensive plant health assessment including disease and weed analysis |
| GET | /health/enhanced | enhanced_health | Enhanced health check including all system components |
| GET | /health/status | get_health_system_status | Get status of plant health monitoring system |
| GET | /health/trends | get_health_trends | Get plant health trends from historical assessments |
| POST | /ingest | ingest |  |
| POST | /irrigation/start | irrigation_start |  |
| POST | /irrigation/stop | irrigation_stop |  |
| GET | /live | live |  |
| GET | /metrics | get_metrics | Prometheus metrics endpoint |
| GET | /openapi.json | openapi |  |
| GET | /plants | get_plants | Return a combined list of crops from config and dataset labels. |
| POST | /rainwater/log | rainwater_log |  |
| GET | /rainwater/recent | rainwater_recent_api |  |
| GET | /rainwater/summary | rainwater_summary_api |  |
| GET | /ready | ready |  |
| GET | /recent | get_recent |  |
| POST | /reco/log | log_reco_snapshot | Explicitly log a recommendation snapshot from the client. |
| GET | /reco/recent | get_reco_recent |  |
| POST | /recommend | recommend |  |
| GET | /recommend/latest | iot_recommend_latest | Synthesize a latest recommendation document compatible with AGRISENSE_IoT frontend. |
| GET | /redoc | redoc_html |  |
| GET | /sensors/recent | iot_sensors_recent | Return recent sensor readings as a bare list, matching AGRISENSE_IoT expectations. |
| GET | /simple-metrics | get_simple_metrics |  |
| GET | /soil/types | get_soil_types | Expose available soil types from config for data-driven selection in UI. |
| GET | /status/rate-limits | rate_limit_status | Get current rate limit status for the requesting client |
| GET | /status/tensorflow-serving | tensorflow_serving_status | Get TensorFlow Serving status and model information |
| GET | /status/websocket | websocket_status | Get WebSocket connection status |
|  | /storage | None |  |
| POST | /suggest_crop | suggest_crop | Suggest high-yield crops for a given soil type and optional conditions. |
| GET | /tank/history | get_tank_history | Return recent tank level rows for sparkline/history consumers. |
| POST | /tank/level | post_tank_level |  |
| GET | /tank/status | get_tank_status |  |
|  | /ui | frontend |  |
| GET | /ui/{path:path} | serve_spa |  |
| GET | /valves/events | get_valve_events |  |
| GET | /version | version |  |
| POST | /weed/analyze | analyze_weeds | Analyze weed infestation in field image using smart detection |
<!-- AUTO:API_END -->
<!-- AUTO:ENV_START -->
| Variable | Present |
|----------|---------|
| ACCESS_TOKEN_EXPIRE_MINUTES | yes |
| AGRISENSE_ADMIN_TOKEN | yes |
| AGRISENSE_ALERT_ON_RECOMMEND | yes |
| AGRISENSE_CHATBOT_ALPHA | yes |
| AGRISENSE_CHATBOT_BM25_WEIGHT | yes |
| AGRISENSE_CHATBOT_DEFAULT_TOPK | yes |
| AGRISENSE_CHATBOT_MIN_COS | yes |
| AGRISENSE_CHATBOT_TOPK_MAX | yes |
| AGRISENSE_DATASET | yes |
| AGRISENSE_DATA_DIR | yes |
| AGRISENSE_DB | yes |
| AGRISENSE_DB_PATH | yes |
| AGRISENSE_DISABLE_ML | yes |
| AGRISENSE_DISABLE_RATE_LIMITING | yes |
| AGRISENSE_DOY | yes |
| AGRISENSE_JWT_SECRET | yes |
| AGRISENSE_LAT | yes |
| AGRISENSE_LOG_RECO | yes |
| AGRISENSE_LON | yes |
| AGRISENSE_MODEL_PATH | yes |
| AGRISENSE_MONGO_DB | yes |
| AGRISENSE_MONGO_URI | yes |
| AGRISENSE_NOTIFY_WEBHOOK_URL | yes |
| AGRISENSE_SBERT_MODEL | yes |
| AGRISENSE_TANK_CAP_L | yes |
| AGRISENSE_TANK_LOW_PCT | yes |
| AGRISENSE_TMAX_C | yes |
| AGRISENSE_TMIN_C | yes |
| AGRISENSE_TWILIO_FROM | yes |
| AGRISENSE_TWILIO_SID | yes |
| AGRISENSE_TWILIO_TO | yes |
| AGRISENSE_TWILIO_TOKEN | yes |
| AGRISENSE_USE_PYTORCH_SBERT | yes |
| AGRISENSE_USE_TENSORFLOW_SERVING | yes |
| AGRISENSE_WEATHER_CACHE | yes |
| ALLOWED_ORIGINS | yes |
| CELERY_BROKER_URL | yes |
| CELERY_RESULT_BACKEND | yes |
| CHATBOT_ALPHA | yes |
| CHATBOT_BM25_WEIGHT | yes |
| CHATBOT_DEFAULT_TOPK | yes |
| CHATBOT_ENABLE_CROP_FACTS | yes |
| CHATBOT_ENABLE_QMATCH | yes |
| CHATBOT_LLM_BLEND | yes |
| CHATBOT_LLM_RERANK_TOPN | yes |
| CHATBOT_MIN_COS | yes |
| CHATBOT_POOL_MIN | yes |
| CHATBOT_POOL_MULT | yes |
| CHATBOT_TOPK_MAX | yes |
| DATABASE_URL | yes |
| DATASET_CSV | yes |
| DEEPSEEK_API_KEY | yes |
| DEEPSEEK_BASE_URL | yes |
| DEEPSEEK_MODEL | yes |
| GEMINI_API_KEY | yes |
| GEMINI_MODEL | yes |
| MONGO_DB | yes |
| MONGO_URI | yes |
| MQTT_BROKER | yes |
| MQTT_PORT | yes |
| MQTT_PREFIX | yes |
| MQTT_TOPIC | yes |
| REDIS_URL | yes |
| REFRESH_TOKEN_EXPIRE_DAYS | yes |
| SENDER_EMAIL | yes |
| SMTP_PASSWORD | yes |
| SMTP_PORT | yes |
| SMTP_SERVER | yes |
| SMTP_USERNAME | yes |
| SQL_DEBUG | yes |
| TANK_CAPACITY_L | yes |
| TANK_LOW_PCT | yes |
| TENSORFLOW_SERVING_URL | yes |
<!-- AUTO:ENV_END -->
<!-- AUTO:MODELS_START -->
| Artifact | Size (KB) |
|----------|-----------|
| chatbot_index.npz | 3576.9 |
| chatbot_lgbm_ranker.joblib | 1554.3 |
| chatbot_q_index.npz | 3497.7 |
| chatbot_question_encoder.keras | 10248.9 |
| crop_classification_model.joblib | 2528.5 |
| crop_encoder.joblib | 0.9 |
| crop_tf.keras | 0.1 |
| disease_encoder_enhanced.joblib | 0.9 |
| disease_model_enhanced.joblib | 4458.9 |
| fert_model.joblib | 298878.6 |
| fert_model.keras | 0.1 |
| soil_encoder.joblib | 0.6 |
| water_model.joblib | 85369.1 |
| water_model.keras | 0.1 |
| weed_encoder_enhanced.joblib | 0.7 |
| weed_model_enhanced.joblib | 5703.8 |
| yield_prediction_model.joblib | 378.0 |
| yield_tf.keras | 0.1 |
<!-- AUTO:MODELS_END -->
```

---
## 17. FUTURE EXTENSIONS (Manual)
- Satellite imagery ingestion
- IoT OTA update manager
- Multi-tenant farms & access control
- Predictive yield modeling with temporal fusion transformers
- Mobile offline sync client

---
## 18. MAINTENANCE PLAYBOOK (Manual)
Weekly:
- Run blueprint regen script
- Verify model hash integrity
- Archive old sensor records (optional rotation)
- Refresh weather cache

Monthly:
- Retrain models (if drift observed)
- Update dependency security patches
- Review alert anomaly thresholds

---
## 19. GLOSSARY (Manual)
| Term | Definition |
|------|------------|
| Edge Adapter | Lightweight ingestion process running near sensors |
| Recommendation Engine | Calculates irrigation/fertilizer suggestions |
| Comprehensive Detector | Enhanced rule + heuristic disease analyzer |
| Treatment Plan | Structured multi-category response to detected diseases |
| RAG | Retrieval-Augmented Generation (for advisory chatbot) |

---
## 20. CHANGE LOG (Auto)
Last generated: 2025-09-28T12:00:00Z
<!-- AUTO:CHANGELOG_START -->
 - Auto-update: 2025-09-28T12:00:00Z
(pending)
<!-- AUTO:CHANGELOG_END -->

---
> End of manually curated baseline. Auto sections will appear below after first generation.
<!-- AUTO:MODELS_START -->
| Artifact | Size (KB) |
|----------|-----------|
| chatbot_index.npz | 3576.9 |
| chatbot_lgbm_ranker.joblib | 1554.3 |
| chatbot_q_index.npz | 3497.7 |
| chatbot_question_encoder.keras | 10248.9 |
| crop_classification_model.joblib | 2528.5 |
| crop_encoder.joblib | 0.9 |
| crop_tf.keras | 0.1 |
| disease_encoder_enhanced.joblib | 0.9 |
| disease_model_enhanced.joblib | 4458.9 |
| fert_model.joblib | 298878.6 |
| fert_model.keras | 0.1 |
| soil_encoder.joblib | 0.6 |
| water_model.joblib | 85369.1 |
| water_model.keras | 0.1 |
| weed_encoder_enhanced.joblib | 0.7 |
| weed_model_enhanced.joblib | 5703.8 |
| yield_prediction_model.joblib | 378.0 |
| yield_tf.keras | 0.1 |
<!-- AUTO:MODELS_END -->
