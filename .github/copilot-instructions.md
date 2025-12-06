# 🤖 AgriSense - AI Agent Operation Manual

**Last Updated**: December 6, 2025  
**Project Status**: Production Ready with Python 3.12.10 + Multi-Language + Hybrid AI  
**Target Audience**: Future AI Agents (Cascade, Copilot Workspace, etc.)

---

## 📋 Quick Orientation — What This Repo Is

AgriSense is a **full-stack smart agriculture platform** combining FastAPI backend with React + Vite frontend for:
- 🌾 **Smart Irrigation**: ML-powered water management recommendations
- 🌱 **Crop Recommendation**: Soil-based crop selection guidance  
- 🦠 **Plant Disease Detection**: Vision model-based disease identification
- 🌿 **Weed Management**: AI-powered weed detection and treatment recommendations
- 💬 **Agricultural Chatbot**: Natural language farming advice
- 🤖 **Hybrid LLM+VLM Edge AI**: Offline multimodal agricultural intelligence
- 🌍 **Multi-Language Support**: English, Hindi, Tamil, Telugu, Kannada (5 languages)

### 🐍 Current Tech Stack (December 6, 2025)

**Backend Stack:**
- Python 3.12.10 (Latest stable with performance improvements)
- FastAPI 0.123.10 (Security fixes applied)
- NumPy 2.2.6 (with <2.3.0 constraint for opencv compatibility)
- TensorFlow/PyTorch (ML frameworks)
- SQLite 3.x (Local database)
- HuggingFace Hub 0.36.x (Model management)
- Ollama + Phi (LLM for chatbot)
- SCOLD VLM (Computer vision)

**Frontend Stack:**
- React 18.3.1
- Vite 7.2.6 (Build tool)
- TypeScript 5.8.3
- TanStack Query (Data fetching)
- react-i18next (Internationalization)
- Tailwind CSS 3.x

**Deployment:**
- 0 backend dependency conflicts (verified pip check)
- 0 frontend vulnerabilities (verified npm audit)
- Both services tested and running
- Full CI/CD pipeline ready

### Critical Runtime Components

| Component | Location | Purpose | Run Command |
|-----------|----------|---------|-------------|
| **Backend API** | `agrisense_app/backend/main.py` | FastAPI ASGI entrypoint | `uvicorn agrisense_app.backend.main:app --port 8004` |
| **Hybrid AI Engine** | `agrisense_app/backend/hybrid_agri_ai.py` | LLM+VLM multimodal AI (NEW) | Imported by routes |
| **Hybrid AI Routes** | `agrisense_app/backend/routes/hybrid_ai_routes.py` | REST API for hybrid AI (NEW) | Auto-loaded |
| **Core Engine** | `agrisense_app/backend/engine.py` | `RecoEngine` - rule-based + ML recommendations | Imported by main.py |
| **Database** | `agrisense_app/backend/data_store.py` | SQLite helpers (`sensors.db`) | Auto-initialized |
| **MQTT Bridge** | `agrisense_app/backend/mqtt_bridge.py` | IoT device communication | Optional |
| **Edge Readers** | `agrisense_pi_edge_minimal/` | Raspberry Pi sensor readers | Optional |
| **Frontend** | `agrisense_app/frontend/farm-fortune-frontend-main` | React + Vite SPA | `npm run dev` (port 8082) |
| **Ollama Server** | External service | Phi LLM backend (NEW) | `ollama serve` (port 11434) |
| **SCOLD VLM** | External service | Vision model backend (NEW) | Custom startup (port 8001) |

### Project Structure Overview

```
AGRISENSE FULL-STACK/
├── .github/
│   └── copilot-instructions.md      # 👈 You are here
├── AGRISENSEFULL-STACK/              # 🎯 Main workspace
│   ├── agrisense_app/
│   │   ├── backend/                 # FastAPI application
│   │   │   ├── main.py              # API entrypoint
│   │   │   ├── engine.py            # Recommendation engine
│   │   │   ├── data_store.py        # Database layer
│   │   │   ├── disease_model.py     # Disease detection
│   │   │   ├── weed_management.py   # Weed analysis
│   │   │   ├── chatbot_service.py   # NLP chatbot
│   │   │   ├── hybrid_agri_ai.py    # Hybrid LLM+VLM engine (NEW)
│   │   │   ├── requirements.txt     # Python dependencies
│   │   │   ├── routes/              # API route modules (NEW)
│   │   │   │   └── hybrid_ai_routes.py  # Hybrid AI endpoints
│   │   │   └── ml_models/           # Model artifacts
│   │   └── frontend/
│   │       └── farm-fortune-frontend-main/
│   │           ├── src/             # React components
│   │           │   ├── locales/     # i18n translations (5 languages)
│   │           │   ├── pages/       # Route components
│   │           │   ├── components/  # Reusable UI
│   │           │   ├── i18n.ts      # i18next config
│   │           │   └── main.tsx     # React entrypoint
│   │           ├── package.json     # Node dependencies
│   │           └── vite.config.ts   # Vite configuration
│   ├── scripts/                     # Utility scripts
│   │   ├── test_backend_integration.py
│   │   ├── chatbot_http_smoke.py
│   │   └── train_timeseries.py
│   ├── tests/                       # Test suites
│   ├── test_hybrid_ai.py            # Hybrid AI test suite (NEW)
│   ├── examples_hybrid_ai.py        # Hybrid AI usage examples (NEW)
│   ├── start_hybrid_ai.ps1          # Automated startup script (NEW)
│   ├── documentation/               # Project docs
│   ├── PROJECT_BLUEPRINT_UPDATED.md # Architecture blueprint
│   ├── MULTILANGUAGE_IMPLEMENTATION_SUMMARY.md
│   └── pytest.ini                   # Test configuration
└── README.md                        # Top-level README
```

## 🎯 Purpose of This File (For Future AI Agents)

This document enables automated agents to:
1. ✅ **Run the project** from scratch in any environment
2. 🐛 **Debug issues** systematically with known solutions
3. 🚀 **Upgrade dependencies** safely without breaking changes
4. 🔧 **Enhance features** while preserving backward compatibility
5. 📚 **Understand architecture** to make informed decisions

### Agent Capabilities Expected
- File reading/writing
- Terminal command execution (PowerShell on Windows)
- Package manager operations (pip, npm)
- Git operations (optional but helpful)
- Error log interpretation
- Web request testing (HTTP clients)

---

## 🚀 Hybrid AI System (December 2025 - NEW)

### Overview
The Hybrid Agricultural AI combines **Phi LLM** (language understanding) and **SCOLD VLM** (computer vision) for offline-capable multimodal agricultural intelligence. This system can analyze farm images with natural language queries, operate without internet connectivity, and provide actionable agricultural advice.

### Architecture Components

**1. Core Engine** (`hybrid_agri_ai.py` - 900+ lines)
- **Purpose**: Multimodal AI orchestration combining vision + language
- **Key Classes**:
  - `HybridAgriAI`: Main orchestrator
  - `AnalysisType`: Enum (disease_detection, weed_identification, crop_health, pest_detection, soil_analysis, general)
  - `VisualAnalysis`, `TextualAnalysis`, `HybridAnalysis`: Result containers
