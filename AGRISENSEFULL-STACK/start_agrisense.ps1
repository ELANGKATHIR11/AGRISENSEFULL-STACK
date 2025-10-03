# AgriSense Unified Server Startup Script for PowerShell
# This script starts both frontend and backend on a single server

Write-Host "🌾 Starting AgriSense Unified Server..." -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Blue

# Check if virtual environment exists
if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found at .venv" -ForegroundColor Red
    Write-Host "Please ensure you have set up the Python virtual environment" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".venv\Scripts\Activate.ps1"

# Set environment variables for optimal performance
$env:AGRISENSE_DISABLE_ML = "1"

# Start the unified server
Write-Host "Starting AgriSense server..." -ForegroundColor Green
Write-Host "Frontend will be served at: http://localhost:8004/ui" -ForegroundColor Cyan
Write-Host "API documentation at: http://localhost:8004/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

try {
    python start_agrisense.py $args
}
catch {
    Write-Host "Error starting server: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Server stopped." -ForegroundColor Green
Read-Host "Press Enter to exit"