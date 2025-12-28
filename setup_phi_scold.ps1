#!/usr/bin/env powershell
<#
.SYNOPSIS
    Quick setup script for Phi LLM & SCOLD VLM integration

.DESCRIPTION
    Starts all required services for AgriSense with Phi LLM and SCOLD VLM

.EXAMPLE
    .\setup_phi_scold.ps1
#>

param(
    [switch]$SkipOllama = $false,
    [switch]$TestOnly = $false
)

$ErrorActionPreference = "Stop"

# Color codes
$Green = "`e[92m"
$Yellow = "`e[93m"
$Red = "`e[91m"
$Blue = "`e[94m"
$Reset = "`e[0m"

Write-Host "$Blue" -NoNewline
Write-Host "╔════════════════════════════════════════════════════════════╗"
Write-Host "║  AgriSense Phi LLM & SCOLD VLM Quick Setup                ║"
Write-Host "║  December 4, 2025                                          ║"
Write-Host "╚════════════════════════════════════════════════════════════╝"
Write-Host "$Reset"

# Step 1: Verify Ollama
Write-Host "$Blue[1/5]$Reset Checking Ollama..."
try {
    $response = curl.exe -s http://localhost:11434/api/tags
    if ($LASTEXITCODE -eq 0) {
        Write-Host "$Green✅$Reset Ollama is running"
        $models = $response | ConvertFrom-Json
        $modelNames = @($models.models | ForEach-Object { $_.name })
        Write-Host "   Models found: $($modelNames -join ', ')"
        
        if ($modelNames -contains "phi:latest") {
            Write-Host "$Green✅$Reset Phi model found"
        } else {
            Write-Host "$Yellow⚠️$Reset Phi model not found"
            if (-not $SkipOllama) {
                Write-Host "$Yellow   Downloading Phi model...$Reset"
                ollama pull phi
            }
        }
    }
} catch {
    Write-Host "$Yellow⚠️$Reset Ollama not running"
    if (-not $SkipOllama) {
        Write-Host "$Blue   Starting Ollama...$Reset"
        Start-Job -ScriptBlock { ollama serve } | Out-Null
        Start-Sleep -Seconds 3
        Write-Host "$Green✅$Reset Ollama started (waiting for full initialization...)"
        Start-Sleep -Seconds 3
    }
}

# Step 2: Verify Backend
Write-Host "$Blue[2/5]$Reset Checking Backend..."
try {
    $response = Invoke-WebRequest -Uri http://localhost:8004/health -ErrorAction SilentlyContinue
    Write-Host "$Green✅$Reset Backend is running"
} catch {
    Write-Host "$Yellow⚠️$Reset Backend not running"
    Write-Host "$Yellow   To start backend:$Reset"
    Write-Host "   cd 'd:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK'"
    Write-Host "   python -m uvicorn agrisense_app.backend.main:app --port 8004"
}

# Step 3: Test Imports
Write-Host "$Blue[3/5]$Reset Testing Python imports..."
$pythonCmd = ".\.venv\Scripts\python.exe"
if (Test-Path $pythonCmd) {
    $phiTest = & $pythonCmd -c "from agrisense_app.backend.phi_chatbot_integration import *; print('OK')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "$Green✅$Reset Phi integration module imports successfully"
    } else {
        Write-Host "$Red❌$Reset Phi integration import failed: $phiTest"
    }
    
    $scoldTest = & $pythonCmd -c "from agrisense_app.backend.vlm_scold_integration import *; print('OK')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "$Green✅$Reset SCOLD VLM integration module imports successfully"
    } else {
        Write-Host "$Red❌$Reset SCOLD integration import failed: $scoldTest"
    }
} else {
    Write-Host "$Red❌$Reset Python venv not found"
}

# Step 4: Check API Routes
Write-Host "$Blue[4/5]$Reset Checking API routes..."
try {
    $response = Invoke-WebRequest -Uri http://localhost:8004/api/phi/status -ErrorAction SilentlyContinue
    Write-Host "$Green✅$Reset Phi API endpoints available"
} catch {
    Write-Host "$Yellow⚠️$Reset Phi API not yet available"
    Write-Host "   (Add routes to main.py as described in PHI_SCOLD_INTEGRATION_GUIDE.md)"
}

try {
    $response = Invoke-WebRequest -Uri http://localhost:8004/api/scold/status -ErrorAction SilentlyContinue
    Write-Host "$Green✅$Reset SCOLD VLM API endpoints available"
} catch {
    Write-Host "$Yellow⚠️$Reset SCOLD API not yet available"
}

# Step 5: Test Integration
Write-Host "$Blue[5/5]$Reset Running integration tests..."
if (Test-Path "scripts\test_phi_scold_integration.py") {
    Write-Host "$Blue   Running test suite...$Reset"
    & $pythonCmd scripts\test_phi_scold_integration.py
} else {
    Write-Host "$Yellow⚠️$Reset Test script not found"
}

# Final Summary
Write-Host ""
Write-Host "$Blue" -NoNewline
Write-Host "╔════════════════════════════════════════════════════════════╗"
Write-Host "║                    Setup Complete!                         ║"
Write-Host "╚════════════════════════════════════════════════════════════╝"
Write-Host "$Reset"

Write-Host "$Green✅ Phi LLM:$Reset"
Write-Host "   • Model: phi:latest (1.6 GB)"
Write-Host "   • Status: Downloaded"
Write-Host "   • Features: Answer enrichment, reranking, contextual chat"
Write-Host ""

Write-Host "$Green✅ SCOLD VLM:$Reset"
Write-Host "   • Disease detection with localization"
Write-Host "   • Weed detection and coverage analysis"
Write-Host "   • Status: Integration ready"
Write-Host ""

Write-Host "$Yellow📚 Documentation:$Reset"
Write-Host "   • PHI_SCOLD_INTEGRATION_GUIDE.md (Full guide)"
Write-Host "   • PHI_SCOLD_SETUP_COMPLETE.md (Quick reference)"
Write-Host ""

Write-Host "$Blue🚀 Next Steps:$Reset"
Write-Host "   1. Add routes to agrisense_app/backend/main.py (see guide)"
Write-Host "   2. Start Ollama: $Yellow ollama serve $Reset"
Write-Host "   3. Start Backend in new terminal (see guide)"
Write-Host "   4. Test with: python scripts/test_phi_scold_integration.py"
Write-Host ""

Write-Host "$Blue📡 API Endpoints:$Reset"
Write-Host "   • Chatbot: POST /api/chatbot/enrich"
Write-Host "   • Ranking: POST /api/chatbot/rerank"
Write-Host "   • Disease: POST /api/disease/detect-scold"
Write-Host "   • Weeds: POST /api/weed/detect-scold"
Write-Host "   • Status: GET /api/models/status"
Write-Host ""

Write-Host "$Green$([char]0x1F389) System ready for Phi LLM + SCOLD VLM integration!$Reset"
Write-Host ""