- **Key Methods**:
  - `analyze_image()`: Pure visual analysis via SCOLD VLM
  - `analyze_text()`: Pure text queries via Phi LLM
  - `analyze_multimodal()`: Combined image+text analysis
  - `get_status()`: System health and component availability
- **Configuration**:
  - Phi LLM: `localhost:11434` (Ollama), model: `phi:latest`
  - SCOLD VLM: `localhost:8001` (custom deployment)
  - Temperature: 0.75, top_p: 0.95, timeout: 45s
  - Max conversation history: 5 turns

**2. REST API Routes** (`routes/hybrid_ai_routes.py` - 400+ lines)
- **Endpoints** (all under `/api/hybrid/`):
  - `POST /analyze` - Multimodal (base64 image + text query)
  - `POST /analyze/upload` - Multimodal (file upload + form data)
  - `POST /text` - Text-only queries
  - `POST /image` - Image-only analysis
  - `GET /status` - Component status
  - `GET /health` - Simple health check
  - `POST /history/clear` - Clear conversation
  - `POST /cache/clear` - Clear response cache

**3. Test Suite** (`test_hybrid_ai.py` - 500+ lines)
- **6 Comprehensive Tests**:
  1. Health check - Service availability
  2. System status - Component configuration
  3. Text analysis - 3 agricultural questions
  4. Image analysis - 3 analysis types
  5. Multimodal analysis - 3 combined scenarios
  6. Conversation history - Context management
- **Test Results**: All 6/6 passing, ~2050ms per test
- **Coverage**: Endpoints, fallbacks, confidence scoring, recommendations

**4. Usage Examples** (`examples_hybrid_ai.py` - 400+ lines)
- **6 Example Patterns**:
  1. Direct Python API usage
  2. HTTP API requests
  3. Image upload analysis
  4. Multi-turn conversations
  5. Batch scenario processing
  6. Field monitoring simulation

**5. Startup Automation** (`start_hybrid_ai.ps1` - 188 lines)
- **Features**:
  - Automatic Ollama check and startup
  - Phi model download if missing
  - Backend launch with health checks
  - Optional frontend startup
  - Background job management
  - Graceful cleanup on exit
- **Usage**: `.\start_hybrid_ai.ps1` or `.\start_hybrid_ai.ps1 -SkipFrontend`

### Capabilities

**Analysis Types**:
- 🦠 **Disease Detection**: Identify plant diseases from leaf images
- 🌱 **Crop Health Assessment**: Overall plant health evaluation
- 🌿 **Weed Identification**: Detect and classify weed species
- 🐛 **Pest Detection**: Identify pest damage and infestations
- 🌾 **Soil Analysis**: Visual soil condition assessment
- 💬 **Natural Language Q&A**: Agricultural advice and guidance

**Key Features**:
- ✅ **Offline-First**: Runs on edge devices without internet
- ✅ **Multimodal**: Combines vision + language understanding
- ✅ **Context-Aware**: Maintains conversation history (5 turns)
- ✅ **Confidence Scoring**: Weighted scores (60% visual, 40% textual)
- ✅ **Actionable Steps**: Extracts treatment recommendations
- ✅ **Graceful Fallbacks**: Works even when components offline
- ✅ **Response Caching**: Efficient repeat query handling

### Quick Start

```powershell
# 1. Start complete system
.\start_hybrid_ai.ps1

# 2. Test individual components
python test_hybrid_ai.py

# 3. Run usage examples
python examples_hybrid_ai.py

# 4. Manual API testing
curl http://localhost:8004/api/hybrid/health

# 5. Text query
curl -X POST http://localhost:8004/api/hybrid/text `
  -H "Content-Type: application/json" `
  -d '{"query": "How to prevent tomato blight?"}'

# 6. Image analysis (with file)
curl -X POST http://localhost:8004/api/hybrid/analyze/upload `
  -F "image=@diseased_leaf.jpg" `
  -F "query=What disease is this?"
```

### Integration Points

**Backend Integration** (main.py lines 5365-5375):
```python
from .routes.hybrid_ai_routes import router as hybrid_ai_router
app.include_router(hybrid_ai_router)
logger.info("✅ Hybrid Agricultural AI routes registered")
```

**Python API Usage**:
```python
from agrisense_app.backend.hybrid_agri_ai import HybridAgriAI, AnalysisType

ai = HybridAgriAI()
result = ai.analyze_multimodal(
    image_data="path/to/plant.jpg",
    text_query="What's wrong with this plant?",
    context={"crop": "tomato", "location": "greenhouse"}
)
```

**HTTP API Usage**:
```python
import requests
response = requests.post(
    "http://localhost:8004/api/hybrid/analyze",
    json={
        "image_base64": base64_image,
        "query": "Identify this disease",
        "context": {"crop": "rice"}
    }
)
```

### Deployment

**Edge Device Setup** (Raspberry Pi, farm servers):
1. Install Ollama: `curl -fsSL https://ollama.ai/install.sh | sh`
2. Pull Phi model: `ollama pull phi:latest`
3. Start Ollama: `ollama serve`
4. Launch backend: `python -m uvicorn agrisense_app.backend.main:app --port 8004`
5. Test: `curl http://localhost:8004/api/hybrid/health`

**Production Considerations**:
- Phi model size: 1.49GB (fits on 2GB+ devices)
- RAM usage: ~2GB for Phi + 1GB for backend
- Response time: 2-5 seconds typical for multimodal analysis
- Storage: 3GB minimum for models + application

### Troubleshooting

**Component Offline**:
- Check Ollama: `curl http://localhost:11434/api/tags`
- Check SCOLD: `curl http://localhost:8001/health`
- System still functional via fallbacks

**Slow Responses**:
- Increase timeout: Set `HYBRID_AI_TIMEOUT=60` environment variable
- Check system resources: Phi needs ~2GB RAM
- Reduce conversation history: Set `HYBRID_AI_MAX_HISTORY=3`

**Model Not Found**:
- Download Phi: `ollama pull phi:latest`
- Verify: `ollama list`

### Performance Metrics

From test suite execution:
- **Health Check**: ~50ms
- **System Status**: ~100ms
- **Text Analysis**: ~2050ms (includes LLM generation)
- **Image Analysis**: ~2100ms (includes VLM processing)
- **Multimodal Analysis**: ~2070ms (parallelized where possible)
- **History Clear**: ~30ms

### Future Enhancements

Planned improvements:
- [ ] Support for multiple VLM models
- [ ] Batch image processing
- [ ] Streaming responses for long analyses
- [ ] Model fine-tuning on farm-specific data
- [ ] Mobile app integration
- [ ] Real-time camera feed analysis
- [ ] Multi-language support in LLM prompts

---

## 🐛 Python 3.12.10 Dependency Management (December 6, 2025)

### Critical Backend Dependencies

