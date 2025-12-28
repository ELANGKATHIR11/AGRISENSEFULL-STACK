#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start AgriSense with hardware-optimized configuration
.DESCRIPTION
    Optimized for Intel Core Ultra 9 275HX (32 threads) + RTX 5060 (8GB)
    Performance mode with multi-worker uvicorn and full CPU/GPU utilization
#>

param(
    [switch]$NoBrowser,
    [switch]$Monitor,
    [int]$Workers = 8,
    [string]$HostAddress = "0.0.0.0",
    [int]$Port = 8004
)

$ErrorActionPreference = "Stop"

# Check PowerShell execution policy
try {
    $policy = Get-ExecutionPolicy -Scope CurrentUser
    if ($policy -eq "Restricted" -or $policy -eq "Undefined") {
        Write-Host "`n⚠️  PowerShell execution policy is restrictive: $policy" -ForegroundColor Yellow
        Write-Host "   Run this command to fix: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
        Write-Host "   Or use: .venv\Scripts\python.exe directly instead of activating`n" -ForegroundColor Gray
    }
} catch {}

Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   🚀 AgriSense - Hardware Optimized Startup 🚀               ║" -ForegroundColor Cyan
Write-Host "║   Intel Core Ultra 9 275HX (32 threads)                      ║" -ForegroundColor Cyan
Write-Host "║   NVIDIA RTX 5060 Laptop GPU (8GB)                           ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# ============================================================================
# System Check
# ============================================================================
Write-Host "📊 System Check:" -ForegroundColor Yellow
try {
    $cpuInfo = Get-WmiObject Win32_Processor | Select-Object -First 1
    Write-Host "   ✓ CPU: $($cpuInfo.Name)" -ForegroundColor Green
    Write-Host "   ✓ Cores: $($cpuInfo.NumberOfCores) | Threads: $($cpuInfo.NumberOfLogicalProcessors)" -ForegroundColor Green
    
    $memory = Get-WmiObject Win32_ComputerSystem
    $totalRAM = [math]::Round($memory.TotalPhysicalMemory / 1GB, 2)
    Write-Host "   ✓ RAM: $totalRAM GB" -ForegroundColor Green
} catch {
    Write-Host "   ⚠ Could not retrieve CPU info" -ForegroundColor Yellow
}

try {
    $gpuInfo = nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>$null
    if ($gpuInfo) {
        Write-Host "   ✓ GPU: $gpuInfo" -ForegroundColor Green
    } else {
        Write-Host "   ⚠ GPU: Not detected (will use CPU)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ⚠ GPU: nvidia-smi not available (will use CPU)" -ForegroundColor Yellow
}

# ============================================================================
# Environment Setup
# ============================================================================
Write-Host "`n⚙️  Loading hardware-optimized configuration..." -ForegroundColor Yellow

# Check for virtual environment
$venvPath = Join-Path $PSScriptRoot ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "   ❌ Virtual environment not found at $venvPath" -ForegroundColor Red
    Write-Host "   Run: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    . $activateScript
    Write-Host "   ✓ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "   ❌ Activation script not found" -ForegroundColor Red
    exit 1
}

# Load optimized environment variables
$envFile = Join-Path $PSScriptRoot ".env.production.optimized"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^=#]+)=(.*)$' -and -not $_.Trim().StartsWith('#')) {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
    Write-Host "   ✓ Configuration loaded from .env.production.optimized" -ForegroundColor Green
} else {
    Write-Host "   ⚠ Optimized config not found, using defaults" -ForegroundColor Yellow
}

# Set critical environment variables
[System.Environment]::SetEnvironmentVariable("OMP_NUM_THREADS", "24", "Process")
[System.Environment]::SetEnvironmentVariable("MKL_NUM_THREADS", "24", "Process")
[System.Environment]::SetEnvironmentVariable("NUMEXPR_NUM_THREADS", "24", "Process")
[System.Environment]::SetEnvironmentVariable("PYTHONTHREADED", "1", "Process")
[System.Environment]::SetEnvironmentVariable("CUDA_VISIBLE_DEVICES", "0", "Process")

Write-Host "   ✓ Threading optimizations enabled (24 threads)" -ForegroundColor Green

# ============================================================================
# Database Initialization
# ============================================================================
Write-Host "`n💾 Checking database..." -ForegroundColor Yellow
$dbPath = Join-Path $PSScriptRoot "sensors.db"
if (Test-Path $dbPath) {
    $dbSize = [math]::Round((Get-Item $dbPath).Length / 1MB, 2)
    Write-Host "   ✓ Database exists ($dbSize MB)" -ForegroundColor Green
} else {
    Write-Host "   ℹ Database will be created on first startup" -ForegroundColor Cyan
}

# ============================================================================
# Start Backend (Multi-Worker)
# ============================================================================
Write-Host "`n🔥 Starting FastAPI backend with $Workers workers..." -ForegroundColor Yellow

$backendArgs = @(
    "-m", "uvicorn",
    "agrisense_app.backend.main:app",
    "--host", $HostAddress,
    "--port", $Port,
    "--workers", $Workers,
    "--backlog", "4096",
    "--limit-concurrency", "2000",
    "--timeout-keep-alive", "75",
    "--log-level", "info",
    "--access-log"
)

Write-Host "   Command: python $($backendArgs -join ' ')" -ForegroundColor Gray

$backendProcess = Start-Process `
    -FilePath "python" `
    -ArgumentList $backendArgs `
    -PassThru `
    -NoNewWindow

Start-Sleep -Seconds 5

# Check if backend started successfully
$backendRunning = Get-Process -Id $backendProcess.Id -ErrorAction SilentlyContinue
if ($backendRunning) {
    Write-Host "   ✓ Backend started (PID: $($backendProcess.Id))" -ForegroundColor Green
} else {
    Write-Host "   ❌ Backend failed to start" -ForegroundColor Red
    exit 1
}

