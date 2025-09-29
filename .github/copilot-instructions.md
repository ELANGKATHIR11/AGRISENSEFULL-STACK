## Quick orientation — what this repo is

AgriSense is a full-stack FastAPI + Vite app for smart irrigation, crop recommendation and plant disease tooling. This document is a practical, upgrade-focused guide for future automated agents and maintainers.

Key runtime pieces:

- Backend app (FastAPI): `agrisense_app/backend/main.py` — the ASGI entrypoint. Run with `uvicorn agrisense_app.backend.main:app`.
- Core logic: `agrisense_app/backend/engine.py` — `RecoEngine` performs rule-based calculations and optional ML blending for water/fertilizer recommendations.
- Persistence: `agrisense_app/backend/data_store.py` — SQLite (`sensors.db`) helpers and schema accessors.
- MQTT & Edge: `agrisense_app/backend/mqtt_bridge.py`, `mqtt_publish.py`, and `agrisense_pi_edge_minimal` for optional edge readers.
- Frontend (React + Vite): `agrisense_app/frontend/farm-fortune-frontend-main`. Built assets are served under `/ui` by the backend when present.

This repo also contains utility scripts, datasets, model artifacts and training/QA scaffolding useful during upgrades.

## Purpose of this file (for future agents)

This file should let an automated agent safely and predictably perform upgrades: run, test, and validate changes without accidentally breaking CI or production. Follow the "Small contract" below and the step-by-step upgrade checklist.

---

## Small contract — guarantees to preserve

When modifying core behavior, preserve backward compatibility and tests.

- Inputs: API endpoints accept JSON sensor readings (see `edge_ingest` for accepted keys). Keep normalization tolerant of earlier key names.
- Outputs: `RecoEngine.recommend(reading: Dict)` must return a dict with at least `{"water_liters": float, "tips": List[str]}`. Extra keys allowed but do not rename/remove required keys.
- Error modes: APIs must return appropriate HTTP status codes and JSON with a `detail` field for machine parsing.
- Tests: Any behavior change must add/update pytest tests. CI runs with `AGRISENSE_DISABLE_ML=1` to avoid heavy ML packages.
- Security: Maintain input validation, CORS protection, and rate limiting
- Fallbacks: Preserve graceful degradation when ML dependencies unavailable

---

## Security Best Practices

### Critical Security Guarantees
1. **Never hardcode secrets** - Use environment variables for:
   - `AGRISENSE_ADMIN_TOKEN`
   - Database credentials
   - API tokens
2. **Input validation** - All endpoints must use Pydantic models
3. **Dependency hygiene** - Regularly audit with `pip-audit`/`npm audit`
4. **Error handling** - Never expose stack traces in production

### Common Vulnerabilities to Monitor
- **PYSEC-2024-110**: scikit-learn (keep ≥1.5.0)
- **PYSEC-2024-232/233**: python-jose (keep ≥3.4.0)
- **GHSA-f96h-pmfr-66vw**: starlette (keep ≥0.47.2)
- Frontend build tool vulnerabilities (Vite ≥7.1.7)

### Security Audit Checklist
✅ Dependency vulnerability scan
✅ Hardcoded secret check
✅ Input validation verification
✅ Error handling review
✅ CORS configuration check
✅ Rate limiting validation

---

## Production Deployment Reference

### Validated Deployment Command
```bash
cd agrisense_app/backend && python -m uvicorn main:app --host 0.0.0.0 --port 8004
```

### Key Health Endpoints
- Health check: `http://localhost:8004/health`
- Ready check: `http://localhost:8004/ready`
- VLM status: `http://localhost:8004/api/vlm/status`

### Frontend Serving
- Built frontend must be served from `/ui` endpoint
- HTML files require `Cache-Control: no-cache` headers

---

## Critical Fixes Reference

### Resolved Issues to Preserve
1. **Backend Import Errors**: 
   - Torch import guards in `weed_management.py`
   - Core module fallback paths in `main.py`
2. **Frontend Issues**:
   - Service worker disabled in production
   - JSX parsing errors resolved
3. **Security Fixes**:
   - scikit-learn upgraded to 1.5.0+
   - python-jose upgraded to 3.4.0+
   - starlette upgraded to 0.47.2+

### Fallback Mechanisms
- ML-dependent features must degrade gracefully
- Rule-based calculations as primary fallback
- Clear error logging when fallbacks activated

---

## ML Workflow

### Training Models
1. **Time-series model**: `python scripts/train_timeseries.py`
2. **Natural Language Model**: `python scripts/train_nlm.py`

