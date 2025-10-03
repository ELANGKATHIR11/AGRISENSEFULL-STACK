# 🚀 AgriSense Quick Reference Card for AI Agents

**Last Updated**: October 2, 2025  
**For**: Rapid agent orientation and common tasks

---

## ⚡ 30-Second Orientation

```
PROJECT: AgriSense - Smart Agriculture Platform
STACK: FastAPI (Python) + React (TypeScript) + Vite
PORTS: Backend 8004 | Frontend 8082
LANGUAGES: 5 (English, Hindi, Tamil, Telugu, Kannada)
STATUS: Production Ready ✅
```

---

## 🎯 Most Common Agent Tasks

### 1. Start the Project (5 mins)
```powershell
# Backend
cd "AGRISENSE FULL-STACK/AGRISENSEFULL-STACK"
.venv\Scripts\Activate.ps1
$env:AGRISENSE_DISABLE_ML='1'
python -m uvicorn agrisense_app.backend.main:app --port 8004 --reload

# Frontend (new terminal)
cd agrisense_app/frontend/farm-fortune-frontend-main
npm run dev
```

**Verify**: 
- Backend: http://localhost:8004/health
- Frontend: http://localhost:8082

---

### 2. Fix Blank White Page (2 mins)
```powershell
# Cause: i18n race condition or cache
# Solution 1: Hard refresh browser (Ctrl+Shift+R)
# Solution 2: Check browser console for errors
# Solution 3: Verify i18nPromise in main.tsx
```

**Common Error**: `useI18n not exported`  
**Fix**: Change to `import { useTranslation } from 'react-i18next'`

---

### 3. Run Tests (3 mins)
```powershell
# Backend tests (ML disabled)
$env:AGRISENSE_DISABLE_ML='1'
pytest scripts/test_backend_integration.py -v

# Frontend type check
cd agrisense_app/frontend/farm-fortune-frontend-main
npm run typecheck
```

**Expected**: 0 errors, all tests green ✅

---

### 4. Check for Vulnerabilities (2 mins)
```powershell
# Backend
cd agrisense_app/backend
pip-audit

# Frontend
cd agrisense_app/frontend/farm-fortune-frontend-main
npm audit --production
```

**Action if found**: See Section "Security Incident Response"

---

### 5. Add New Translation Key (5 mins)
```json
// Add to ALL files: src/locales/{en,hi,ta,te,kn}.json
{
  "translation": {
    "your_new_key": "Translation text"
  }
}
```

```typescript
// Use in component
import { useTranslation } from 'react-i18next';
const { t } = useTranslation();
<div>{t('your_new_key')}</div>
```

---

## 🐛 Emergency Debug Commands

### Backend Not Starting
```powershell
# Check if port in use
Get-NetTCPConnection -LocalPort 8004

# Kill process on port
Stop-Process -Id (Get-NetTCPConnection -LocalPort 8004).OwningProcess -Force

# Check Python imports
python -c "import fastapi; print('OK')"
```

### Frontend Not Starting
```powershell
# Clear node_modules and reinstall
Remove-Item node_modules -Recurse -Force
Remove-Item package-lock.json
npm install

# Check Node version
node --version  # Should be 18+
```

### Database Locked
```powershell
# Stop all Python processes
Stop-Process -Name python -Force

# Remove lock file
Remove-Item agrisense_app/backend/sensors.db-journal -ErrorAction SilentlyContinue

# Restart backend
```

---

## 📊 Health Check Matrix

| Endpoint | Expected Response | Action if Failed |
|----------|-------------------|------------------|
| `GET /health` | `{"status": "healthy"}` | Check backend logs |
| `GET /ready` | `{"ready": true}` | Check database connection |
| `GET /api/vlm/status` | `{"vlm_available": bool}` | Check ML dependencies |
| `http://localhost:8082` | React app loads | Check frontend console |

---

## 🔧 Common Fix Patterns

