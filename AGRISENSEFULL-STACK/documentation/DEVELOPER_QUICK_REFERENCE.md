# 🚀 AgriSense Developer Quick Reference Card

**One-Page Cheat Sheet for Developers**

**Version**: 1.0 | **Last Updated**: October 14, 2025

---

## 📦 Quick Start (5 Minutes)

```powershell
# 1. Clone & Navigate
cd "AGRISENSE FULL-STACK/AGRISENSEFULL-STACK"

# 2. Backend Setup
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r agrisense_app/backend/requirements.txt

# 3. Start Backend (Port 8004)
$env:AGRISENSE_DISABLE_ML='1'
python -m uvicorn agrisense_app.backend.main:app --reload --port 8004

# 4. Frontend Setup (New Terminal)
cd agrisense_app/frontend/farm-fortune-frontend-main
npm install
npm run dev  # Port 8080-8082 auto-selected
```

**✅ Verify**: http://localhost:8004/health → `{"status": "healthy"}`

---

## 🔧 Common Commands

### Backend

```powershell
# Run with ML enabled
$env:AGRISENSE_DISABLE_ML='0'
uvicorn agrisense_app.backend.main:app --reload --port 8004

# Run tests
pytest -v                              # All tests
pytest -m integration                  # Integration only
pytest tests/test_e2e_workflow.py     # E2E tests
pytest --cov=agrisense_app             # With coverage

# Security audit
pip-audit

# Format code
black agrisense_app/backend/

# Lint
pylint agrisense_app/backend/
```

### Frontend

```powershell
cd agrisense_app/frontend/farm-fortune-frontend-main

# Development
npm run dev                # Dev server
npm run build              # Production build
npm run preview            # Preview build

# Code quality
npm run typecheck          # TypeScript checking
npm run lint               # ESLint
npm run lint:fix           # Auto-fix issues

# Security
npm audit                  # Vulnerability scan
npm audit fix              # Fix vulnerabilities
```

---

## 🌐 API Endpoints Reference

### Base URL
```
Development: http://localhost:8004
Production: https://api.agrisense.example
```

### Core Endpoints

| Endpoint | Method | Purpose | Request Example |
|----------|--------|---------|-----------------|
| `/health` | GET | Health check | `curl http://localhost:8004/health` |
| `/api/v1/irrigation/recommend` | POST | Get irrigation advice | See below ↓ |
| `/api/v1/crop/recommend` | POST | Get crop recommendation | See below ↓ |
| `/api/v1/disease/detect` | POST | Detect plant disease | See below ↓ |
| `/api/v1/weed/analyze` | POST | Analyze weed image | See below ↓ |
| `/chatbot/ask` | POST | Ask farming question | See below ↓ |
| `/api/edge/ingest` | POST | Ingest sensor data | See below ↓ |

### Quick Examples

#### 1. Irrigation Recommendation
```bash
curl -X POST http://localhost:8004/api/v1/irrigation/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 28.5,
    "humidity": 65,
    "soil_moisture": 42,
    "crop_type": "rice"
  }'
```

**Response**:
```json
{
  "water_liters": 25.0,
  "irrigation_needed": true,
  "confidence": 0.92,
  "tips": ["Water in early morning", "Check soil drainage"]
}
```

#### 2. Crop Recommendation
```bash
curl -X POST http://localhost:8004/api/v1/crop/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "nitrogen": 45,
    "phosphorus": 38,
    "potassium": 52,
    "ph": 6.5,
    "rainfall": 120,
    "temperature": 26
  }'
```

**Response**:
```json
{
  "recommended_crops": ["rice", "wheat", "cotton"],
  "confidence_scores": [0.89, 0.76, 0.68],
  "reasoning": "Soil NPK levels ideal for rice cultivation"
}
```

#### 3. Disease Detection
```bash
curl -X POST http://localhost:8004/api/v1/disease/detect \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "<base64-encoded-image>",
    "crop_type": "tomato"
  }'
```

**Response**:
```json
{
  "disease": "Early Blight",
  "confidence": 0.87,
  "severity": "moderate",
  "treatment": "Apply copper-based fungicide",
  "prevention_tips": ["Improve air circulation", "Avoid overhead watering"]
}
```

#### 4. Chatbot Query
```bash
curl -X POST http://localhost:8004/chatbot/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How to grow tomatoes?",
    "language": "en"
  }'
```

**Response**:
```json
{
  "results": [
    {
      "answer": "Tomato cultivation guide: 1. Soil: Well-drained, pH 6.0-6.8...",
      "confidence": 0.92,
      "source": "cultivation_guide"
    }
  ]
}
```

---

## 🧪 Testing Patterns

### Unit Test Example
```python
# tests/test_engine.py
import pytest
from agrisense_app.backend.engine import RecoEngine

def test_irrigation_recommendation():
    engine = RecoEngine()
    reading = {
        "temperature": 30,
        "humidity": 60,
        "soil_moisture": 35,
        "crop_type": "rice"
    }
    
    result = engine.recommend(reading)
    
    assert result["water_liters"] > 0
    assert result["irrigation_needed"] is True
    assert len(result["tips"]) > 0
```