### Artifact Management
- Models are saved in `agrisense_app/backend/ml_models/{model_type}/artifacts/`
- Each model must include a `metadata.json` with:
  - `model_version`
  - `trained_on`
  - `commit_hash`
  - `params`

### Smoke Testing
- Run `python scripts/smoke_ml_infer.py` to test the recommendation endpoint

### CI/CD Integration
- ML tests run with `AGRISENSE_DISABLE_ML=1` for fast feedback
- Full training runs are triggered manually

### Updating Models
1. Train new model
2. Update artifacts in versioned directory
3. Update metadata
4. Run smoke tests
5. Update documentation

---

## Agentic AI (Cascade) Guidelines

### When Making Changes
1. Always maintain backward compatibility
2. Preserve existing API contracts
3. Add tests for new functionality
4. Update documentation with changes

### Vulnerability Fixing Protocol
1. Identify vulnerable dependencies
2. Check compatibility with current codebase
3. Update dependency versions in:
   - `agrisense_app/backend/requirements.txt`
   - `agrisense_app/frontend/package.json`
4. Verify no breaking changes

### Enhancement Implementation
1. Follow existing architectural patterns
2. Maintain separation of concerns:
   - Business logic in `engine.py`
   - API endpoints in `main.py`
   - UI components in frontend `src/`
3. Add feature flags for major changes

---

## Upgrade checklist (what an automated agent should do)

1) Pre-flight risk assessment
  - Review `pytest.ini`, CI workflows, and this guide for constraints
  - Run `pip-audit`, `npm audit`, and (if available) `safety check` for Python packages
  - Scan for secrets using `detect-secrets scan` or `git secrets --scan`
  - Verify Pydantic models provide strict validation on all new/modified endpoints
  - Ensure `AGRISENSE_DISABLE_ML=1` is exported for any automated or CI test runs

2) Environment preparation
  - Create or refresh a Python 3.9+ virtual environment:
    ```powershell
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    $env:AGRISENSE_DISABLE_ML='1'
    pip install --upgrade pip wheel setuptools
    pip install -r agrisense_app/backend/requirements.txt
    pip install -r agrisense_app/backend/requirements-dev.txt
    ```
  - Install frontend dependencies: `cd agrisense_app/frontend/farm-fortune-frontend-main && npm install`
  - Launch backend from repo root: `python -m uvicorn agrisense_app.backend.main:app --host 0.0.0.0 --port 8004 --reload`
  - Start frontend dev server: `npm run dev`

3) Automated verification
  - Run backend tests with ML disabled: `$env:AGRISENSE_DISABLE_ML='1'; pytest -q scripts/test_backend_inprocess.py scripts/test_edge_endpoints.py`
  - Execute smoke suites: `python scripts/test_backend_integration.py`, `python scripts/chatbot_http_smoke.py`
  - Hit VLM endpoints and plant-health APIs with sample payloads (`http :8004/api/vlm/status`, `/api/disease/detect`, `/api/weed/analyze`)
  - Re-run `pip-audit`/`npm audit` (or `npm audit --production`) to confirm zero regressions

4) Resilience & performance checks
  - Flip `AGRISENSE_DISABLE_ML` off/on to confirm graceful fallbacks remain functional
  - Run targeted load smoke (e.g., `hey` or `locust`) against `/health`, `/api/disease/detect`, `/api/weed/analyze`
  - Validate edge simulators via `python tools/development/scripts/test_edge_endpoints.py`
  - Inspect backend logs for new warnings or exceptions

5) Documentation & release readiness
  - Update `CHANGELOG.md`, relevant files in `documentation/`, and `PROJECT_BLUEPRINT_UPDATED.md`
  - Add migration notes for any DB/API schema changes
  - Summarize dependency bumps and security outcomes in the PR description
  - Follow PR checklist below

---

## PR checklist (must pass before merge)

1. Update `CHANGELOG.md` or `docs/`
2. Add/update unit tests (run with `AGRISENSE_DISABLE_ML=1`)
3. Run security audit (dependencies, secrets, validation)
4. Verify no hardcoded secrets
5. Add migration notes for DB/API changes
6. For ML changes, include artifact regeneration notes
7. Confirm fallback mechanisms preserved

---

## Agentic AI Access Points

Key entry points for Cascade:
- `agrisense_app/backend/main.py` - API endpoints
- `agrisense_app/backend/engine.py` - Core logic
- `agrisense_app/backend/data_store.py` - Database
- `agrisense_app/backend/weed_management.py` - ML integration
- `agrisense_app/frontend/farm-fortune-frontend-main/src/` - UI components

---

If anything above is unclear or you want additional automation (example CI workflows, focused upgrade scripts, or test scaffolding), tell me which area to expand and I will implement it.