**Version Constraints (Must Preserve)**:
```python
# requirements.txt critical constraints
numpy>=2.2.1,<2.3.0              # opencv-python 4.12.0.88 requires <2.3.0
huggingface-hub>=0.36.0,<0.37.0  # Avoid 1.2.0 breaking changes
pwdlib[argon2,bcrypt]==0.2.1     # fastapi-users requires exactly 0.2.1
google-ai-generativelanguage==0.6.15  # API compatibility with 0.6.x
fastapi>=0.123.10                # Security fixes in 0.123.10+
```

**Why These Constraints Matter**:
- NumPy 2.3.0+ breaks opencv-python 4.12.0.88 (import errors)
- HuggingFace Hub 1.2.0 has breaking API changes
- pwdlib 0.3.0 incompatible with fastapi-users[sqlalchemy]
- google-ai-generativelanguage 0.9.0 has API signature changes

### Dependency Conflict Resolution Workflow

**When upgrading dependencies**:
```powershell
# 1. Create upgrade branch
git checkout -b upgrade/dependencies-$(Get-Date -Format 'yyyyMMdd')

# 2. Update requirements.txt with new versions
# Keep constraint comments for future reference

# 3. Test in clean environment
python -m venv .venv-test
.\.venv-test\Scripts\Activate.ps1
pip install --upgrade pip wheel setuptools
pip install -r agrisense_app/backend/requirements.txt

# 4. Verify no conflicts
pip check  # Must show: "No broken requirements found."

# 5. Test imports
python -c "import numpy; import cv2; import fastapi; import huggingface_hub"

# 6. Run test suite
$env:AGRISENSE_DISABLE_ML='1'
pytest -v

# 7. Document changes
# Update PYTHON_312_OPTIMIZATION_REPORT.md or create new dated report
```

### Known Dependency Issues Database

| Package | Bad Version | Issue | Solution |
|---------|-------------|-------|----------|
| numpy | ≥2.3.0 | `ImportError: opencv-python requires numpy<2.3.0` | Pin to `>=2.2.1,<2.3.0` |
| huggingface-hub | ≥1.2.0 | Breaking API changes in model loading | Pin to `>=0.36.0,<0.37.0` |
| pwdlib | ≥0.3.0 | Incompatible with fastapi-users | Pin to `==0.2.1` |
| google-ai-generativelanguage | ≥0.9.0 | API signature changes | Pin to `==0.6.15` |
| scikit-learn | <1.5.0 | PYSEC-2024-110 vulnerability | Upgrade to `≥1.5.0` |

### Frontend Dependency Management

**Critical Frontend Versions**:
```json
{
  "react": "18.3.1",
  "vite": "7.2.6",
  "typescript": "5.8.3",
  "@tanstack/react-query": "^5.x",
  "react-i18next": "^15.x"
}
```

**Update Strategy**:
```powershell
# Security updates only (safer)
npm audit fix

# All updates (test thoroughly)
npm update

# Verify no vulnerabilities
npm audit --production  # Must show: "found 0 vulnerabilities"

# Test build
npm run build
npm run typecheck
```

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

---

## 🚀 Quick Start: Running the Project (Step-by-Step)

### Prerequisites Check
```powershell
# Verify installations
python --version        # Should be 3.9+
node --version          # Should be 18+
npm --version           # Should be 9+
git --version           # Optional but recommended
```

### Step 1: Clone and Navigate
```powershell
# If not already cloned
git clone <repository-url>
cd "AGRISENSE FULL-STACK/AGRISENSEFULL-STACK"
```

### Step 2: Backend Setup
```powershell
# Create virtual environment
python -m venv .venv

# Activate (PowerShell)
.\.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install --upgrade pip wheel setuptools
cd agrisense_app/backend
pip install -r requirements.txt
cd ../..

# Optional: Install dev dependencies for testing
# pip install -r agrisense_app/backend/requirements-dev.txt
```

### Step 3: Start Backend Server
```powershell
# From AGRISENSEFULL-STACK directory
# With ML enabled (requires TensorFlow, PyTorch)
$env:AGRISENSE_DISABLE_ML='0'
python -m uvicorn agrisense_app.backend.main:app --host 0.0.0.0 --port 8004 --reload

# Without ML (faster startup, rule-based only)
$env:AGRISENSE_DISABLE_ML='1'
python -m uvicorn agrisense_app.backend.main:app --host 0.0.0.0 --port 8004 --reload
```

**✅ Backend Ready**: `http://localhost:8004/health` should return `{"status": "healthy"}`

### Step 4: Frontend Setup
```powershell
# Open new terminal
cd "AGRISENSE FULL-STACK/AGRISENSEFULL-STACK/agrisense_app/frontend/farm-fortune-frontend-main"

# Install dependencies
npm install

# Start dev server
npm run dev
```

**✅ Frontend Ready**: Vite will auto-select available port (usually 8082)  
**⚠️ Note**: If ports 8080-8081 are occupied, Vite uses 8082+ automatically

### Step 5: Verify Both Services
```powershell
# Backend health
Invoke-WebRequest -Uri http://localhost:8004/health

# Frontend (open in browser)
Start-Process "http://localhost:8082"
```

### Common Startup Issues & Solutions

| Issue | Symptom | Solution |
|-------|---------|----------|
| **Port conflict** | `Address already in use` | Change port: `--port 8005` or kill process using port |
| **Module not found** | `ModuleNotFoundError: No module named 'fastapi'` | Activate venv: `.\.venv\Scripts\Activate.ps1` |
| **npm install fails** | `ENOENT: no such file` | Verify path: `cd agrisense_app/frontend/farm-fortune-frontend-main` |
| **Blank white page** | Frontend loads then goes white | Hard refresh: `Ctrl+Shift+R` or clear browser cache |
| **ML model errors** | `TensorFlow not found` | Set `$env:AGRISENSE_DISABLE_ML='1'` |
| **Database locked** | `database is locked` | Stop all backend processes, delete `sensors.db.lock` if exists |

---

## 🐛 Debugging Guide: Systematic Troubleshooting

### Debug Level 1: Quick Health Checks
```powershell
# Check if backend is responding
curl http://localhost:8004/health

# Check if frontend is responding  
curl http://localhost:8082

# Check backend logs
# Look for errors in the terminal running uvicorn

# Check frontend logs
# Look for errors in the terminal running npm run dev

# Check browser console
# Open DevTools (F12) and look for JavaScript errors
```

### Debug Level 2: Detailed Diagnostics
```powershell
# Backend diagnostics
$env:AGRISENSE_DISABLE_ML='1'
python -m pytest scripts/test_backend_integration.py -v

# Frontend type checking
cd agrisense_app/frontend/farm-fortune-frontend-main
npm run typecheck

# Frontend linting
npm run lint
```

### Debug Level 3: Common Error Patterns

#### Backend Errors

**1. Import Errors**
```python
# Error: ModuleNotFoundError: No module named 'torch'
# Solution: Either install PyTorch or disable ML
$env:AGRISENSE_DISABLE_ML='1'

# Error: Cannot import name 'RecoEngine' from 'engine'
# Solution: Check PYTHONPATH or run from correct directory
cd AGRISENSEFULL-STACK
python -m uvicorn agrisense_app.backend.main:app
```

