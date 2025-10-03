#!/usr/bin/env pwsh
# AgriSense Application Startup Script
# This script starts the AgriSense application with both frontend and backend on a single server

Write-Host "🌱 Starting AgriSense Application..." -ForegroundColor Green

# Change to the backend directory
Set-Location "d:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK\agrisense_app\backend"

# Set environment variables
$env:AGRISENSE_DISABLE_ML = "1"

Write-Host "📍 Backend directory: $PWD" -ForegroundColor Yellow
Write-Host "🔧 ML disabled for performance" -ForegroundColor Yellow
Write-Host "🚀 Starting server on http://localhost:8004" -ForegroundColor Yellow
Write-Host "🌐 Frontend will be available at http://localhost:8004/ui" -ForegroundColor Green
Write-Host "📱 API endpoints available at http://localhost:8004/api/..." -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Red
Write-Host ""

# Start the server
python -m uvicorn main:app --reload --port 8004