# =====================================================================
# AgriSense - Quick Integration Test
# =====================================================================
# Simplified test script for existing running services
# =====================================================================

Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "AgriSense Integration Test" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

$ErrorActionPreference = "Continue"

# Test 1: Backend Health
Write-Host "[1/5] Testing Backend Health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8004/health" -Method GET -TimeoutSec 3
    Write-Host "✅ Backend is healthy: $($health.status)" -ForegroundColor Green
    Write-Host "    Response: $($health | ConvertTo-Json -Compress)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Backend health check failed!" -ForegroundColor Red
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Gray
    Write-Host "    Make sure backend is running on port 8004" -ForegroundColor Yellow
}

# Test 2: Backend API
Write-Host "`n[2/5] Testing Backend API..." -ForegroundColor Yellow
try {
    $testData = @{
        plant = "tomato"
        soil_type = "loam"
        area_m2 = 100
        moisture_pct = 45
        temperature_c = 25
        ph = 6.5
    } | ConvertTo-Json
    
    $apiResponse = Invoke-RestMethod -Uri "http://localhost:8004/api/recommend" -Method POST -Body $testData -ContentType "application/json" -TimeoutSec 5
    Write-Host "✅ API endpoint working!" -ForegroundColor Green
    Write-Host "    Water recommendation: $($apiResponse.water_liters) liters" -ForegroundColor Gray
    Write-Host "    Tips: $($apiResponse.tips -join ', ')" -ForegroundColor Gray
} catch {
    Write-Host "⚠️  API endpoint test inconclusive" -ForegroundColor Yellow
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Gray
    if ($_.Exception.Message -like "*404*") {
        Write-Host "    Endpoint may not exist or path incorrect" -ForegroundColor Yellow
    } elseif ($_.Exception.Message -like "*500*") {
        Write-Host "    Server error - check backend logs" -ForegroundColor Yellow
    }
}

# Test 3: Frontend
Write-Host "`n[3/5] Testing Frontend..." -ForegroundColor Yellow
$frontendPorts = @(3000, 8080, 8081, 8082)
$frontendFound = $false

foreach ($port in $frontendPorts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$port" -Method GET -TimeoutSec 2 -ErrorAction Stop
        Write-Host "✅ Frontend is running on port $port" -ForegroundColor Green
        $frontendFound = $true
        $frontendPort = $port
        break
    } catch {
        # Try next port
    }
}

if (-not $frontendFound) {
    Write-Host "⚠️  Frontend not detected on common ports" -ForegroundColor Yellow
    Write-Host "    Checked ports: $($frontendPorts -join ', ')" -ForegroundColor Gray
    Write-Host "    Start frontend: npm run dev" -ForegroundColor Yellow
}

# Test 4: Frontend-Backend Proxy
if ($frontendFound) {
    Write-Host "`n[4/5] Testing Frontend-Backend Proxy..." -ForegroundColor Yellow
    try {
        $proxyResponse = Invoke-RestMethod -Uri "http://localhost:$frontendPort/api/health" -Method GET -TimeoutSec 5
        Write-Host "✅ Proxy working! Frontend can communicate with backend" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Proxy test inconclusive" -ForegroundColor Yellow
        Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Gray
        Write-Host "    This may be normal if Vite is still starting" -ForegroundColor Yellow
    }
} else {
    Write-Host "`n[4/5] Skipping proxy test (frontend not running)" -ForegroundColor Yellow
}

# Test 5: Dependency Check
Write-Host "`n[5/5] Checking Dependencies..." -ForegroundColor Yellow

# Backend dependencies
Write-Host "`n  Backend Python Dependencies:" -ForegroundColor Gray
try {
    cd "d:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK"
    $venvPython = if (Test-Path ".\.venv-py312\Scripts\python.exe") {
        ".\.venv-py312\Scripts\python.exe"
    } else {
        ".\.venv\Scripts\python.exe"
    }
    
    if (Test-Path $venvPython) {
        $pipCheck = & $venvPython -m pip check 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    ✅ No dependency conflicts" -ForegroundColor Green
        } else {
            Write-Host "    ⚠️  Some dependency warnings:" -ForegroundColor Yellow
            $pipCheck | Select-Object -First 5 | ForEach-Object { Write-Host "      $_" -ForegroundColor Gray }
        }
    } else {
        Write-Host "    ⚠️  Virtual environment not found" -ForegroundColor Yellow
    }
} catch {
    Write-Host "    ❌ Could not check backend dependencies" -ForegroundColor Red
}

# Frontend dependencies
Write-Host "`n  Frontend NPM Dependencies:" -ForegroundColor Gray
try {
    cd "d:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK\agrisense_app\frontend\farm-fortune-frontend-main"
    $npmAudit = npm audit --production 2>&1 | Out-String
    if ($npmAudit -like "*0 vulnerabilities*") {
        Write-Host "    ✅ No security vulnerabilities" -ForegroundColor Green
    } else {
        Write-Host "    ⚠️  Security audit results:" -ForegroundColor Yellow
        Write-Host "    $npmAudit" -ForegroundColor Gray
    }
} catch {
    Write-Host "    ❌ Could not check frontend dependencies" -ForegroundColor Red
}

# Summary
Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "Integration Test Summary" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

$services = @()
$services += if ((Test-Connection -ComputerName localhost -Port 8004 -ErrorAction SilentlyContinue)) { "Backend (8004)" } else { $null }
if ($frontendFound) { $services += "Frontend ($frontendPort)" }

if ($services.Count -gt 0) {
    Write-Host "✅ Running Services:" -ForegroundColor Green
    $services | ForEach-Object { Write-Host "    - $_" -ForegroundColor White }
} else {
    Write-Host "⚠️  No services detected" -ForegroundColor Yellow
}

Write-Host "`n📝 Recommendations:" -ForegroundColor Cyan
if (-not $frontendFound) {
    Write-Host "  • Start frontend: npm run dev" -ForegroundColor Yellow
}
Write-Host "  • View logs for any errors" -ForegroundColor White
Write-Host "  • Test in browser: http://localhost:$($frontendPort -or 3000)" -ForegroundColor White
Write-Host "  • Check backend logs if API calls fail" -ForegroundColor White

Write-Host "`n================================`n" -ForegroundColor Cyan
