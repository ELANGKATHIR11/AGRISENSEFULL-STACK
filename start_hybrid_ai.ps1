#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start AgriSense Hybrid AI System

.DESCRIPTION
    Launches the complete hybrid LLM+VLM agricultural AI system:
    - Ollama server with Phi model
    - AgriSense backend with Hybrid AI routes
    - Optional: Frontend development server

.EXAMPLE
    .\start_hybrid_ai.ps1
    .\start_hybrid_ai.ps1 -SkipFrontend
#>

param(
    [switch]$SkipFrontend,
    [switch]$SkipOllama
)

$ErrorActionPreference = "Continue"

Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     🌾 AgriSense Hybrid AI - Startup Script 🌾              ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$workspaceRoot = $PSScriptRoot

# Step 1: Check Ollama
Write-Host "📋 Step 1: Checking Ollama..." -ForegroundColor Yellow
if (-not $SkipOllama) {
    try {
        $ollamaRunning = $false
        try {
            $null = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction SilentlyContinue
            $ollamaRunning = $true
        } catch {
            $ollamaRunning = $false
        }
        
        if (-not $ollamaRunning) {
            Write-Host "  🚀 Starting Ollama server..." -ForegroundColor Blue
            Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
            Start-Sleep -Seconds 5
            Write-Host "  ✅ Ollama started" -ForegroundColor Green
        } else {
            Write-Host "  ✅ Ollama already running" -ForegroundColor Green
        }
        
        # Check Phi model
        $models = ollama list 2>&1 | Out-String
        if ($models -match "phi") {
            Write-Host "  ✅ Phi model available" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  Phi model not found" -ForegroundColor Yellow
            Write-Host "     Downloading Phi model (1.6GB)..." -ForegroundColor Yellow
            ollama pull phi:latest
            Write-Host "  ✅ Phi model downloaded" -ForegroundColor Green
        }
        
    } catch {
        Write-Host "  ❌ Ollama setup failed: $_" -ForegroundColor Red
    }
} else {
    Write-Host "  ⏭️  Skipping Ollama check" -ForegroundColor Gray
}

# Step 2: Start Backend
Write-Host "`n📋 Step 2: Starting AgriSense Backend..." -ForegroundColor Yellow

try {
    # Clean up old processes
    Get-Process python* -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    
    Set-Location $workspaceRoot
    
    Write-Host "  🚀 Launching backend on port 8004..." -ForegroundColor Blue
    
    # Start backend in background job
    $null = Start-Job -ScriptBlock {
        param($root)
        Set-Location $root
        & .\.venv\Scripts\python.exe -m uvicorn agrisense_app.backend.main:app --host 0.0.0.0 --port 8004
    } -ArgumentList $workspaceRoot
    
    Write-Host "  ⏳ Waiting for backend startup..." -ForegroundColor Gray
    Start-Sleep -Seconds 10
    
    # Check backend health
    try {
        $healthResponse = Invoke-WebRequest -Uri "http://localhost:8004/health" -UseBasicParsing -TimeoutSec 5
        Write-Host "  ✅ Backend is healthy! (Status: $($healthResponse.StatusCode))" -ForegroundColor Green
        
        # Check Hybrid AI
        $hybridHealth = Invoke-WebRequest -Uri "http://localhost:8004/api/hybrid/health" -UseBasicParsing -TimeoutSec 5
        $hybridData = $hybridHealth.Content | ConvertFrom-Json
        
        Write-Host "`n  🤖 Hybrid AI Status:" -ForegroundColor Cyan
        Write-Host "     Phi LLM  : $($hybridData.components.phi_llm)" -ForegroundColor White
        Write-Host "     SCOLD VLM: $($hybridData.components.scold_vlm)" -ForegroundColor White
        
    } catch {
        Write-Host "  ⚠️  Backend starting but health check pending..." -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "  ❌ Backend startup failed: $_" -ForegroundColor Red
    exit 1
}

# Step 3: Start Frontend (optional)
if (-not $SkipFrontend) {
    Write-Host "`n📋 Step 3: Starting Frontend..." -ForegroundColor Yellow
    
    $frontendPath = Join-Path $workspaceRoot "agrisense_app\frontend\farm-fortune-frontend-main"
    
    if (Test-Path $frontendPath) {
        try {
            Set-Location $frontendPath
            
            Write-Host "  🚀 Launching Vite dev server..." -ForegroundColor Blue
            
            $null = Start-Job -ScriptBlock {
                param($path)
                Set-Location $path
                npm run dev
            } -ArgumentList $frontendPath
            
            Start-Sleep -Seconds 5
            Write-Host "  ✅ Frontend starting..." -ForegroundColor Green
            
        } catch {
            Write-Host "  ⚠️  Frontend startup issue: $_" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ⚠️  Frontend path not found" -ForegroundColor Yellow
    }
} else {
    Write-Host "`n⏭️  Skipping frontend startup" -ForegroundColor Gray
}

# Summary
Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║            ✅ HYBRID AI SYSTEM RUNNING ✅                     ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "🔗 Access Points:" -ForegroundColor Yellow
Write-Host "   Backend API      : http://localhost:8004" -ForegroundColor White
Write-Host "   API Documentation: http://localhost:8004/docs" -ForegroundColor White
Write-Host "   Hybrid AI Health : http://localhost:8004/api/hybrid/health" -ForegroundColor White
if (-not $SkipFrontend) {
    Write-Host "   Frontend UI      : http://localhost:8082" -ForegroundColor White
}

Write-Host "`n📝 Quick Tests:" -ForegroundColor Yellow
Write-Host "   Test Suite       : python test_hybrid_ai.py" -ForegroundColor Gray
Write-Host "   Status Check     : curl http://localhost:8004/api/hybrid/status" -ForegroundColor Gray
Write-Host "   Text Query       : curl -X POST http://localhost:8004/api/hybrid/text -H 'Content-Type: application/json' -d '{""query"":""When to plant wheat?""}'" -ForegroundColor Gray

Write-Host "`n💡 Tips:" -ForegroundColor Cyan
Write-Host "   - Replace sample images in test_hybrid_ai.py with real farm images" -ForegroundColor White
Write-Host "   - Check logs: Get-Job | Receive-Job" -ForegroundColor White
Write-Host "   - Stop all: Get-Job | Stop-Job; Get-Process python* | Stop-Process" -ForegroundColor White

Write-Host "`n✨ System ready for agricultural AI analysis! ✨`n" -ForegroundColor Green

# Keep script running
Write-Host "Press Ctrl+C to stop all services..." -ForegroundColor Gray
try {
    while ($true) {
        Start-Sleep -Seconds 10
        
        # Check if jobs are still running
        $runningJobs = Get-Job | Where-Object { $_.State -eq 'Running' }
        if ($runningJobs.Count -eq 0) {
            Write-Host "`n⚠️  All services stopped" -ForegroundColor Yellow
            break
        }
    }
} finally {
    Write-Host "`n🛑 Stopping services..." -ForegroundColor Yellow
    Get-Job | Stop-Job
    Get-Job | Remove-Job
    Write-Host "✅ Cleanup complete`n" -ForegroundColor Green
}