### Integration Test Example
```python
# tests/test_api.py
from fastapi.testclient import TestClient
from agrisense_app.backend.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_irrigation_endpoint():
    response = client.post("/api/v1/irrigation/recommend", json={
        "temperature": 28,
        "humidity": 65,
        "soil_moisture": 40
    })
    assert response.status_code == 200
    assert "water_liters" in response.json()
```

### Frontend Test Example
```typescript
// src/pages/Dashboard.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Dashboard from './Dashboard';

test('renders dashboard', async () => {
  const queryClient = new QueryClient();
  
  render(
    <QueryClientProvider client={queryClient}>
      <Dashboard />
    </QueryClientProvider>
  );
  
  await waitFor(() => {
    expect(screen.getByText(/Dashboard/i)).toBeInTheDocument();
  });
});
```

---

## 📁 Project Structure (Essential Files)

```
AGRISENSEFULL-STACK/
│
├── agrisense_app/
│   ├── backend/
│   │   ├── main.py                    # ⭐ FastAPI app entry
│   │   ├── engine.py                  # ⭐ Recommendation logic
│   │   ├── disease_model.py           # Disease detection
│   │   ├── weed_management.py         # Weed analysis
│   │   ├── chatbot_service.py         # Chatbot NLP
│   │   ├── data_store.py              # Database layer
│   │   └── requirements.txt           # Python deps
│   │
│   └── frontend/
│       └── farm-fortune-frontend-main/
│           ├── src/
│           │   ├── main.tsx           # ⭐ React entry
│           │   ├── App.tsx            # ⭐ Router & layout
│           │   ├── i18n.ts            # ⭐ i18n config
│           │   ├── pages/             # Route components
│           │   ├── components/        # Reusable UI
│           │   └── locales/           # Translations (5 langs)
│           ├── package.json           # Node deps
│           └── vite.config.ts         # ⭐ Build config
│
├── tests/
│   ├── test_e2e_workflow.py          # ⭐ E2E test suite
│   └── ...
│
├── documentation/
│   ├── API_DOCUMENTATION.md          # ⭐ API reference
│   ├── user/FARMER_GUIDE.md          # ⭐ User manual
│   ├── MONITORING_SETUP.md           # ⭐ Monitoring guide
│   └── ENHANCEMENT_SUMMARY_OCT14_2025.md
│
└── pytest.ini                         # Test config
```

---

## 🐛 Debugging Quick Fixes

### Backend Issues

| Problem | Quick Fix |
|---------|-----------|
| `ModuleNotFoundError` | Activate venv: `.\.venv\Scripts\Activate.ps1` |
| `Port 8004 in use` | Change port: `--port 8005` |
| ML model errors | Disable ML: `$env:AGRISENSE_DISABLE_ML='1'` |
| Database locked | Stop all backends, delete `sensors.db-journal` |
| CORS errors | Check `origins` in `main.py` includes frontend URL |

### Frontend Issues

| Problem | Quick Fix |
|---------|-----------|
| Blank white page | Hard refresh: `Ctrl+Shift+R` |
| i18n errors | Check all 5 locale files have same keys |
| TypeScript errors | Run `npm run typecheck` and fix |
| Build fails | Delete `node_modules`, `rm -rf node_modules`, `npm install` |
| Port occupied | Vite auto-selects next available port |

---

## 🔐 Environment Variables

### Backend (.env)
```bash
# ML Configuration
AGRISENSE_DISABLE_ML=1              # Disable ML models

# Database
DATABASE_PATH=./sensors.db

# Logging
LOG_LEVEL=INFO

# Monitoring
SENTRY_DSN=https://...              # Sentry error tracking
PROMETHEUS_PORT=9090

# Security
AGRISENSE_ADMIN_TOKEN=secret123     # Admin API token
```

### Frontend (.env)
```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8004

# Monitoring
VITE_SENTRY_DSN=https://...

# Feature Flags
VITE_ENABLE_CHATBOT=true
VITE_ENABLE_DISEASE_DETECTION=true
```

---

## 🎨 Code Style Guide

### Python (PEP 8)
```python
# ✅ GOOD
def calculate_irrigation(
    temperature: float,
    humidity: float,
    soil_moisture: float
) -> Dict[str, Any]:
    """
    Calculate irrigation recommendation.
    
    Args:
        temperature: Temperature in Celsius
        humidity: Relative humidity (%)
        soil_moisture: Soil moisture (%)
    
    Returns:
        Dict with water_liters, tips, confidence
    """
    if soil_moisture < 30:
        return {
            "water_liters": 25.0,
            "irrigation_needed": True,
            "confidence": 0.9
        }
    return {"water_liters": 0, "irrigation_needed": False}

# ❌ BAD
def calcIrrig(t,h,s):
    if s<30: return 25
    return 0
```

