# 🚀 VLM Quick Start Guide

**AgriSense Vision Language Model - Get Started in 5 Minutes**

---

## ⚡ Quick Commands

### Start Backend
```powershell
cd "d:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK\agrisense_app\backend"
.\.venv\Scripts\python.exe -m uvicorn main:app --port 8004 --reload
```

### Check Health
```powershell
Invoke-RestMethod -Uri "http://localhost:8004/api/vlm/health" | ConvertTo-Json
```

### List Crops
```powershell
Invoke-RestMethod -Uri "http://localhost:8004/api/vlm/crops" | ConvertTo-Json
```

---

## 📋 All Available Endpoints

```
1. GET  /api/vlm/health                         # Health check
2. GET  /api/vlm/status                         # Detailed status
3. GET  /api/vlm/crops                          # List all crops
4. GET  /api/vlm/crops?category=cereal          # Filter by category
5. GET  /api/vlm/crops/{crop_name}              # Crop details
6. GET  /api/vlm/crops/{crop_name}/diseases     # Disease library
7. GET  /api/vlm/crops/{crop_name}/weeds        # Weed library
8. POST /api/vlm/analyze/disease                # Analyze disease
9. POST /api/vlm/analyze/weed                   # Analyze weeds
10. POST /api/vlm/analyze/comprehensive         # Both disease + weed
11. GET /docs                                   # API documentation
```

---

## 🌾 Analyze Disease (PowerShell)

```powershell
$form = @{
    image = Get-Item -Path "C:\path\to\plant_image.jpg"
    crop_name = "rice"
    include_cost = "true"
}

$result = Invoke-RestMethod -Uri "http://localhost:8004/api/vlm/analyze/disease" -Method Post -Form $form

# View results
$result | ConvertTo-Json -Depth 10

# Quick summary
Write-Host "Disease: $($result.disease_name)"
Write-Host "Severity: $($result.severity)"
Write-Host "Confidence: $($result.confidence * 100)%"
Write-Host "Cost: ₹$($result.cost_estimate.total_per_acre)/acre"
```

---

## 🌿 Analyze Weeds (PowerShell)

```powershell
$form = @{
    image = Get-Item -Path "C:\path\to\field_image.jpg"
    crop_name = "wheat"
    growth_stage = "tillering"
    preferred_control = "organic"
    include_cost = "true"
}

$result = Invoke-RestMethod -Uri "http://localhost:8004/api/vlm/analyze/weed" -Method Post -Form $form

# Quick summary
Write-Host "Infestation: $($result.infestation_level)"
Write-Host "Coverage: $($result.weed_coverage_percentage)%"
Write-Host "Cost: ₹$($result.cost_estimate.total_per_acre)/acre"
```

---

## 🔬 Comprehensive Analysis (PowerShell)

```powershell
$form = @{
    plant_image = Get-Item -Path "C:\path\to\plant.jpg"
    field_image = Get-Item -Path "C:\path\to\field.jpg"
    crop_name = "rice"
    growth_stage = "vegetative"
    include_cost = "true"
}

$result = Invoke-RestMethod -Uri "http://localhost:8004/api/vlm/analyze/comprehensive" -Method Post -Form $form

# View priority actions
$result.priority_actions | ForEach-Object { Write-Host $_ }

# View total cost
Write-Host "Total Cost: ₹$($result.cost_estimate.total_per_acre)/acre"
Write-Host "Success Probability: $($result.success_probability * 100)%"
```

---

## 🧪 Run Tests

```powershell
cd "d:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK"

# Run all VLM tests
pytest tests\test_vlm_*.py -v

# Run specific test file
pytest tests\test_vlm_disease_detector.py -v
pytest tests\test_vlm_weed_detector.py -v
pytest tests\test_vlm_api_integration.py -v

# Run with coverage
pytest tests\test_vlm_*.py --cov=agrisense_app.backend.vlm --cov-report=html
```

---

## 📖 Documentation Files

```
1. VLM_SYSTEM_GUIDE.md              # Complete system guide (3,500 lines)
2. VLM_IMPLEMENTATION_SUMMARY.md    # Implementation summary
3. VLM_QUICK_START.md               # This file (quick reference)
4. examples/vlm_python_examples.py  # Python code examples
5. examples/vlm_curl_examples.sh    # Bash/cURL examples
```

---

## 🌾 Supported Crops (13)

**Cereals:** Rice, Wheat, Maize, Sorghum, Pearl Millet  
**Pulses:** Chickpea, Pigeon Pea, Green Gram, Black Gram, Lentil  
**Oilseeds:** Groundnut, Soybean, Mustard, Sunflower

---

## 💡 Common Use Cases

### 1. Get Crop Information
```powershell
Invoke-RestMethod -Uri "http://localhost:8004/api/vlm/crops/rice" | ConvertTo-Json
```

### 2. List All Diseases for Rice
```powershell
$diseases = Invoke-RestMethod -Uri "http://localhost:8004/api/vlm/crops/rice/diseases"
$diseases.diseases | ForEach-Object { Write-Host $_.name }
```

### 3. List All Weeds for Wheat
```powershell
$weeds = Invoke-RestMethod -Uri "http://localhost:8004/api/vlm/crops/wheat/weeds"
$weeds.weeds | ForEach-Object { Write-Host $_.name }
```

### 4. Check System Status
```powershell
Invoke-RestMethod -Uri "http://localhost:8004/api/vlm/status" | ConvertTo-Json
```

---

## 🐛 Troubleshooting

### Backend won't start
```powershell
# Check if port 8004 is in use
netstat -ano | findstr :8004

# Kill process if needed
Stop-Process -Id <PID> -Force

# Restart backend
cd agrisense_app\backend
python -m uvicorn main:app --port 8004
```

### VLM endpoints not found (404)
```powershell
# Check if VLM router is included
curl http://localhost:8004/api/vlm/health

# Check main.py has VLM router
Select-String -Path "agrisense_app\backend\main.py" -Pattern "vlm_router"
```

### Tests failing
```powershell
# Ensure backend path is correct in tests
# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Install test dependencies
pip install pytest pytest-cov Pillow
```

---

## 📊 Response Time Benchmarks

| Endpoint | Expected Time |
|----------|--------------|
| Health Check | < 100ms |
| List Crops | < 200ms |
| Get Crop Info | < 200ms |
| Analyze Disease | < 3s |
| Analyze Weeds | < 2s |
| Comprehensive | < 5s |

---

## 🔐 Security Notes

⚠️ **Development Mode** - No authentication required  
⚠️ **Production** - Add API keys and rate limiting  
⚠️ **HTTPS** - Use HTTPS in production  
⚠️ **CORS** - Configure allowed origins  

---

## 📞 Quick Links

- **API Docs**: http://localhost:8004/docs
- **Health**: http://localhost:8004/api/vlm/health
- **Crops**: http://localhost:8004/api/vlm/crops
- **ReDoc**: http://localhost:8004/redoc

---

## 🎯 Next Steps

1. ✅ Start backend: `uvicorn main:app --port 8004`
2. ✅ Test health: `curl http://localhost:8004/api/vlm/health`
3. ✅ List crops: `curl http://localhost:8004/api/vlm/crops`
4. ✅ Try analysis with your images
5. ✅ Run tests: `pytest tests/test_vlm_*.py -v`
6. ✅ Read full docs: `VLM_SYSTEM_GUIDE.md`

---

**🌾 Happy Farming! 🌾**
