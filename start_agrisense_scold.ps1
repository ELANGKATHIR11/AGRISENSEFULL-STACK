# Start AgriSense with SCOLD VLM Integration
# ==========================================
# 
# This script starts:
# 1. SCOLD VLM Server (port 8001)
# 2. AgriSense Backend (port 8004)
# 3. AgriSense Frontend (port 8082)

param(
    [switch]$SkipFrontend,
    [switch]$SkipSCOLD,
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "🚀 AgriSense Hybrid AI Startup (with SCOLD VLM)" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

$rootPath = $PSScriptRoot
$scoldPath = Join-Path $rootPath "AI_Models\scold"
$frontendPath = Join-Path $rootPath "agrisense_app\frontend\farm-fortune-frontend-main"

# Function to check if port is in use
function Test-Port {
    param([int]$Port)
    $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue
    return $connection.TcpTestSucceeded
}

# Function to wait for service
function Wait-ForService {
    param(
        [string]$Name,
        [string]$Url,
        [int]$MaxAttempts = 20,
        [int]$DelaySeconds = 3
    )
    
    Write-Host "⏳ Waiting for $Name to be ready..." -ForegroundColor Yellow
    
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ $Name is ready!" -ForegroundColor Green
                return $true
            }
        }
        catch {
            # Service not ready yet
        }
        
        Write-Host "   Attempt $i/$MaxAttempts..." -ForegroundColor Gray
        Start-Sleep -Seconds $DelaySeconds
    }
    
    Write-Host "⚠️  $Name did not become ready in time" -ForegroundColor Yellow
    return $false
}

# Check dependencies
Write-Host "🔍 Checking dependencies..." -ForegroundColor Cyan

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "❌ Python not found!" -ForegroundColor Red
    exit 1
}

# Check Node.js
if (-not $SkipFrontend) {
    try {
        $nodeVersion = node --version
        Write-Host "✅ Node.js: $nodeVersion" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Node.js not found!" -ForegroundColor Red
        exit 1
    }
}

# Check SCOLD model
if (-not $SkipSCOLD) {
    if (Test-Path $scoldPath) {
        Write-Host "✅ SCOLD model directory found" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️  SCOLD model not found at: $scoldPath" -ForegroundColor Yellow
        Write-Host "   Clone with: cd AI_Models && git clone https://huggingface.co/enalis/scold" -ForegroundColor Yellow
        $SkipSCOLD = $true
    }
}

if ($CheckOnly) {
    Write-Host ""
    Write-Host "✅ All dependency checks passed!" -ForegroundColor Green
    exit 0
}

Write-Host ""
Write-Host "🚀 Starting services..." -ForegroundColor Cyan
Write-Host ""

# Kill existing processes on ports
Write-Host "🧹 Cleaning up existing services..." -ForegroundColor Yellow
Get-Process | Where-Object { $_.ProcessName -like "*python*" -or $_.ProcessName -like "*node*" } | ForEach-Object {
    try {
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    catch {
        # Ignore errors
    }
}
Start-Sleep -Seconds 2

# Start SCOLD VLM Server
$scoldJob = $null
if (-not $SkipSCOLD) {
    Write-Host "🔬 Starting SCOLD VLM Server (port 8001)..." -ForegroundColor Cyan
    
    $scoldJob = Start-Job -ScriptBlock {
        param($scriptPath, $scoldPath)
        Set-Location $scriptPath
        python start_scold_server.py --model-path $scoldPath
    } -ArgumentList $rootPath, $scoldPath
    
    $scoldReady = Wait-ForService -Name "SCOLD VLM" -Url "http://localhost:8001/health" -MaxAttempts 15 -DelaySeconds 4
    
    if (-not $scoldReady) {
        Write-Host "⚠️  Continuing without SCOLD VLM" -ForegroundColor Yellow
    }
}
else {
    Write-Host "⏭️  Skipping SCOLD VLM Server" -ForegroundColor Yellow
}

Write-Host ""

# Start Backend
Write-Host "🖥️  Starting AgriSense Backend (port 8004)..." -ForegroundColor Cyan

Start-Job -ScriptBlock {
    param($rootPath)
    Set-Location $rootPath
    $env:SCOLD_BASE_URL = "http://localhost:8001"
    $env:HYBRID_AI_MODE = "offline"
    python -m uvicorn agrisense_app.backend.main:app --host 0.0.0.0 --port 8004
} -ArgumentList $rootPath | Out-Null

$backendReady = Wait-ForService -Name "Backend" -Url "http://localhost:8004/health" -MaxAttempts 15 -DelaySeconds 3

if (-not $backendReady) {
    Write-Host "❌ Backend failed to start!" -ForegroundColor Red
    Get-Job | Stop-Job
    Get-Job | Remove-Job
    exit 1
}

Write-Host ""

# Start Frontend
$frontendJob = $null
if (-not $SkipFrontend) {
    Write-Host "🎨 Starting Frontend (port 8082)..." -ForegroundColor Cyan
    
    $frontendJob = Start-Job -ScriptBlock {
        param($frontendPath)
        Set-Location $frontendPath
        npm run dev
    } -ArgumentList $frontendPath
    
    Start-Sleep -Seconds 8
    
    # Check if frontend is running
    if (Test-Port -Port 8082) {
        Write-Host "✅ Frontend is ready!" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️  Frontend may still be starting..." -ForegroundColor Yellow
    }
}
else {
    Write-Host "⏭️  Skipping Frontend" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "✅ AgriSense Hybrid AI is running!" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""
Write-Host "Services:" -ForegroundColor Cyan
if (-not $SkipSCOLD -and $scoldJob) {
    Write-Host "  🔬 SCOLD VLM:  http://localhost:8001" -ForegroundColor White
}
Write-Host "  🖥️  Backend:    http://localhost:8004" -ForegroundColor White
if (-not $SkipFrontend -and $frontendJob) {
    Write-Host "  🎨 Frontend:   http://localhost:8082" -ForegroundColor White
}
Write-Host ""
Write-Host "API Endpoints:" -ForegroundColor Cyan
Write-Host "  📊 Status:     http://localhost:8004/health" -ForegroundColor White
Write-Host "  🦠 Disease:    http://localhost:8004/api/disease/detect" -ForegroundColor White
Write-Host "  🌿 Weeds:      http://localhost:8004/api/weed/analyze" -ForegroundColor White
Write-Host "  🤖 Hybrid AI:  http://localhost:8004/api/hybrid/status" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

# Monitor jobs
try {
    while ($true) {
        Start-Sleep -Seconds 5
        
        # Check if jobs are still running
        $runningJobs = Get-Job | Where-Object { $_.State -eq "Running" }
        if ($runningJobs.Count -eq 0) {
            Write-Host "⚠️  All services stopped" -ForegroundColor Yellow
            break
        }
    }
}
finally {
    Write-Host ""
    Write-Host "🛑 Stopping services..." -ForegroundColor Yellow
    
    # Stop all jobs
    Get-Job | Stop-Job
    Get-Job | Remove-Job
    
    Write-Host "✅ Cleanup complete" -ForegroundColor Green
}