### Pattern 1: Import Error
```python
# Error: ModuleNotFoundError
# Fix: Activate venv or install package
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Pattern 2: TypeScript Error
```typescript
// Error: Type 'X' not assignable to 'Y'
// Fix: Add explicit type conversion
String(numberValue)  // For JSX
value as SomeType    // For type assertions
```

### Pattern 3: CORS Error
```python
# Error: CORS policy blocked
# Fix: Add origin to main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8082"],
)
```

---

## 📁 Critical File Locations

### Backend
```
agrisense_app/backend/
├── main.py              # API endpoints ⭐
├── engine.py            # Business logic ⭐
├── data_store.py        # Database
├── disease_model.py     # ML models
├── weed_management.py   # ML models
└── requirements.txt     # Dependencies ⭐
```

### Frontend
```
agrisense_app/frontend/farm-fortune-frontend-main/
├── src/
│   ├── main.tsx         # App entry ⭐
│   ├── App.tsx          # Routing ⭐
│   ├── i18n.ts          # i18n config ⭐
│   ├── locales/         # Translations ⭐
│   ├── pages/           # Route components
│   └── components/      # Reusable UI
├── package.json         # Dependencies ⭐
└── vite.config.ts       # Build config
```

---

## 🚨 When to Escalate to Human

**Immediate Escalation** (Critical):
- 🔴 Critical security vulnerability (CVSS >7.0)
- 🔴 Database migration required
- 🔴 Breaking API changes that affect external systems
- 🔴 Data loss risk

**Schedule Review** (Important):
- 🟡 Major dependency upgrade (semver major version)
- 🟡 Performance degradation >20%
- 🟡 Test failures not understood after 30 mins
- 🟡 Architectural change proposal

**Proceed Autonomously** (Safe):
- 🟢 Dependency patch (same major version)
- 🟢 Adding translations
- 🟢 Documentation updates
- 🟢 Bug fixes with tests
- 🟢 Code formatting/linting

---

## 💡 Pro Tips for AI Agents

1. **Always test with ML disabled first**
   ```powershell
   $env:AGRISENSE_DISABLE_ML='1'
   ```

2. **Check TypeScript before runtime**
   ```powershell
   npm run typecheck
   ```

3. **Use hard refresh after frontend changes**
   ```
   Ctrl + Shift + R (or Ctrl + F5)
   ```

4. **Run from project root, not subdirectories**
   ```powershell
   cd "AGRISENSE FULL-STACK/AGRISENSEFULL-STACK"
   ```

5. **Check browser console first for frontend issues**
   ```
   F12 → Console tab → Look for red errors
   ```

---

## 📞 Where to Find More Info

| Topic | Document | Location |
|-------|----------|----------|
| **Full setup guide** | copilot-instructions.md | `.github/` |
| **Architecture** | PROJECT_BLUEPRINT_UPDATED.md | `AGRISENSEFULL-STACK/` |
| **Multi-language** | MULTILANGUAGE_IMPLEMENTATION_SUMMARY.md | `AGRISENSEFULL-STACK/` |
| **Deployment** | DEPLOYMENT_GUIDE.md | `AGRISENSEFULL-STACK/` |
| **Testing** | TESTING_README.md | `AGRISENSEFULL-STACK/` |
| **VLM features** | VLM_INTEGRATION_SUMMARY.md | `AGRISENSEFULL-STACK/` |

---

## 🎓 5-Minute Learning Path

```
1. Read "Quick Orientation" (1 min)
   → Understand what AgriSense is
   
2. Run "Start the Project" (5 mins)
   → Get both servers running
   
3. Check "Health Check Matrix" (1 min)
   → Verify everything works
   
4. Scan "Common Fix Patterns" (2 mins)
   → Know where to look when issues arise
   
5. Review "When to Escalate" (1 min)
   → Understand autonomy boundaries
```

**Total**: 10 minutes to operational competence ✅

---

## 🔄 Quick Decision Tree

```
TASK RECEIVED
    │
    ├─ Is it documented? ────→ YES → Follow instructions
    │                               ↓
    │                               SUCCESS? → YES → Done ✅
    │                                         ↓ NO
    ├─ Is it simple? ───────→ YES → Try safe fix
    │                               ↓
    │                               SUCCESS? → YES → Done ✅
    │                                         ↓ NO
    ├─ Is it critical? ─────→ YES → Escalate immediately 🚨
    │                               
    └─ Need more info? ─────→ YES → Check full guide
                                    (.github/copilot-instructions.md)
```

---

## ✅ Pre-Task Checklist

Before starting any work:
- [ ] Virtual environment activated
- [ ] Dependencies up to date
- [ ] No existing errors (run tests)
- [ ] Git status clean (optional)
- [ ] Documentation reviewed

After completing any work:
- [ ] Tests pass (0 failures)
- [ ] TypeScript clean (0 errors)
- [ ] No new security issues
- [ ] Documentation updated
- [ ] Changes committed

---

**Document Type**: Quick Reference  
**Target Time**: <5 minutes to find any answer  
**Companion Doc**: `.github/copilot-instructions.md` (full guide)  

💡 **Tip**: Bookmark this file for instant access to common tasks!
