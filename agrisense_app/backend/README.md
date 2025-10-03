# AgriSense Backend

## Chatbot Endpoint

- **POST /api/chat**: Sends a user message to the NLM service and returns the response.
  - Request body: `{ "message": "user message here" }`
  - Response: `{ "response": "NLM response here" }`

## Machine Learning / Optional Dependencies

The backend includes optional ML-powered features (VLM, NLM, disease models). To avoid forcing heavy ML installs on CI or lightweight developer setups, these dependencies are split into a separate file:

- `agrisense_app/backend/requirements-ml.txt` — install this when you plan to run ML features locally or in a GPU-enabled environment.

To install core backend deps only:

```powershell
.\.venv\Scripts\python.exe -m pip install -r agrisense_app/backend/requirements.txt
```

To install ML deps as well:

```powershell
.\.venv\Scripts\python.exe -m pip install -r agrisense_app/backend/requirements.txt -r agrisense_app/backend/requirements-ml.txt
```



## CI / Pipeline

This repository includes a GitHub Actions workflow that:

- Installs backend dependencies (uses `requirements-dev.txt` if present, otherwise `requirements.txt`).
- Runs pytest with `AGRISENSE_DISABLE_ML=1` to avoid heavy ML startup during CI.
- Optionally builds the frontend if the `agrisense_app/frontend/farm-fortune-frontend-main` project is present.

To run the same steps locally, use the helper script at `scripts/ci_local.ps1`:

```powershell
# from repository root
.\scripts\ci_local.ps1
# to include ML deps (may be slow):
.\scripts\ci_local.ps1 -InstallML
```

The CI uses `AGRISENSE_DISABLE_ML=1` by default so tests remain fast and deterministic in CI.

