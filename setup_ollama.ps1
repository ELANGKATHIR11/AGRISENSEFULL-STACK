#!/usr/bin/env powershell
<#
.SYNOPSIS
    Quick setup script for Ollama LLM integration with AgriSense chatbot

.DESCRIPTION
    Automates:
    1. Ollama installation check
    2. Model download (Phi recommended)
    3. Python dependencies installation
    4. Backend startup with Ollama configuration
    5. Chatbot testing

.EXAMPLE
    .\setup_ollama.ps1 -Model phi
    .\setup_ollama.ps1 -Model mistral -TestOnly

.PARAMETER Model
    Ollama model to use: phi, mistral, tinyllama, neural-chat, llama2
    Default: phi (fastest for resource-limited systems)

.PARAMETER TestOnly
    Only test existing installation without downloading new model
    Default: false

.PARAMETER SkipTest
    Skip chatbot testing after setup
    Default: false
#>

param(
    [ValidateSet("phi", "mistral", "tinyllama", "neural-chat", "llama2")]
    [string]$Model = "phi",
    
    [switch]$TestOnly,
    [switch]$SkipTest
)

# Color output helpers
function Write-Status { Write-Host "[✓] $args" -ForegroundColor Green }
function Write-Warning { Write-Host "[⚠] $args" -ForegroundColor Yellow }
function Write-Error { Write-Host "[✗] $args" -ForegroundColor Red }
function Write-Info { Write-Host "[ℹ] $args" -ForegroundColor Cyan }

Write-Info "AgriSense Ollama Setup"
Write-Info "=====================`n"

# ============================================================================
# 1. CHECK OLLAMA INSTALLATION
# ============================================================================
Write-Info "Step 1: Checking Ollama installation..."

try {
    $null = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -ErrorAction Stop
    Write-Status "Ollama is running on http://localhost:11434"
} catch {
    Write-Error "Ollama is not running!"
    Write-Warning "Please install Ollama from: https://ollama.ai/download"
    Write-Warning "Or run: ollama serve"
    exit 1
}

# ============================================================================
# 2. DOWNLOAD MODEL
# ============================================================================
if (-not $TestOnly) {
    Write-Info "`nStep 2: Downloading model '$Model'..."
    Write-Warning "This may take 5-15 minutes depending on your internet"
    
    try {
        ollama pull $Model
        Write-Status "Model '$Model' downloaded successfully"
    } catch {
        Write-Error "Failed to download model: $_"
        exit 1
    }
} else {
    Write-Info "Step 2: Skipping model download (test mode)"
}

# ============================================================================
# 3. VERIFY MODEL AVAILABLE
# ============================================================================
Write-Info "`nStep 3: Verifying model availability..."

try {
    $models = ollama list
    if ($models -like "*$Model*") {
        Write-Status "Model '$Model' is available"
    } else {
        Write-Error "Model '$Model' not found in: $models"
        exit 1
    }
} catch {
    Write-Error "Failed to list models: $_"
    exit 1
}

# ============================================================================
# 4. TEST OLLAMA MODEL
# ============================================================================
Write-Info "`nStep 4: Testing Ollama model generation..."