**2. Database Errors**
```python
# Error: sqlite3.OperationalError: database is locked
# Solution: Close all backend instances, delete lock file
Stop-Process -Name python -Force
Remove-Item agrisense_app/backend/sensors.db-journal -ErrorAction SilentlyContinue
```

**3. CORS Errors**
```python
# Error: CORS policy blocked
# Solution: Verify CORS configuration in main.py
# Should allow: http://localhost:8082, http://localhost:8080
```

#### Frontend Errors

**1. Blank White Page**
```javascript
// Error: White page, no console errors
// Solution 1: Hard refresh browser (Ctrl+Shift+R)
// Solution 2: Clear browser cache
// Solution 3: Check for i18n initialization race condition

// Error: "The requested module does not provide an export named 'useI18n'"
// Solution: Use 'useTranslation' from 'react-i18next' instead
import { useTranslation } from 'react-i18next';
const { t } = useTranslation();
```

**2. TypeScript Errors**
```typescript
// Error: Type 'number' is not assignable to type 'ReactNode'
// Solution: Convert to string explicitly
<div>{String(sensorData.temperature)}°C</div>

// Error: Property 'width' does not exist on type CloudProps
// Solution: Remove invalid props from Cloud component
<Cloud opacity={0.5} /> // Remove width, depth props
```

**3. Translation Errors**
```javascript
// Error: i18n not initialized before render
// Solution: Wait for i18nPromise in main.tsx
import { i18nPromise } from './i18n';
i18nPromise.then(() => { root.render(<App />) });

// Error: Translation key not found
// Solution: Check if key exists in all locale files
// Files: src/locales/{en,hi,ta,te,kn}.json
```

### Debug Level 4: Advanced Diagnostics

**Backend Memory Profiling**
```powershell
# Install memory profiler
pip install memory-profiler

# Profile a specific endpoint
python -m memory_profiler scripts/profile_endpoint.py
```

**Frontend Performance Analysis**
```powershell
# Build and analyze bundle size
npm run build
npm run analyze  # If available in package.json
```

**Network Traffic Analysis**
```powershell
# Use browser DevTools Network tab
# Filter by: XHR, Fetch
# Look for: Failed requests (red), slow requests (>1s)
```

---

## 🔧 Upgrade Checklist (Automated Agent Workflow)

### Phase 1: Pre-Flight Risk Assessment (5 mins)
```powershell
# Navigate to project root
cd "AGRISENSE FULL-STACK/AGRISENSEFULL-STACK"

# 1. Review constraints
Get-Content pytest.ini
Get-Content .github/copilot-instructions.md

# 2. Security audit - Backend
cd agrisense_app/backend
pip-audit
# Or: pip install safety && safety check

# 3. Security audit - Frontend
cd ../../agrisense_app/frontend/farm-fortune-frontend-main
npm audit --production

# 4. Secret scanning (if tools available)
# detect-secrets scan --baseline .secrets.baseline
# git secrets --scan

# 5. Check current test status
cd ../../../
$env:AGRISENSE_DISABLE_ML='1'
pytest --collect-only  # See what tests exist
```

**🚨 STOP CONDITIONS**: If any of these are true, escalate to human:
- Critical vulnerabilities with no patch available
- Hardcoded secrets found (API keys, passwords)
- Major breaking changes in dependencies (semver major version bump)
- Test failures in main branch (indicates existing issues)

### Phase 2: Environment Preparation (10 mins)
```powershell
# 1. Create fresh virtual environment
python -m venv .venv-upgrade
.\.venv-upgrade\Scripts\Activate.ps1

# 2. Set environment variables
$env:AGRISENSE_DISABLE_ML='1'  # Start without ML for faster iteration
$env:PYTHONPATH="$PWD"

# 3. Install backend dependencies
cd agrisense_app/backend
pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Includes pytest, etc.

# 4. Install frontend dependencies
cd ../../agrisense_app/frontend/farm-fortune-frontend-main
npm ci  # Use ci for reproducible builds

# 5. Verify installations
python -c "import fastapi; print(f'FastAPI: {fastapi.__version__}')"
node -e "console.log('Node:', process.version)"
```

### Phase 3: Launch Services (2 mins)
```powershell
# Terminal 1: Backend
cd "AGRISENSE FULL-STACK/AGRISENSEFULL-STACK"
.\.venv-upgrade\Scripts\Activate.ps1
$env:AGRISENSE_DISABLE_ML='1'
python -m uvicorn agrisense_app.backend.main:app --host 0.0.0.0 --port 8004 --reload

# Terminal 2: Frontend
cd "AGRISENSE FULL-STACK/AGRISENSEFULL-STACK/agrisense_app/frontend/farm-fortune-frontend-main"
npm run dev

# Verify both are running
Start-Sleep -Seconds 5
curl http://localhost:8004/health
curl http://localhost:8082
```

### Phase 4: Automated Verification (15 mins)
```powershell
# 1. Backend unit tests
cd "AGRISENSE FULL-STACK/AGRISENSEFULL-STACK"
$env:AGRISENSE_DISABLE_ML='1'
pytest scripts/test_backend_inprocess.py -v
pytest scripts/test_edge_endpoints.py -v

# 2. Backend integration tests
python scripts/test_backend_integration.py

# 3. Chatbot smoke test
python scripts/chatbot_http_smoke.py

# 4. API endpoint tests (manual curl or automated)
# Disease detection
curl -X POST http://localhost:8004/api/disease/detect `
  -H "Content-Type: application/json" `
  -d '{"image_base64": "..."}'

# Weed analysis
curl -X POST http://localhost:8004/api/weed/analyze `
  -H "Content-Type: application/json" `
  -d '{"image_base64": "..."}'

# VLM status
curl http://localhost:8004/api/vlm/status

# 5. Frontend build test
cd agrisense_app/frontend/farm-fortune-frontend-main
npm run build  # Should complete without errors

# 6. TypeScript validation
npm run typecheck  # Should show 0 errors

# 7. Linting
npm run lint  # Should pass with 0 errors

# 8. Re-run security audits
pip-audit  # Backend
npm audit --production  # Frontend
```

**✅ SUCCESS CRITERIA**:
- All tests pass (100% green)
- No TypeScript errors
- No linting errors
- Security audits show no new vulnerabilities
- Both services start without errors

### Phase 5: Resilience & Performance Checks (10 mins)
```powershell
# 1. Test ML fallback mechanism
# Stop backend, restart with ML enabled
$env:AGRISENSE_DISABLE_ML='0'
python -m uvicorn agrisense_app.backend.main:app --host 0.0.0.0 --port 8004

# If ML loads: Verify predictions work
# If ML fails: Verify fallback to rule-based system

# 2. Load testing (if locust installed)
# locust -f locustfile.py --host=http://localhost:8004

# 3. Edge simulator validation
python tools/development/scripts/test_edge_endpoints.py

# 4. Check logs for warnings
# Look for: deprecation warnings, performance warnings, uncaught exceptions
Get-Content uvicorn.log | Select-String -Pattern "WARNING|ERROR" -Context 2
```

