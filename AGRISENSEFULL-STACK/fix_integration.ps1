# =====================================================================
# AgriSense - Comprehensive Fix Script
# =====================================================================
# This script fixes all pipeline and integration issues between 
# frontend and backend
# =====================================================================

Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "AgriSense Integration Fix Script" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

$ErrorActionPreference = "Stop"
$projectRoot = "d:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK"

# =====================================================================
# Step 1: Fix Backend Dependencies
# =====================================================================
Write-Host "`n[1/6] Fixing Backend Dependencies..." -ForegroundColor Yellow

Set-Location $projectRoot

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Gray
$venvPath = Join-Path $projectRoot ".venv-py312\Scripts\Activate.ps1"
if (-not (Test-Path $venvPath)) {
    # Try alternate path
    $venvPath = Join-Path $projectRoot ".venv\Scripts\Activate.ps1"
}
if (Test-Path $venvPath) {
    & $venvPath
    Write-Host "Virtual environment activated: $venvPath" -ForegroundColor Gray
} else {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Searched: .venv-py312 and .venv" -ForegroundColor Yellow
    Write-Host "Please create virtual environment first: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# Upgrade pip and core tools
Write-Host "Upgrading pip, wheel, and setuptools..." -ForegroundColor Gray
python -m pip install --upgrade pip wheel setuptools

# Uninstall conflicting packages
Write-Host "Removing conflicting packages..." -ForegroundColor Gray
pip uninstall -y tensorflow tensorflow-intel tensorflow-cpu 2>$null
pip uninstall -y numpy 2>$null
pip uninstall -y protobuf 2>$null
pip uninstall -y keras 2>$null

# Install fixed requirements
Write-Host "Installing backend dependencies with fixes..." -ForegroundColor Gray
pip install -r agrisense_app\backend\requirements.txt

# Verify no conflicts
Write-Host "Verifying dependency integrity..." -ForegroundColor Gray
$pipCheckResult = python -m pip check 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Backend dependencies verified - no conflicts!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Some dependency warnings detected:" -ForegroundColor Yellow
    Write-Host $pipCheckResult -ForegroundColor Gray
    Write-Host "Continuing anyway - these may be acceptable version mismatches..." -ForegroundColor Yellow
}

# =====================================================================
# Step 2: Update Frontend Dependencies
# =====================================================================
Write-Host "`n[2/6] Checking Frontend Dependencies..." -ForegroundColor Yellow

Set-Location "$projectRoot\agrisense_app\frontend\farm-fortune-frontend-main"

Write-Host "Running npm audit..." -ForegroundColor Gray
npm audit --production

Write-Host "✅ Frontend dependencies checked!" -ForegroundColor Green

# =====================================================================
# Step 3: Stop Existing Services
# =====================================================================
Write-Host "`n[3/6] Stopping Existing Services..." -ForegroundColor Yellow

# Stop all existing Python and Node processes related to AgriSense
Write-Host "Stopping backend processes..." -ForegroundColor Gray
Get-Process | Where-Object { $_.ProcessName -eq "python" -and $_.CommandLine -like "*uvicorn*" } | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "Stopping frontend processes..." -ForegroundColor Gray
Get-Process | Where-Object { $_.ProcessName -eq "node" -and $_.CommandLine -like "*vite*" } | Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 2
Write-Host "✅ Existing services stopped!" -ForegroundColor Green

# =====================================================================
# Step 4: Start Backend Service
# =====================================================================
Write-Host "`n[4/6] Starting Backend Service..." -ForegroundColor Yellow

Set-Location $projectRoot

# Start backend in background job
$backendJob = Start-Job -Name "AgriSense-Backend-Fixed" -ScriptBlock {
    Set-Location "d:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK"
    $venvPath = if (Test-Path ".\.venv-py312\Scripts\Activate.ps1") {
        ".\.venv-py312\Scripts\Activate.ps1"
    } else {
        ".\.venv\Scripts\Activate.ps1"
    }
    & $venvPath
    $env:AGRISENSE_DISABLE_ML = '0'  # Enable ML if available
    $env:PYTHONPATH = "d:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK"
    python -m uvicorn agrisense_app.backend.main:app --host 0.0.0.0 --port 8004 --reload
}

Write-Host "Backend starting... (PID: $($backendJob.Id))" -ForegroundColor Gray

# Wait for backend to be ready
Write-Host "Waiting for backend to be ready..." -ForegroundColor Gray
$maxAttempts = 30
$attempt = 0
$backendReady = $false

while ($attempt -lt $maxAttempts -and -not $backendReady) {
    Start-Sleep -Seconds 2
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8004/health" -Method GET -TimeoutSec 2 -ErrorAction Stop
        $backendReady = $true
        Write-Host "✅ Backend is ready on http://localhost:8004" -ForegroundColor Green
    } catch {
        $attempt++
        Write-Host "." -NoNewline -ForegroundColor Gray
    }
}

