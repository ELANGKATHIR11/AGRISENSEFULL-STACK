# 🚀 SCOLD VLM Quick Start Guide

## Prerequisites Checklist

Before starting, ensure you have:

- ✅ Python 3.9+ installed
- ✅ SCOLD model cloned to `AI_Models/scold`
- ✅ Virtual environment created at `AI_Models/scold/venv`
- ✅ Dependencies installed (torch, transformers, fastapi, etc.)
- ✅ Backend virtual environment at `.venv` with all requirements

## Quick Start (3 Steps)

### Option A: Using PowerShell Script (Recommended)

```powershell
# Start all services with one command
.\start_agrisense_scold.ps1

# Or start only SCOLD + Backend (no frontend)
.\start_agrisense_scold.ps1 -SkipFrontend
```

This will:
1. ✅ Start SCOLD VLM server on port 8001
2. ✅ Start AgriSense backend on port 8004  
3. ✅ Start frontend on port 8082 (if not skipped)
4. ✅ Monitor all services with health checks
5. ✅ Handle graceful shutdown on Ctrl+C

### Option B: Manual Startup

**Terminal 1 - SCOLD VLM Server:**
```powershell
cd "d:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK\AI_Models\scold"
.\venv\Scripts\Activate.ps1
python ..\..\start_scold_server.py --port 8001
```

**Terminal 2 - AgriSense Backend:**
```powershell
cd "d:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK"
.\.venv\Scripts\Activate.ps1
python -m uvicorn agrisense_app.backend.main:app --host 0.0.0.0 --port 8004 --reload
```

**Terminal 3 - Frontend (Optional):**
```powershell
cd "d:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK\agrisense_app\frontend\farm-fortune-frontend-main"
npm run dev
```

## Verify Installation

### 1. Check SCOLD Server
```powershell
# Health check
curl http://localhost:8001/health

# Expected response:
# {"status": "healthy", "model_loaded": true}

# Detailed status
curl http://localhost:8001/status
```

### 2. Check Backend
```powershell
# Health check
curl http://localhost:8004/health

# VLM status
curl http://localhost:8004/api/vlm/status

# Hybrid AI status
curl http://localhost:8004/api/hybrid/status
```

### 3. Run Integration Tests
```powershell
# Activate backend environment
.\.venv\Scripts\Activate.ps1

# Run comprehensive test suite
python test_scold_integration.py
```

**Expected Output:**
```
🧪 SCOLD VLM Integration Test Suite
======================================================================
✅ PASS - SCOLD Health
✅ PASS - SCOLD Status
✅ PASS - Backend Health
✅ PASS - Disease Detection
✅ PASS - Weed Identification
✅ PASS - Hybrid AI Status

Total: 6 | Passed: 6 | Failed: 0
🎉 All tests passed!
```

## Test Endpoints

### Disease Detection
```powershell
# Create test request
$imageBase64 = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes("test_leaf.jpg"))
$body = @{
    image_base64 = $imageBase64
    crop_type = "tomato"
} | ConvertTo-Json

# Send request
$response = Invoke-RestMethod -Uri "http://localhost:8004/api/disease/detect" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"

# View results
$response | ConvertTo-Json -Depth 10
```

### Weed Identification
```powershell
# Create test request
$imageBase64 = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes("test_field.jpg"))
$body = @{
    image_base64 = $imageBase64
    crop_type = "wheat"
} | ConvertTo-Json

# Send request
$response = Invoke-RestMethod -Uri "http://localhost:8004/api/weed/analyze" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"

# View results
$response | ConvertTo-Json -Depth 10
```

### Hybrid AI Multimodal Analysis
```powershell
# Text + Image analysis
$imageBase64 = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes("farm_image.jpg"))
$body = @{
    image_base64 = $imageBase64
    query = "What crop disease is this and how do I treat it?"
    context = @{
        crop = "rice"
        location = "field"
    }
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8004/api/hybrid/analyze" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"

$response | ConvertTo-Json -Depth 10
```

## Common Issues & Solutions

### Issue 1: SCOLD Server Won't Start

**Symptom:** `ModuleNotFoundError: No module named 'transformers'`

**Solution:**
```powershell
cd AI_Models\scold
.\venv\Scripts\Activate.ps1
pip install torch transformers torchvision pillow fastapi uvicorn
```

### Issue 2: Port Already in Use

**Symptom:** `Address already in use: 8001`

**Solution:**
```powershell
# Find process using port 8001
Get-NetTCPConnection -LocalPort 8001 | Select-Object OwningProcess
$pid = (Get-NetTCPConnection -LocalPort 8001).OwningProcess

# Kill the process
Stop-Process -Id $pid -Force

# Or use different port
python start_scold_server.py --port 8002
```

### Issue 3: Model Not Found

**Symptom:** `Model path does not exist: AI_Models/scold`