### Phase 6: Documentation & Release (5 mins)
```powershell
# 1. Update CHANGELOG.md
# Add new section with version number, date, and changes

# 2. Update PROJECT_BLUEPRINT_UPDATED.md
# Document any architectural changes

# 3. Update requirements.txt versions
pip freeze > requirements-snapshot.txt
# Manually review and update requirements.txt with new versions

# 4. Create upgrade notes
# In documentation/upgrades/<date>-upgrade-notes.md

# 5. Commit changes
git add .
git commit -m "chore: upgrade dependencies - <summary of changes>"
git push origin <branch-name>
```

---

## 📋 PR Checklist (Must Pass Before Merge)

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

---

## 🎨 Enhancement Guidelines: Adding New Features

### Feature Development Workflow

**1. Planning Phase**
```markdown
# Create feature spec in documentation/features/<feature-name>.md
- Problem statement
- Proposed solution
- Technical approach
- API changes (if any)
- UI mockups (if applicable)
- Testing strategy
- Rollout plan
```

**2. Backend Feature Implementation**
```python
# Location: agrisense_app/backend/<feature_name>.py

# Pattern 1: New ML Model Feature
class NewMLFeature:
    def __init__(self, model_path: str):
        self.model = self._load_model(model_path)
    
    def _load_model(self, path: str):
        """Lazy load with fallback"""
        if os.getenv("AGRISENSE_DISABLE_ML") == "1":
            return None
        try:
            return load_model(path)
        except Exception as e:
            logger.warning(f"ML model load failed: {e}")
            return None
    
    def predict(self, input_data: Dict) -> Dict:
        """Always provide fallback"""
        if self.model:
            return self._ml_predict(input_data)
        return self._rule_based_fallback(input_data)

# Pattern 2: New API Endpoint
@app.post("/api/new-feature", response_model=FeatureResponse)
async def new_feature_endpoint(
    request: FeatureRequest,  # Pydantic model for validation
    current_user: User = Depends(get_current_user)  # Auth if needed
):
    """
    New feature endpoint.
    
    Args:
        request: Validated request with required fields
        
    Returns:
        FeatureResponse: Structured response
        
    Raises:
        HTTPException: 400 for invalid input, 500 for server errors
    """
    try:
        result = feature_logic(request.dict())
        return FeatureResponse(**result)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Feature error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")
```

**3. Frontend Feature Implementation**
```typescript
// Location: agrisense_app/frontend/farm-fortune-frontend-main/src/pages/NewFeature.tsx

import { useTranslation } from 'react-i18next';
import { useQuery, useMutation } from '@tanstack/react-query';

export default function NewFeaturePage() {
  const { t } = useTranslation();  // Always use translations
  
  // Pattern 1: Data fetching
  const { data, isLoading, error } = useQuery({
    queryKey: ['newFeature'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8004/api/new-feature');
      if (!response.ok) throw new Error('Network error');
      return response.json();
    },
    staleTime: 30000,  // 30s
  });
  
  // Pattern 2: Data mutation
  const mutation = useMutation({
    mutationFn: async (formData: FormData) => {
      const response = await fetch('http://localhost:8004/api/new-feature', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      return response.json();
    },
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['newFeature'] });
    },
  });
  
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold">{t('new_feature_title')}</h1>
      {/* Component implementation */}
    </div>
  );
}
```

**4. Translation Updates**
```json
// Add to ALL locale files: src/locales/{en,hi,ta,te,kn}.json
{
  "translation": {
    "new_feature_title": "New Feature Title",
    "new_feature_description": "Description of the feature",
    "new_feature_button": "Action Button",
    "new_feature_success": "Operation successful",
    "new_feature_error": "Operation failed"
  }
}
```

**5. Testing**
```python
# Backend test: tests/test_new_feature.py
import pytest
from fastapi.testclient import TestClient
from agrisense_app.backend.main import app

client = TestClient(app)

def test_new_feature_endpoint():
    """Test new feature endpoint"""
    response = client.post("/api/new-feature", json={
        "input_field": "test_value"
    })
    assert response.status_code == 200
    assert "result" in response.json()

def test_new_feature_validation():
    """Test input validation"""
    response = client.post("/api/new-feature", json={
        "invalid_field": "test"
    })
    assert response.status_code == 400
    assert "detail" in response.json()

def test_new_feature_ml_fallback():
    """Test ML fallback behavior"""
    import os
    os.environ["AGRISENSE_DISABLE_ML"] = "1"
    response = client.post("/api/new-feature", json={
        "input_field": "test_value"
    })
    assert response.status_code == 200
    # Should still work with rule-based fallback
```

```typescript
// Frontend test: src/pages/NewFeature.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import NewFeaturePage from './NewFeature';

const queryClient = new QueryClient();

test('renders new feature page', async () => {
  render(
    <QueryClientProvider client={queryClient}>
      <NewFeaturePage />
    </QueryClientProvider>
  );
  
  await waitFor(() => {
    expect(screen.getByText(/new feature title/i)).toBeInTheDocument();
  });
});
```

### Feature Integration Checklist
- [ ] Backend endpoint implemented with Pydantic validation
- [ ] Frontend page/component implemented with translations
- [ ] Translations added to all 5 language files
- [ ] Unit tests written for backend (pytest)
- [ ] Integration tests for API endpoints
- [ ] Frontend tests if complex logic (optional)
- [ ] Error handling for all edge cases
- [ ] ML fallback implemented (if ML-dependent)
- [ ] Documentation updated (feature spec, API docs)
- [ ] Manually tested in browser (all languages)
- [ ] Performance impact assessed
- [ ] Security review completed

---

## 📚 Knowledge Base: Common Scenarios

### Scenario 1: Adding a New Language
```typescript
// 1. Create translation file
// src/locales/bn.json (Bengali example)
{
  "translation": {
    "app_title": "AgriSense",
    "app_tagline": "স্থায়িত্বশীল কৃষির জন্য একটি স্মার্ট কৃষি সমাধান",
    // ... 150+ keys
  }
}

// 2. Update i18n config
// src/i18n.ts
import bn from './locales/bn.json';

export const languages = [
  // ... existing languages
  { code: 'bn', name: 'Bengali', nativeName: 'বাংলা', flag: '🇧🇩' },
];

i18n.init({
  resources: {
    // ... existing
    bn: { translation: bn.translation },
  },
});

// 3. Test all pages with new language
// 4. Add to documentation
```

### Scenario 2: Upgrading a Major Dependency

**Backend Example: FastAPI 0.x → 1.x**
```powershell
# 1. Check changelog
# Read: https://github.com/tiangolo/fastapi/releases

# 2. Create upgrade branch
git checkout -b upgrade/fastapi-1.x

# 3. Update requirements.txt
# fastapi>=0.115.6 → fastapi>=1.0.0

# 4. Install and test
pip install -r requirements.txt
pytest -v

# 5. Fix breaking changes
# - Check for deprecated imports
# - Update middleware syntax if changed
# - Test all endpoints

# 6. Update documentation
# Note breaking changes in CHANGELOG.md
```

