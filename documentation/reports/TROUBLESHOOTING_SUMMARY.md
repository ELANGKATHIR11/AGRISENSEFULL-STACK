# Troubleshooting Summary - October 5, 2025

## Issues Resolved

### ✅ 1. Chatbot Bug: Carrot Query Returns Soybean Info
**Status**: PARTIALLY FIXED  
**Root Cause**: Training dataset lacked comprehensive cultivation guides  
**Solution Implemented**:
- Created `comprehensive_crop_guides.csv` with 8 detailed crop guides
- Merged with existing dataset (4095 → 4103 QA pairs)
- Rebuilt chatbot artifacts using TF-IDF + SVD (256 components)
- Enabled crop facts fallback (`CHATBOT_ENABLE_CROP_FACTS=1`)

**Current State**:
- ✅ Carrot queries now return carrot information (not soybean)
- ⚠️ Using crop facts fallback instead of comprehensive guide
- ⚠️ Comprehensive guide score < 0.40 threshold (line 4458 in main.py)

**Artifacts Location**:
- `comprehensive_crop_guides.csv` - 8 detailed crop cultivation guides
- `merged_with_guides.csv` - Combined dataset (4103 rows)
- `agrisense_app/backend/chatbot_qa_pairs.json` - Rebuilt QA pairs
- `agrisense_app/backend/chatbot_q_index.npz` - Question embeddings
- `agrisense_app/backend/chatbot_index.npz` - Answer embeddings

**Known Limitation**:
```python
# Line 4458 in main.py
if top_cos < max(0.40, _chatbot_min_cos):
    need_facts = True
```
The threshold of **0.40** is too high for TF-IDF-based scoring. The comprehensive guide exists in the dataset but scores below this threshold.

**Next Steps**:
1. Lower the crop facts threshold from 0.40 to ~0.25
2. OR improve scoring by training a proper sentence encoder
3. OR manually verify retrieval scores with `debug_retrieval_scores.py`

---

### ✅ 2. Blank White Page Issue
**Status**: RESOLVED  
**Root Cause**: Frontend dev server was not running  
**Solution**: Started both services

**Services Now Running**:
- ✅ Backend: http://localhost:8004 (Uvicorn - FastAPI)
- ✅ Frontend: http://localhost:8080 (Vite dev server)

**Important**: 
- Access the app at **http://localhost:8080** (Vite dev server)
- DO NOT use backend's `/ui` endpoint - it serves built files only
- The 404 errors for `/ui/assets/*.js` are expected in dev mode

---

### ℹ️ 3. CSS Compatibility Warnings
**Status**: INFORMATIONAL (non-critical)  
**Description**: Browser compatibility warnings from developer tools

**Warnings**:
1. `-webkit-filter` → Add `filter` for Chrome Android 53+
2. `-webkit-text-size-adjust` → Add `text-size-adjust` for modern browsers
3. `backdrop-filter` → Add `-webkit-backdrop-filter` for Safari 9+
4. `-webkit-image-set` → Image set syntax warnings
5. `user-select` → Add `-webkit-user-select` for Safari 3+
6. `viewport` meta warnings (maximum-scale, user-scalable)
7. `forced-color-adjust` → Safari not supported
8. `meta[name=theme-color]` → Firefox not supported

**Impact**: Low - These are minor cross-browser compatibility warnings
**Action**: These can be addressed later during CSS optimization phase

**Recommended Fixes** (if needed):
```css
/* Add vendor prefixes */
.element {
  -webkit-backdrop-filter: blur(10px);
  backdrop-filter: blur(10px);
  
  -webkit-user-select: none;
  user-select: none;
  
  -webkit-filter: brightness(1.1);
  filter: brightness(1.1);
  
  -webkit-text-size-adjust: 100%;
  text-size-adjust: 100%;
}
```

---

## Current System Status

### Backend Health
```
✅ Server running on port 8004
✅ Chatbot loaded: 13 answers, 4095 QA pairs
✅ Crop facts fallback enabled
⚠️ Redis unavailable (using fallback cache)
⚠️ Database table creation errors (non-critical)
⚠️ ML model errors (expected with AGRISENSE_DISABLE_ML=1)
```

### Frontend Health
```
✅ Vite dev server running on port 8080
✅ Hot module replacement enabled
✅ Multi-language support (5 languages)
```

### Testing Commands
```powershell
# Test backend health
curl http://localhost:8004/health

# Test chatbot (with comprehensive guide check)
cd "d:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK"
.\.venv\Scripts\python.exe check_carrot_in_artifacts.py

# Test frontend
Start-Process "http://localhost:8080"
```

---

## Open Items for Investigation

### Priority 1: Retrieval Scoring Issue
- Comprehensive guide exists but not retrieved
- Scores below 0.40 threshold trigger crop facts fallback
- Need to investigate why TF-IDF scoring is low

### Priority 2: Backend Stability
- Connection reset errors during rapid queries
- May need rate limiting or connection pooling

### Priority 3: CSS Optimization
- Address vendor prefix warnings
- Test cross-browser compatibility
- Optimize viewport meta tags

---

## Files Created/Modified This Session

**New Files**:
- `comprehensive_crop_guides.csv` - Detailed crop cultivation guides
- `merged_with_guides.csv` - Combined training dataset
- `check_carrot_in_artifacts.py` - Verification script
- `test_carrot_queries.py` - Multi-query test script
- `test_retrieval_scores.py` - Score debugging script
- `debug_retrieval_scores.py` - Retrieval analysis script
- `TROUBLESHOOTING_SUMMARY.md` - This document

**Modified Files**:
- `agrisense_app/backend/chatbot_qa_pairs.json` - Rebuilt with new guides
- `agrisense_app/backend/chatbot_q_index.npz` - Rebuilt embeddings
- `agrisense_app/backend/chatbot_index.npz` - Rebuilt embeddings

---

## Quick Reference

### Start Both Services
```powershell
# Terminal 1: Backend
cd "d:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK"
$env:AGRISENSE_DISABLE_ML='1'
$env:CHATBOT_ENABLE_CROP_FACTS='1'
.\.venv\Scripts\python.exe -m uvicorn agrisense_app.backend.main:app --port 8004 --reload

# Terminal 2: Frontend
cd "d:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK\agrisense_app\frontend\farm-fortune-frontend-main"
npm run dev
```

### Access URLs
- Frontend (Dev): http://localhost:8080
- Backend API: http://localhost:8004
- API Docs: http://localhost:8004/docs
- Health Check: http://localhost:8004/health
- Chatbot Test: http://localhost:8004/chatbot/ask

---

**Last Updated**: October 5, 2025  
**Session Status**: ✅ Both services running, basic fix verified, comprehensive guide retrieval pending investigation