$testPrompt = @{
    model = $Model
    prompt = "Tell me about rice irrigation in one sentence"
    stream = $false
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/generate" `
        -Method POST `
        -Body $testPrompt `
        -ContentType "application/json" `
        -ErrorAction Stop
    
    $data = $response.Content | ConvertFrom-Json
    $responseText = $data.response.Substring(0, [Math]::Min(100, $data.response.Length))
    
    Write-Status "Model test successful!"
    Write-Info "Sample response: $responseText..."
} catch {
    Write-Error "Model test failed: $_"
    exit 1
}

# ============================================================================
# 5. INSTALL PYTHON DEPENDENCIES
# ============================================================================
Write-Info "`nStep 5: Installing Python dependencies..."

try {
    $backendDir = "d:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK"
    
    if (Test-Path "$backendDir\.venv\Scripts\pip.exe") {
        & "$backendDir\.venv\Scripts\pip.exe" install ollama --upgrade -q
        Write-Status "Python Ollama client installed"
    } else {
        Write-Error "Virtual environment not found at $backendDir\.venv"
        Write-Warning "Please create venv: python -m venv .venv"
        exit 1
    }
} catch {
    Write-Error "Failed to install Python dependencies: $_"
    exit 1
}

# ============================================================================
# 6. UPDATE ENVIRONMENT
# ============================================================================
Write-Info "`nStep 6: Configuring environment variables..."

# Set for this session
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:OLLAMA_MODEL = $Model
$env:OLLAMA_TIMEOUT = "30"
$env:LLM_PROVIDER = "ollama"
$env:AGRISENSE_DISABLE_ML = "1"  # Faster startup

Write-Status "Environment variables configured:
  OLLAMA_BASE_URL: $env:OLLAMA_BASE_URL
  OLLAMA_MODEL: $env:OLLAMA_MODEL
  LLM_PROVIDER: $env:LLM_PROVIDER"

# ============================================================================
# 7. TEST OLLAMA INTEGRATION
# ============================================================================
if (-not $SkipTest) {
    Write-Info "`nStep 7: Testing AgriSense backend with Ollama..."
    
    try {
        $backendDir = "d:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK"
        
        # Test Python import
        $testScript = @"
import sys
sys.path.insert(0, '.')
try:
    from agrisense_app.backend import llm_clients_ollama
    status = llm_clients_ollama.ollama_status()
    print(f"✓ Ollama status: {status['available']}")
    print(f"  Model: {status['model']}")
    print(f"  Base URL: {status['base_url']}")
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
"@
        
        $tempFile = New-TemporaryFile -Suffix ".py"
        $testScript | Set-Content $tempFile.FullName
        
        Push-Location $backendDir
        & "$backendDir\.venv\Scripts\python.exe" $tempFile.FullName
        
        if ($LASTEXITCODE -eq 0) {
            Write-Status "Backend integration test passed!"
        } else {
            Write-Error "Backend integration test failed"
            exit 1
        }
        
        Pop-Location
        Remove-Item $tempFile.FullName
        
    } catch {
        Write-Error "Backend test error: $_"
    }
}

# ============================================================================
# SUMMARY
# ============================================================================
Write-Info "`n" + ("=" * 70)
Write-Status "Ollama Setup Complete! ✨"
Write-Info "=" * 70

Write-Info "`nNext steps to run AgriSense with Ollama:"
Write-Info "
1. Terminal 1 - Start Ollama (usually auto-starts):
   > ollama serve

2. Terminal 2 - Start Backend:
   > cd 'd:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK'
   > .\.venv\Scripts\Activate.ps1
   > `$env:OLLAMA_MODEL='$Model'
   > `$env:AGRISENSE_DISABLE_ML='1'
   > python -m uvicorn agrisense_app.backend.main:app --port 8004 --reload

3. Terminal 3 - Start Frontend:
   > cd 'd:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK\agrisense_app\frontend\farm-fortune-frontend-main'
   > npm run dev

4. Browser - Test Chatbot:
   > http://localhost:8082
   > Ask agricultural question and watch Ollama power responses!

Configuration:
  Model:        $Model
  Ollama URL:   http://localhost:11434
  Backend Port: 8004
  Frontend:     Usually 8082 (Vite auto-selects)

Quick Commands:
  List models:     ollama list
  Test model:      ollama run $Model
  Benchmark:       Measure response time with: curl http://localhost:11434/api/generate
  Change model:    Set `$env:OLLAMA_MODEL='mistral'

Troubleshooting:
  - Ollama not running? Run: ollama serve
  - Slow responses? Use 'tinyllama' instead of '$Model'
  - Free memory: curl -X POST http://localhost:11434/api/generate -d '{\"model\": \"$Model\", \"keep_alive\": 0}'
"

Write-Status "Ready to go! 🚀"