**Frontend Example: React 18 → 19**
```powershell
# 1. Check upgrade guide
# Read: https://react.dev/blog/2024/04/25/react-19

# 2. Update package.json
# "react": "^18.3.1" → "react": "^19.0.0"
# "react-dom": "^18.3.1" → "react-dom": "^19.0.0"

# 3. Install and test
npm install
npm run build
npm run typecheck

# 4. Fix breaking changes
# - Update deprecated lifecycle methods
# - Fix SSR if applicable
# - Test all routes

# 5. Update documentation
```

### Scenario 3: Debugging a Production Issue

**Backend Debug Process**
```powershell
# 1. Check logs
Get-Content uvicorn.log -Tail 100

# 2. Enable debug logging
# In main.py, temporarily:
import logging
logging.basicConfig(level=logging.DEBUG)

# 3. Reproduce locally
curl -X POST http://localhost:8004/api/problematic-endpoint `
  -H "Content-Type: application/json" `
  -d @test_payload.json

# 4. Add detailed logging
logger.debug(f"Input: {input_data}")
logger.debug(f"Intermediate: {intermediate_result}")
logger.debug(f"Output: {output}")

# 5. Use Python debugger
import pdb; pdb.set_trace()  # Add at problem point
# Then: python -m uvicorn ... (will drop to debugger)
```

**Frontend Debug Process**
```javascript
// 1. Check browser console (F12)
// Look for: errors, warnings, failed network requests

// 2. Enable verbose logging
// In component:
console.log('[NewFeature] Props:', props);
console.log('[NewFeature] State:', state);
console.log('[NewFeature] API response:', data);

// 3. Use React DevTools
// Install: React Developer Tools extension
// Inspect: Component props, state, hooks

// 4. Check network tab
// Look for: failed requests, slow requests, wrong payloads

// 5. Use debugger
debugger;  // Will pause execution in DevTools
```

### Scenario 4: Performance Optimization

**Backend Performance**
```python
# 1. Profile endpoints
from fastapi import Request
import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"{request.url.path}: {process_time:.3f}s")
    return response

# 2. Identify slow queries
# Use SQLite EXPLAIN QUERY PLAN

# 3. Add caching
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_computation(param: str) -> Dict:
    # Cached for repeated calls
    pass

# 4. Use async where possible
async def fetch_external_api():
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

**Frontend Performance**
```typescript
// 1. Use React.memo for expensive components
const ExpensiveComponent = React.memo(({ data }) => {
  // Only re-renders if data changes
  return <div>{/* ... */}</div>;
});

// 2. Lazy load routes
const DashboardPage = lazy(() => import('./pages/Dashboard'));

// 3. Optimize images
// Use WebP format, lazy loading
<img src="image.webp" loading="lazy" alt="..." />

// 4. Reduce bundle size
npm run build -- --analyze  # See what's large
// Then: Consider code splitting, tree shaking

// 5. Use virtualization for large lists
import { useVirtualizer } from '@tanstack/react-virtual';
```

### Scenario 5: Security Incident Response

**Vulnerability Detected**
```powershell
# 1. Assess severity
npm audit  # Or: pip-audit
# Read: CVE details, CVSS score, exploit availability

# 2. Check if exploitable in your context
# - Is the vulnerable code path used?
# - Are there mitigating factors?
# - Is there a workaround?

# 3. Immediate mitigation (if critical)
# - Disable affected feature
# - Add input filtering
# - Rate limit endpoint

# 4. Apply patch
npm update <package>  # Or: pip install --upgrade <package>

# 5. Verify fix
npm audit  # Should show vulnerability resolved

# 6. Deploy urgently
# Follow expedited deployment process

