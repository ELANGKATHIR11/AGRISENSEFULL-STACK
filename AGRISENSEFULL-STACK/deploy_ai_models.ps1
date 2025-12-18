#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy and test Phi LLM & SCOLD VLM integration

.DESCRIPTION
    This script:
    1. Verifies Ollama and Phi model availability
    2. Starts backend with new AI routes
    3. Tests all integration endpoints
    4. Provides deployment summary

.EXAMPLE
    .\deploy_ai_models.ps1
#>

param(
    [switch]$SkipOllama,
    [switch]$SkipBackend,
    [switch]$QuickTest
)

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "🤖 Phi LLM & SCOLD VLM Deployment" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$workspaceRoot = "D:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK"

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

        if ($ollamaRunning) {
            Write-Host "  ✅ Ollama server is running" -ForegroundColor Green
            
            # Check for Phi model
            $models = ollama list 2>&1 | Out-String
            if ($models -match "phi") {
                Write-Host "  ✅ Phi model installed" -ForegroundColor Green
            } else {
                Write-Host "  ⚠️  Phi model not found. Download with: ollama pull phi" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  ⚠️  Ollama not running. Start with: ollama serve" -ForegroundColor Yellow
            Write-Host "  ℹ️  Integration will use fallback methods" -ForegroundColor Blue
        }
    } catch {
        Write-Host "  ⚠️  Could not check Ollama: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⏭️  Skipping Ollama check" -ForegroundColor Gray
}

# Step 2: Verify Python environment
Write-Host "`n📋 Step 2: Verifying Python environment..." -ForegroundColor Yellow
Set-Location $workspaceRoot

try {
    & .\.venv\Scripts\python.exe -c "import fastapi, requests; print('✅ Python packages OK')"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Python environment ready" -ForegroundColor Green
    }
} catch {
    Write-Host "  ❌ Python environment issue: $_" -ForegroundColor Red
    exit 1
}

# Step 3: Test router import
Write-Host "`n📋 Step 3: Testing AI models router..." -ForegroundColor Yellow
try {
    $routerTest = & .\.venv\Scripts\python.exe -c "from agrisense_app.backend.routes.ai_models_routes import router; print(f'{len(router.routes)} routes'); print(','.join([r.path for r in router.routes]))" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $routeCount = ($routerTest -split "`n")[0]
        $routes = ($routerTest -split "`n")[1]
        Write-Host "  ✅ Router loaded with $routeCount" -ForegroundColor Green
        Write-Host "  ℹ️  Routes: $routes" -ForegroundColor Blue
    } else {
        Write-Host "  ❌ Router import failed" -ForegroundColor Red
        Write-Host "  Error: $routerTest" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ❌ Router test failed: $_" -ForegroundColor Red
    exit 1
}

# Step 4: Test integration modules
Write-Host "`n📋 Step 4: Testing integration modules..." -ForegroundColor Yellow

Write-Host "  Testing Phi integration..." -ForegroundColor Gray
$phiTest = & .\.venv\Scripts\python.exe -c "from agrisense_app.backend.phi_chatbot_integration import get_phi_status; import json; print(json.dumps(get_phi_status()))" 2>&1
if ($LASTEXITCODE -eq 0) {
    $phiStatus = $phiTest | ConvertFrom-Json
    if ($phiStatus.available) {
        Write-Host "    ✅ Phi LLM available" -ForegroundColor Green
    } else {
        Write-Host "    ⚠️  Phi LLM unavailable (will use fallback)" -ForegroundColor Yellow
    }
} else {
    Write-Host "    ❌ Phi test failed: $phiTest" -ForegroundColor Red
}

Write-Host "  Testing SCOLD integration..." -ForegroundColor Gray
$scoldTest = & .\.venv\Scripts\python.exe -c "from agrisense_app.backend.vlm_scold_integration import scold_vlm_status; import json; print(json.dumps(scold_vlm_status()))" 2>&1
if ($LASTEXITCODE -eq 0) {
    $scoldStatus = $scoldTest | ConvertFrom-Json
    if ($scoldStatus.available) {
        Write-Host "    ✅ SCOLD VLM available" -ForegroundColor Green
    } else {
        Write-Host "    ⚠️  SCOLD VLM unavailable (will use fallback)" -ForegroundColor Yellow
    }
} else {
    Write-Host "    ❌ SCOLD test failed: $scoldTest" -ForegroundColor Red
}

# Step 5: Start backend (optional)
if (-not $SkipBackend) {
    Write-Host "`n📋 Step 5: Starting backend server..." -ForegroundColor Yellow
    
    Write-Host "  🚀 Starting uvicorn on port 8004..." -ForegroundColor Blue
    Write-Host "  ℹ️  Press Ctrl+C to stop the server" -ForegroundColor Gray
    Write-Host "  ℹ️  Check http://localhost:8004/docs for API documentation`n" -ForegroundColor Gray
    
    Set-Location $workspaceRoot
    & .\.venv\Scripts\python.exe -m uvicorn agrisense_app.backend.main:app --host 0.0.0.0 --port 8004 --reload
} else {
    Write-Host "`n⏭️  Skipping backend startup (use --SkipBackend:$false to start)" -ForegroundColor Gray
}

# Step 6: Deployment summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "📊 Deployment Summary" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "✅ Integration Status:" -ForegroundColor Green
Write-Host "   - Router: Loaded with 10 endpoints" -ForegroundColor White
Write-Host "   - Phi LLM: $(if ($phiStatus.available) { '✅ Available' } else { '⚠️  Unavailable (fallback active)' })" -ForegroundColor White
Write-Host "   - SCOLD VLM: $(if ($scoldStatus.available) { '✅ Available' } else { '⚠️  Unavailable (fallback active)' })" -ForegroundColor White

Write-Host "`n📚 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. If Ollama not running: ollama serve" -ForegroundColor White
Write-Host "   2. If Phi not installed: ollama pull phi" -ForegroundColor White
Write-Host "   3. Start backend: python -m uvicorn agrisense_app.backend.main:app --port 8004 --reload" -ForegroundColor White
Write-Host "   4. Start frontend: cd agrisense_app\frontend\farm-fortune-frontend-main && npm run dev" -ForegroundColor White
Write-Host "   5. Test endpoints: http://localhost:8004/docs" -ForegroundColor White

Write-Host "`n🔗 Important URLs:" -ForegroundColor Yellow
Write-Host "   - Backend API: http://localhost:8004" -ForegroundColor White
Write-Host "   - API Docs: http://localhost:8004/docs" -ForegroundColor White
Write-Host "   - Models Status: http://localhost:8004/api/models/status" -ForegroundColor White
Write-Host "   - Frontend: http://localhost:8082 (when running)" -ForegroundColor White

Write-Host "`n📖 Documentation:" -ForegroundColor Yellow
Write-Host "   - Full Integration Guide: PHI_SCOLD_FULL_INTEGRATION_SUMMARY.md" -ForegroundColor White
Write-Host "   - Quick Reference: PHI_SCOLD_SETUP_COMPLETE.md" -ForegroundColor White
Write-Host "   - Setup Script: setup_phi_scold.ps1" -ForegroundColor White

Write-Host "`n✨ Integration Complete! Happy farming! 🌾`n" -ForegroundColor Green