**Solution:**
```powershell
# Verify model directory exists
Test-Path "AI_Models\scold"

# If missing, clone SCOLD model
cd AI_Models
git clone https://huggingface.co/enalis/scold
```

### Issue 4: Backend Can't Connect to SCOLD

**Symptom:** `SCOLD VLM unavailable: Connection refused`

**Solution:**
1. Verify SCOLD is running: `curl http://localhost:8001/health`
2. Check firewall isn't blocking port 8001
3. Restart SCOLD server
4. Check SCOLD logs for errors

### Issue 5: Slow Inference

**Symptom:** Disease detection takes >10 seconds

**Solutions:**
- Use GPU if available (requires CUDA-enabled torch)
- Reduce image size before sending
- Enable model caching in SCOLD server
- Check system RAM (needs 2GB+ free)

## Performance Tips

### 1. Enable GPU Acceleration (if available)
```powershell
# Install CUDA-enabled PyTorch
cd AI_Models\scold
.\venv\Scripts\Activate.ps1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### 2. Optimize Image Sizes
- Resize images to 640x640 before sending
- Use JPEG instead of PNG for smaller payloads
- Compress images to ~100KB for faster upload

### 3. Enable Response Caching
Backend automatically caches recent analyses for 5 minutes.

### 4. Monitor Resource Usage
```powershell
# Check memory usage
Get-Process python | Select-Object Name, WorkingSet64

# Check CPU usage
Get-Process python | Select-Object Name, CPU
```

## Environment Variables

Create `.env` file in project root:

```env
# SCOLD Configuration
SCOLD_MODEL_PATH=AI_Models/scold
SCOLD_PORT=8001
SCOLD_HOST=localhost
SCOLD_TIMEOUT=30

# Backend Configuration
BACKEND_PORT=8004
AGRISENSE_DISABLE_ML=0

# Hybrid AI Configuration
HYBRID_AI_TIMEOUT=45
HYBRID_AI_MAX_HISTORY=5
PHI_ENDPOINT=http://localhost:11434
SCOLD_ENDPOINT=http://localhost:8001
```

## Monitoring & Logs

### View SCOLD Logs
```powershell
# If using PowerShell script
Get-Job | Where-Object {$_.Name -like "*SCOLD*"} | Receive-Job
```

### View Backend Logs
```powershell
# If using PowerShell script
Get-Job | Where-Object {$_.Name -like "*Backend*"} | Receive-Job
```

### Monitor Health Status
```powershell
# Continuous health monitoring
while ($true) {
    Write-Host "`n=== Health Check $(Get-Date -Format 'HH:mm:ss') ==="
    
    try {
        $scold = Invoke-RestMethod "http://localhost:8001/health" -TimeoutSec 2
        Write-Host "✅ SCOLD: $($scold.status)"
    } catch {
        Write-Host "❌ SCOLD: offline"
    }
    
    try {
        $backend = Invoke-RestMethod "http://localhost:8004/health" -TimeoutSec 2
        Write-Host "✅ Backend: $($backend.status)"
    } catch {
        Write-Host "❌ Backend: offline"
    }
    
    Start-Sleep -Seconds 10
}
```

## Shutdown

### Using PowerShell Script
```powershell
# Press Ctrl+C in the terminal running start_agrisense_scold.ps1
# Script will automatically clean up all jobs
```

### Manual Shutdown
```powershell
# Stop all PowerShell background jobs
Get-Job | Stop-Job
Get-Job | Remove-Job

# Or kill processes directly
Get-Process python | Where-Object {$_.MainWindowTitle -like "*uvicorn*"} | Stop-Process
Get-Process node | Stop-Process  # If frontend running
```

## Next Steps

1. ✅ **Test the integration** - Run `python test_scold_integration.py`
2. 📱 **Create frontend components** - See `SCOLD_INTEGRATION_SUMMARY.md`
3. 🌍 **Add translations** - Update locale files for multilingual UI
4. 🎯 **Fine-tune SCOLD** - Train on your specific crops/diseases
5. 🚀 **Deploy to production** - See deployment guide

## Need Help?

- 📖 **Full Documentation**: See `SCOLD_INTEGRATION_SUMMARY.md`
- 🐛 **Troubleshooting**: Check logs in PowerShell jobs
- 📝 **API Reference**: Visit `http://localhost:8004/docs` when backend is running
- 🧪 **Test Suite**: Run `python test_scold_integration.py` for diagnostics

## Quick Reference Commands

```powershell
# Start everything
.\start_agrisense_scold.ps1

# Test integration
python test_scold_integration.py

# Check health
curl http://localhost:8001/health  # SCOLD
curl http://localhost:8004/health  # Backend

# View API docs
Start-Process "http://localhost:8004/docs"

# Stop everything
Get-Job | Stop-Job; Get-Job | Remove-Job
```

---

**Status**: ✅ Ready for Testing  
**Last Updated**: December 2025  
**Integration Version**: 1.0.0