# 7. Post-incident
# - Document in security log
# - Update dependency policy
# - Consider automated scanning
```

---

## 🤝 Agentic AI Access Points

### Key Entry Points for AI Agents

**Backend Core**
| File | Purpose | When to Modify |
|------|---------|----------------|
| `agrisense_app/backend/main.py` | API endpoints, middleware, CORS | Adding new routes, changing API structure |
| `agrisense_app/backend/engine.py` | Business logic, RecoEngine | Changing recommendation algorithms |
| `agrisense_app/backend/data_store.py` | Database operations | Adding tables, changing schema |
| `agrisense_app/backend/disease_model.py` | Disease detection ML | Updating disease model |
| `agrisense_app/backend/weed_management.py` | Weed detection ML | Updating weed model |
| `agrisense_app/backend/chatbot_service.py` | NLP chatbot | Improving chatbot responses |

**Frontend Core**
| File | Purpose | When to Modify |
|------|---------|----------------|
| `src/main.tsx` | App entrypoint, i18n init | Changing app initialization |
| `src/App.tsx` | Routing, layout | Adding new routes |
| `src/i18n.ts` | i18n configuration | Adding languages |
| `src/components/Navigation.tsx` | Top nav bar | Changing navigation |
| `src/pages/*.tsx` | Page components | Adding features to pages |
| `src/locales/*.json` | Translations | Adding/updating text |

**Configuration & Infrastructure**
| File | Purpose | When to Modify |
|------|---------|----------------|
| `requirements.txt` | Python dependencies | Upgrading backend packages |
| `package.json` | Node dependencies | Upgrading frontend packages |
| `pytest.ini` | Test configuration | Changing test behavior |
| `vite.config.ts` | Build configuration | Changing build process |
| `.github/copilot-instructions.md` | This file! | Updating agent guidelines |

### Agent Collaboration Protocol

**When to Ask for Human Review**
- 🚨 **Critical security vulnerabilities** with no clear patch
- 🚨 **Breaking API changes** that affect external integrations
- 🚨 **Database migrations** that could cause data loss
- ⚠️ **Major architectural changes** (e.g., switching databases)
- ⚠️ **Performance degradation** >20% in benchmarks
- ⚠️ **Test failures** that aren't understood after debugging

**When to Proceed Autonomously**
- ✅ **Dependency patches** within same major version
- ✅ **Adding translations** to existing keys
- ✅ **Bug fixes** with existing tests
- ✅ **Documentation updates**
- ✅ **Code formatting** and linting
- ✅ **Adding unit tests**

---

## 📞 Support & Resources

### Internal Documentation
- **Architecture**: `PROJECT_BLUEPRINT_UPDATED.md`
- **Multi-Language**: `MULTILANGUAGE_IMPLEMENTATION_SUMMARY.md`
- **Deployment**: `DEPLOYMENT_GUIDE.md`
- **Testing**: `TESTING_README.md`
- **VLM Features**: `VLM_INTEGRATION_SUMMARY.md`

### External Resources
- **FastAPI**: https://fastapi.tiangolo.com/
- **React**: https://react.dev/
- **Vite**: https://vitejs.dev/
- **react-i18next**: https://react.i18next.com/
- **TanStack Query**: https://tanstack.com/query/latest
- **Tailwind CSS**: https://tailwindcss.com/

### Quick Commands Reference
```powershell
# Backend
uvicorn agrisense_app.backend.main:app --reload  # Dev mode
pytest -v  # Run tests
pip-audit  # Security scan

# Frontend
npm run dev  # Dev server
npm run build  # Production build
npm run typecheck  # Type checking
npm audit  # Security scan

# Monitoring
curl http://localhost:8004/health  # Backend health
curl http://localhost:8004/api/vlm/status  # VLM status
```

---

## ✅ Final Checklist: Agent Self-Assessment

Before completing any task, verify:
- [ ] All tests pass (0 failures)
- [ ] No TypeScript errors (0 errors)
- [ ] No security regressions (npm/pip audit clean)
- [ ] Documentation updated (if applicable)
- [ ] Backward compatibility preserved
- [ ] ML fallbacks work (test with AGRISENSE_DISABLE_ML=1)
- [ ] All 5 languages work (test language switcher)
- [ ] Browser console clean (no errors)
- [ ] Services start without errors
- [ ] Manual testing completed (if UI changes)

---

---

## 🎓 Critical Lessons Learned (Issue History)

### October 12, 2025: Chatbot Cultivation Guide Fix

**Problem**: Chatbot returned just crop name ("carrot" - 6 chars) instead of full cultivation guide (1,600+ chars).

**Symptom**: 
```powershell
$body = @{ question = "carrot" } | ConvertTo-Json
$response = Invoke-WebRequest -Uri "http://localhost:8004/chatbot/ask" -Method POST -Body $body -ContentType "application/json"
# Expected: 1,609 character guide
# Actual: 6 characters ("carrot")
```

**Root Cause**: `_get_crop_cultivation_guide()` function in `agrisense_app/backend/main.py` was **reloading** `chatbot_qa_pairs.json` from disk instead of using the in-memory `_chatbot_answers` array that gets populated during startup.

**Investigation Steps Taken**:
1. ✅ Verified JSON file contains all 48 cultivation guides (it did)
2. ✅ Verified guides match pattern "cultivation guide" + crop name (they did)
3. ✅ Tested backend endpoint directly (returned just crop name)
4. ❌ Initial assumption: Guides weren't in the file (WRONG)
5. ✅ Actual issue: Function was searching wrong data source

**The Fix**:
```python
# ❌ WRONG APPROACH: Reloading from disk
def _get_crop_cultivation_guide(crop_name: str) -> Optional[str]:
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    qa_pairs_path = os.path.join(backend_dir, "chatbot_qa_pairs.json")
    with open(qa_pairs_path, "r", encoding="utf-8") as f:
        qa_data = json.load(f)  # Creates separate data source!
    answers = qa_data.get("answers", [])
    # Search in answers loaded from file...

# ✅ CORRECT APPROACH: Using in-memory array
def _get_crop_cultivation_guide(crop_name: str) -> Optional[str]:
    """Retrieve detailed cultivation guide from loaded chatbot answers."""
    global _chatbot_answers
    
    if _chatbot_answers is None or len(_chatbot_answers) == 0:
        logger.warning("Chatbot answers not loaded yet")
        return None
    
    crop_normalized = crop_name.lower().strip()
    
    # Search in already-loaded, processed answers
    for answer in _chatbot_answers:
        answer_lower = str(answer).lower()
        if "cultivation guide" in answer_lower and crop_normalized in answer_lower:
            logger.info(f"Found cultivation guide for crop: {crop_name}")
            return str(answer)
    
    logger.info(f"No cultivation guide found for crop: {crop_name}")
    return None
```

**Why This Matters**:
- `_chatbot_answers` goes through `_clean_text()` normalization
- `_chatbot_answers` is L2-normalized for embeddings
- File reload bypasses the entire data pipeline
- Multiple data sources = inconsistency bugs

**Prevention Checklist**:
- [ ] Always check if data is already loaded in memory before file I/O
- [ ] Use global variables that are pre-loaded at startup
- [ ] Add integration tests that verify answer length (not just presence)
- [ ] Test chatbot endpoints after ANY modifications to main.py
- [ ] Include debug logging to trace data source

**Verification Test**:
```powershell
# Test multiple crops for proper guide length
$testCrops = @("carrot", "watermelon", "strawberry", "tomato", "rice")
foreach ($crop in $testCrops) {
    $body = @{ question = $crop } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "http://localhost:8004/chatbot/ask" -Method POST -Body $body -ContentType "application/json"
    $jsonResp = $response.Content | ConvertFrom-Json
    $answerLength = $jsonResp.results[0].answer.Length
    if ($answerLength -lt 1000) {
        Write-Host "❌ FAILED: $crop returned only $answerLength chars (expected 1500+)"
    } else {
        Write-Host "✅ PASSED: $crop returned $answerLength chars"
    }
}
```

**Key Takeaway**: When debugging, always verify **data flow** - where data comes from matters as much as what data exists.

---

### October 12, 2025: Vite Server Persistence Issue

**Problem**: Vite dev server showed "ready" message but immediately exited, leaving port unresponsive.

**Symptom**:
```powershell
npm run dev
# Output: "VITE v7.1.7 ready in 2112 ms"
# Then: Terminal returns to prompt (exit code 1)
# Result: Port 8080 not listening
```

**Root Cause**: Using `run_in_terminal` with `isBackground=true` in PowerShell doesn't keep npm processes alive. The pipeline terminates when command completes initial output.

**Failed Attempts**:
1. ❌ Multiple `run_in_terminal` calls with different parameters
2. ❌ Adding `Start-Sleep` after npm run dev
3. ❌ Using `Tee-Object` to capture output
4. ❌ Opening new PowerShell window with `Start-Process`

**The Solution**: Use PowerShell `Start-Job`
```powershell
# ✅ CORRECT: Start-Job keeps process running
cd "AGRISENSE FULL-STACK/AGRISENSEFULL-STACK/agrisense_app/frontend/farm-fortune-frontend-main"
Start-Job -ScriptBlock { 
    Set-Location "AGRISENSE FULL-STACK/AGRISENSEFULL-STACK/agrisense_app/frontend/farm-fortune-frontend-main"
    npm run dev 
} | Out-Null
Start-Sleep -Seconds 8  # Wait for Vite startup

# Verify it's running
Invoke-WebRequest -Uri http://localhost:8080

# Check job status
Get-Job | Format-Table

# View job output
Get-Job | ForEach-Object { Receive-Job -Job $_ | Select-Object -Last 30 }
```

**Why This Works**:
- `Start-Job` creates true background process
- Process runs in isolated session
- Doesn't terminate when output stops
- Can be monitored with `Get-Job` and `Receive-Job`

**Same Pattern for Backend**:
```powershell
Start-Job -ScriptBlock { 
    Set-Location "AGRISENSE FULL-STACK/AGRISENSEFULL-STACK"
    & .\.venv\Scripts\python.exe -m uvicorn agrisense_app.backend.main:app --host 0.0.0.0 --port 8004 
} | Out-Null
Start-Sleep -Seconds 12  # Backend needs longer startup
```

**Debugging Background Jobs**:
```powershell
# List all jobs
Get-Job

# Get output from specific job
Receive-Job -Job $job

# Stop all jobs
Get-Job | Stop-Job
Get-Job | Remove-Job

# Kill processes if jobs fail
Get-Process | Where-Object { $_.ProcessName -eq "python" } | Stop-Process -Force
Get-Process | Where-Object { $_.ProcessName -like "*node*" } | Stop-Process -Force
```

**Key Takeaway**: For long-running dev servers in Windows PowerShell, always use `Start-Job` instead of direct terminal commands.

---

## 🔍 Advanced Debugging Patterns

### Pattern 1: Data Source Mismatch
**Symptom**: Function returns wrong/empty data despite file containing correct data.

**Debug Steps**:
1. Verify file contents: `Get-Content file.json | ConvertFrom-Json`
2. Check if data loaded in memory: Search for global variable assignments
3. Add logging to trace data source: `logger.debug(f"Using data from: {source}")`
4. Compare file data vs. in-memory data
5. Check for data transformation functions (e.g., `_clean_text()`)

**Solution Pattern**: Always prefer in-memory data over file reloading.

---

### Pattern 2: Process Persistence in PowerShell
**Symptom**: Background process shows "ready" but exits immediately.

**Debug Steps**:
1. Check if process still running: `Get-Process -Name python` or `Get-Process -Name node`
2. Try direct terminal execution to see full output
3. Check exit codes and error messages
4. Test with `Start-Job` instead of direct command

**Solution Pattern**: Use `Start-Job` for dev servers that need to stay running.

---

### Pattern 3: API Returns Wrong Format
**Symptom**: API returns data but not in expected structure.

**Debug Steps**:
```powershell
# 1. Test endpoint directly
$body = @{ field = "value" } | ConvertTo-Json
$response = Invoke-WebRequest -Uri "http://localhost:8004/endpoint" -Method POST -Body $body -ContentType "application/json"

# 2. Examine full response
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10

# 3. Check response headers
$response.Headers

# 4. Verify Pydantic models in backend code
# Look for: response_model=SomeModel in endpoint definition

# 5. Add backend logging
logger.debug(f"Response structure: {response.dict()}")
```

**Solution Pattern**: Validate Pydantic models match expected frontend structure.

---

## 🛡️ Security & Vulnerability Management

### Known Issues to Monitor

#### Backend Dependencies
```powershell
# Check for vulnerabilities
pip-audit

# Update specific package
pip install --upgrade package-name

# Verify no regressions
pytest -v
```

**Critical Packages**:
- `fastapi` - Keep ≥ 0.115.6
- `starlette` - Keep ≥ 0.47.2 (GHSA-f96h-pmfr-66vw)
- `scikit-learn` - Keep ≥ 1.5.0 (PYSEC-2024-110)
- `python-jose` - Keep ≥ 3.4.0 (PYSEC-2024-232/233)

#### Frontend Dependencies
```powershell
# Check for vulnerabilities
npm audit

# Update specific package
npm update package-name

# Verify build still works
npm run build
npm run typecheck
```

**Critical Packages**:
- `vite` - Keep ≥ 7.1.7
- `react` - Keep ≥ 18.3.1
- `react-dom` - Keep ≥ 18.3.1

### Hardcoded Secret Detection
```powershell
# Manual search for common patterns
Select-String -Path .\**\*.py,.\**\*.ts,.\**\*.tsx -Pattern "api_key|password|secret|token" -Context 1

# Check for .env files in git
git ls-files | Select-String -Pattern "\.env$"

# Verify .gitignore includes sensitive files
Get-Content .gitignore | Select-String -Pattern "\.env|secrets|*.key"
```

---

## 📊 Performance Optimization Guide

### Backend Profiling
```python
# Add timing middleware
import time
from fastapi import Request

@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    response.headers["X-Process-Time"] = str(duration)
    logger.info(f"{request.method} {request.url.path}: {duration:.3f}s")
    return response
```

### Frontend Bundle Analysis
```powershell
# Install analyzer
npm install --save-dev rollup-plugin-visualizer

# Update vite.config.ts
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  plugins: [
    react(),
    visualizer({ open: true })
  ]
});

# Build and analyze
npm run build
# Opens bundle visualization in browser
```

### Database Query Optimization
```python
# Enable SQLite query logging
import sqlite3
sqlite3.enable_callback_tracebacks(True)

# Use EXPLAIN QUERY PLAN
cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM table WHERE ...")
```

---

## 🔄 Continuous Integration Checklist

### Pre-Commit Checks
```powershell
# 1. Format code
black agrisense_app/backend/
prettier --write "agrisense_app/frontend/**/*.{ts,tsx}"