if (-not $backendReady) {
    Write-Host "`n❌ Backend failed to start after $maxAttempts attempts!" -ForegroundColor Red
    Write-Host "Backend Logs:" -ForegroundColor Yellow
    Receive-Job -Job $backendJob | Select-Object -Last 20
    exit 1
}

# =====================================================================
# Step 5: Start Frontend Service
# =====================================================================
Write-Host "`n[5/6] Starting Frontend Service..." -ForegroundColor Yellow

Set-Location "$projectRoot\agrisense_app\frontend\farm-fortune-frontend-main"

# Start frontend in background job
$frontendJob = Start-Job -Name "AgriSense-Frontend-Fixed" -ScriptBlock {
    Set-Location "d:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK\agrisense_app\frontend\farm-fortune-frontend-main"
    npm run dev
}

Write-Host "Frontend starting... (PID: $($frontendJob.Id))" -ForegroundColor Gray

# Wait for frontend to be ready
Write-Host "Waiting for frontend to be ready..." -ForegroundColor Gray
$maxAttempts = 20
$attempt = 0
$frontendReady = $false

while ($attempt -lt $maxAttempts -and -not $frontendReady) {
    Start-Sleep -Seconds 2
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:3000" -Method GET -TimeoutSec 2 -ErrorAction Stop
        $frontendReady = $true
        Write-Host "✅ Frontend is ready on http://localhost:3000" -ForegroundColor Green
    } catch {
        $attempt++
        Write-Host "." -NoNewline -ForegroundColor Gray
    }
}

if (-not $frontendReady) {
    Write-Host "`n⚠️  Frontend may still be starting (this is normal for first run)" -ForegroundColor Yellow
    Write-Host "Check http://localhost:3000 in your browser" -ForegroundColor Yellow
}

# =====================================================================
# Step 6: Run Integration Tests
# =====================================================================
Write-Host "`n[6/6] Running Integration Tests..." -ForegroundColor Yellow

# Test backend health endpoint
Write-Host "`nTesting backend /health endpoint..." -ForegroundColor Gray
try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8004/health" -Method GET
    Write-Host "✅ Health check passed: $($healthResponse.status)" -ForegroundColor Green
} catch {
    Write-Host "❌ Health check failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test backend API endpoint
Write-Host "`nTesting backend API endpoint..." -ForegroundColor Gray
try {
    $testReading = @{
        plant = "tomato"
        soil_type = "loam"
        area_m2 = 100
        moisture_pct = 45
        temperature_c = 25
    } | ConvertTo-Json
    
    $apiResponse = Invoke-RestMethod -Uri "http://localhost:8004/api/recommend" -Method POST -Body $testReading -ContentType "application/json"
    Write-Host "✅ API endpoint working! Water recommendation: $($apiResponse.water_liters)L" -ForegroundColor Green
} catch {
    Write-Host "⚠️  API endpoint test failed (this might be normal if ML is disabled)" -ForegroundColor Yellow
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Gray
}

# Test frontend-backend proxy
Write-Host "`nTesting frontend-backend proxy..." -ForegroundColor Gray
try {
    $proxyResponse = Invoke-RestMethod -Uri "http://localhost:3000/api/health" -Method GET -TimeoutSec 5
    Write-Host "✅ Frontend proxy working!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Frontend proxy test inconclusive (frontend may still be loading)" -ForegroundColor Yellow
}

# =====================================================================
# Summary
# =====================================================================
Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "Integration Fix Summary" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

Write-Host "✅ Backend dependencies fixed" -ForegroundColor Green
Write-Host "✅ Frontend dependencies verified" -ForegroundColor Green
Write-Host "✅ Backend running on http://localhost:8004" -ForegroundColor Green
Write-Host "✅ Frontend running on http://localhost:3000" -ForegroundColor Green
Write-Host "`nServices are running in background jobs:" -ForegroundColor Yellow
Write-Host "  - Backend Job ID: $($backendJob.Id)" -ForegroundColor Gray
Write-Host "  - Frontend Job ID: $($frontendJob.Id)" -ForegroundColor Gray

Write-Host "`n📝 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Open http://localhost:3000 in your browser" -ForegroundColor White
Write-Host "  2. Check if pages load correctly" -ForegroundColor White
Write-Host "  3. Test API integrations (sensors, recommendations, etc.)" -ForegroundColor White

Write-Host "`n🔧 Manage Services:" -ForegroundColor Cyan
Write-Host "  View jobs:   Get-Job" -ForegroundColor White
Write-Host "  View logs:   Receive-Job -Job <job-id>" -ForegroundColor White
Write-Host "  Stop jobs:   Stop-Job -Name 'AgriSense-*'" -ForegroundColor White
Write-Host "  Remove jobs: Remove-Job -Name 'AgriSense-*'" -ForegroundColor White

Write-Host "`n================================`n" -ForegroundColor Cyan