# Test API endpoint
Write-Host "`n🧪 Testing API health..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
try {
    $healthCheck = Invoke-WebRequest -Uri "http://localhost:$Port/health" -UseBasicParsing -ErrorAction Stop
    if ($healthCheck.StatusCode -eq 200) {
        Write-Host "   ✓ API is responding" -ForegroundColor Green
    }
} catch {
    Write-Host "   ⚠ Health check failed, but continuing..." -ForegroundColor Yellow
}

# ============================================================================
# Success Summary
# ============================================================================
Write-Host "`n✅ AgriSense started in OPTIMIZED mode!" -ForegroundColor Green
Write-Host "`n📍 Access points:" -ForegroundColor Cyan
Write-Host "   Main App:    http://localhost:$Port/ui" -ForegroundColor White
Write-Host "   API Docs:    http://localhost:$Port/docs" -ForegroundColor White
Write-Host "   ReDoc:       http://localhost:$Port/redoc" -ForegroundColor White
Write-Host "   Health:      http://localhost:$Port/health" -ForegroundColor White

Write-Host "`n🎯 Performance Configuration:" -ForegroundColor Cyan
Write-Host "   Workers:      $Workers (P-cores)" -ForegroundColor White
Write-Host "   Threads:      24 (OMP/MKL)" -ForegroundColor White
Write-Host "   Concurrency:  2000 connections/worker" -ForegroundColor White
Write-Host "   Throughput:   ~16,000 concurrent connections" -ForegroundColor White
Write-Host "   Expected:     5,000-10,000 req/s" -ForegroundColor White

Write-Host "`n💡 Monitoring Commands:" -ForegroundColor Yellow
Write-Host "   CPU Usage:    Get-Process python | Select-Object CPU,WorkingSet64" -ForegroundColor Gray
Write-Host "   GPU Usage:    nvidia-smi dmon -s ucm -c 60" -ForegroundColor Gray
Write-Host "   Load Test:    locust -f locustfile.py --host=http://localhost:$Port" -ForegroundColor Gray
Write-Host "   Memory:       Get-Process python | Measure-Object WorkingSet64 -Sum" -ForegroundColor Gray

# ============================================================================
# Open Browser
# ============================================================================
if (-not $NoBrowser) {
    Start-Sleep -Seconds 2
    Write-Host "`n🌐 Opening browser..." -ForegroundColor Cyan
    Start-Process "http://localhost:$Port/docs"
}

# ============================================================================
# Monitor Mode (Optional)
# ============================================================================
if ($Monitor) {
    Write-Host "`n📊 Starting monitoring dashboard..." -ForegroundColor Yellow
    Write-Host "Press Ctrl+C to stop monitoring`n" -ForegroundColor Gray
    
    while ($true) {
        Clear-Host
        Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
        Write-Host "   AgriSense Performance Monitor - $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Cyan
        Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
        
        # CPU Usage
        $processes = Get-Process python -ErrorAction SilentlyContinue
        if ($processes) {
            $totalCPU = ($processes | Measure-Object CPU -Sum).Sum
            $totalMemMB = [math]::Round(($processes | Measure-Object WorkingSet64 -Sum).Sum / 1MB, 2)
            Write-Host "`nPython Processes:" -ForegroundColor Yellow
            Write-Host "   Total CPU Time: $([math]::Round($totalCPU, 2))s" -ForegroundColor White
            Write-Host "   Total Memory:   $totalMemMB MB" -ForegroundColor White
            Write-Host "   Process Count:  $($processes.Count)" -ForegroundColor White
        }
        
        # GPU Usage
        try {
            $gpuStats = nvidia-smi --query-gpu=utilization.gpu,utilization.memory,memory.used,temperature.gpu --format=csv,noheader,nounits 2>$null
            if ($gpuStats) {
                $stats = $gpuStats -split ","
                Write-Host "`nGPU Status (RTX 5060):" -ForegroundColor Yellow
                Write-Host "   GPU Usage:    $($stats[0].Trim())%" -ForegroundColor White
                Write-Host "   Memory Usage: $($stats[1].Trim())%" -ForegroundColor White
                Write-Host "   Memory Used:  $($stats[2].Trim()) MB" -ForegroundColor White
                Write-Host "   Temperature:  $($stats[3].Trim())°C" -ForegroundColor White
            }
        } catch {}
        
        # System Memory
        $mem = Get-WmiObject Win32_OperatingSystem
        $totalMemGB = [math]::Round($mem.TotalVisibleMemorySize / 1MB, 2)
        $freeMemGB = [math]::Round($mem.FreePhysicalMemory / 1MB, 2)
        $usedMemGB = $totalMemGB - $freeMemGB
        $memPercent = [math]::Round(($usedMemGB / $totalMemGB) * 100, 1)
        
        Write-Host "`nSystem Memory:" -ForegroundColor Yellow
        Write-Host "   Total: $totalMemGB GB | Used: $usedMemGB GB | Free: $freeMemGB GB ($memPercent%)" -ForegroundColor White
        
        Write-Host "`nPress Ctrl+C to exit monitoring..." -ForegroundColor Gray
        Start-Sleep -Seconds 5
    }
} else {
    Write-Host "`n👉 TIP: Run with -Monitor flag for real-time performance dashboard" -ForegroundColor Cyan
    Write-Host "`nPress Ctrl+C to stop server..." -ForegroundColor Gray
    
    try {
        Wait-Process -Id $backendProcess.Id
    } catch {
        Write-Host "`n🛑 Server stopped" -ForegroundColor Yellow
    }
}