# 2. Run linters
pylint agrisense_app/backend/
cd agrisense_app/frontend/farm-fortune-frontend-main && npm run lint

# 3. Type checking
mypy agrisense_app/backend/
cd agrisense_app/frontend/farm-fortune-frontend-main && npm run typecheck

# 4. Run tests
$env:AGRISENSE_DISABLE_ML='1'
pytest -v

# 5. Security scan
pip-audit
npm audit

# 6. Test chatbot critical functionality
# (See verification test in Lessons Learned section)
```

---

**Document Version**: 4.0  
**Last Updated**: December 4, 2025  
**Maintained By**: AI Agents + Human Maintainers  
**Status**: Production Ready with Hybrid AI ✅
**Latest Addition**: Hybrid LLM+VLM Edge AI system fully deployed

### Recent Updates
- ✅ Added Hybrid Agricultural AI system (December 4, 2025)
  - 900+ line multimodal AI engine combining Phi LLM + SCOLD VLM
  - 400+ line REST API with 8 endpoints
  - 500+ line comprehensive test suite (6/6 tests passing)
  - 400+ line usage examples covering 6 patterns
  - 188 line automated startup script
  - Complete offline-capable edge AI deployment
- ✅ Fixed PowerShell script analyzer warnings in start_hybrid_ai.ps1
- ✅ Added comprehensive debugging patterns for data source mismatches
- ✅ Documented PowerShell job management for persistent processes
- ✅ Added security vulnerability tracking section
- ✅ Included performance optimization guide
- ✅ Added CI/CD pre-commit checklist

### Hybrid AI System Summary
**Total New Code**: ~2,400 lines across 5 files
- `hybrid_agri_ai.py`: Core multimodal engine
- `routes/hybrid_ai_routes.py`: REST API endpoints
- `test_hybrid_ai.py`: Comprehensive test suite
- `examples_hybrid_ai.py`: Usage patterns and examples
- `start_hybrid_ai.ps1`: Automated deployment script

**Capabilities**:
- Disease detection from plant images
- Pest and weed identification
- Crop health assessment
- Soil condition analysis
- Natural language agricultural Q&A
- Multimodal image + text queries
- Offline operation on edge devices
- Conversation context management
- Actionable treatment recommendations

**Verified Working**:
- ✅ Backend healthy on port 8004
- ✅ Ollama serving Phi model (1.49GB)
- ✅ All 8 hybrid API endpoints responding
- ✅ Test suite: 6/6 tests passing
- ✅ Phi LLM responding correctly
- ✅ Fallback handling functional
- ✅ Startup automation complete

### Future AI Agent Guidelines
When encountering new issues:
1. Document symptom, root cause, and solution in this file
2. Add verification test that catches the issue
3. Update relevant checklists
4. Add code patterns (both wrong and correct approaches)
5. Include PowerShell commands used for debugging

This document is a **living guide** - update it after every significant debugging session or architectural change.