### TypeScript (Airbnb Style)
```typescript
// ✅ GOOD
interface SensorData {
  temperature: number;
  humidity: number;
  soilMoisture: number;
  timestamp: Date;
}

const fetchSensorData = async (): Promise<SensorData> => {
  const response = await fetch('/api/sensor/latest');
  if (!response.ok) {
    throw new Error('Failed to fetch sensor data');
  }
  return response.json();
};

// ❌ BAD
const fetch_sensor_data = () => {
  return fetch('/api/sensor/latest').then(r => r.json())
}
```

---

## 🌍 Multi-Language Support

### Adding a New Language

1. **Create translation file**: `src/locales/bn.json`
```json
{
  "translation": {
    "app_title": "AgriSense",
    "dashboard": "ড্যাশবোর্ড",
    "smart_irrigation": "স্মার্ট সেচ"
  }
}
```

2. **Update i18n config**: `src/i18n.ts`
```typescript
import bn from './locales/bn.json';

export const languages = [
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'hi', name: 'Hindi', flag: '🇮🇳' },
  { code: 'bn', name: 'Bengali', nativeName: 'বাংলা', flag: '🇧🇩' },
];

i18n.init({
  resources: {
    en: { translation: en.translation },
    hi: { translation: hi.translation },
    bn: { translation: bn.translation },
  },
});
```

3. **Test all pages** with language switcher

### Using Translations in Components
```typescript
import { useTranslation } from 'react-i18next';

export default function Component() {
  const { t } = useTranslation();
  
  return (
    <div>
      <h1>{t('app_title')}</h1>
      <p>{t('welcome_message')}</p>
    </div>
  );
}
```

---

## 📊 Performance Tips

### Backend Optimization
- ✅ Use async/await for I/O operations
- ✅ Cache ML model predictions
- ✅ Add database indexes
- ✅ Use connection pooling
- ✅ Enable gzip compression

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_crop_guide(crop_name: str) -> str:
    """Cached crop guide lookup"""
    return load_from_database(crop_name)
```

### Frontend Optimization
- ✅ Use React.memo for expensive components
- ✅ Lazy load routes with React.lazy()
- ✅ Optimize images (WebP, lazy loading)
- ✅ Use virtual scrolling for lists
- ✅ Code-splitting (already configured)

```typescript
// Lazy loading
const DashboardPage = lazy(() => import('./pages/Dashboard'));

// Memoization
const ExpensiveComponent = React.memo(({ data }) => {
  return <div>{/* expensive render */}</div>;
});
```

---

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] All tests pass: `pytest -v`
- [ ] No TypeScript errors: `npm run typecheck`
- [ ] Security scan: `pip-audit && npm audit`
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] ML models deployed
- [ ] Monitoring configured

### Production Build
```bash
# Backend
pip install -r requirements.txt
python -m uvicorn agrisense_app.backend.main:app --host 0.0.0.0 --port 8004 --workers 4

# Frontend
npm run build
# Serve dist/ with nginx or similar
```

### Health Check
```bash
# Backend
curl http://production-url:8004/health

# Metrics
curl http://production-url:8004/metrics
```

---

## 📚 Documentation Links

- **API Documentation**: `documentation/API_DOCUMENTATION.md`
- **User Guide**: `documentation/user/FARMER_GUIDE.md`
- **Monitoring Setup**: `documentation/MONITORING_SETUP.md`
- **Enhancement Summary**: `documentation/ENHANCEMENT_SUMMARY_OCT14_2025.md`
- **Project Blueprint**: `PROJECT_BLUEPRINT_UPDATED.md`

---

## 🆘 Getting Help

### Internal Resources
1. Read documentation in `documentation/` folder
2. Check `.github/copilot-instructions.md` for agent guidelines
3. Review test examples in `tests/` folder

### External Resources
- **FastAPI**: https://fastapi.tiangolo.com/
- **React**: https://react.dev/
- **Vite**: https://vitejs.dev/
- **pytest**: https://docs.pytest.org/

### Common Questions

**Q: How do I add a new API endpoint?**
A: Add to `agrisense_app/backend/main.py`, define Pydantic models, add tests

**Q: How do I add a new page to frontend?**
A: Create in `src/pages/`, add route to `App.tsx`, add translations

**Q: How do I run just integration tests?**
A: `pytest -m integration`

**Q: How do I enable ML models?**
A: `$env:AGRISENSE_DISABLE_ML='0'` (requires PyTorch/TensorFlow)

**Q: Frontend won't start?**
A: Check if port is free, try `npm install` again, check Node version (18+)

---

**Quick Command Clipboard** 📋

```powershell
# Start everything (copy-paste)
cd "AGRISENSE FULL-STACK/AGRISENSEFULL-STACK"
.\.venv\Scripts\Activate.ps1
$env:AGRISENSE_DISABLE_ML='1'
python -m uvicorn agrisense_app.backend.main:app --reload --port 8004

# In new terminal
cd "AGRISENSE FULL-STACK/AGRISENSEFULL-STACK/agrisense_app/frontend/farm-fortune-frontend-main"
npm run dev
```

---

**Version**: 1.0  
**Last Updated**: October 14, 2025  
**Maintained By**: AgriSense Dev Team

**Print this page for quick reference! 🖨️**
