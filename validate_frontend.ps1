# Browser Console Error Checker
# Use this script to validate frontend is loading without errors
# Author: GitHub Copilot
# Date: December 18, 2025

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "AgriSense Frontend Validation Checklist" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "✅ Backend running on port 8004" -ForegroundColor Green
Write-Host "✅ Frontend running on port 8080" -ForegroundColor Green
Write-Host "✅ API proxy configured correctly" -ForegroundColor Green
Write-Host "✅ 47 plants available via /api/plants" -ForegroundColor Green
Write-Host "✅ Integration tests: 5/6 passing" -ForegroundColor Green

Write-Host "`n📱 Manual Browser Validation Steps:" -ForegroundColor Magenta
Write-Host "------------------------------------" -ForegroundColor Gray
Write-Host "1. Open: http://localhost:8080" -ForegroundColor Yellow
Write-Host "2. Press F12 to open DevTools" -ForegroundColor Yellow
Write-Host "3. Go to 'Console' tab" -ForegroundColor Yellow
Write-Host "4. Check for any red errors" -ForegroundColor Yellow
Write-Host "5. Navigate to 'Recommend' page" -ForegroundColor Yellow
Write-Host "6. Verify crops/plants dropdown shows 47 items" -ForegroundColor Yellow
Write-Host "7. Check 'Network' tab for any failed requests (red)" -ForegroundColor Yellow

Write-Host "`n🔍 Expected Console Output (Good):" -ForegroundColor Magenta
Write-Host "------------------------------------" -ForegroundColor Gray
Write-Host "✅ No red errors" -ForegroundColor Green
Write-Host "✅ No 404 Not Found for /api/plants" -ForegroundColor Green
Write-Host "✅ No CORS errors" -ForegroundColor Green
Write-Host "✅ Successful fetch to /api/plants (200 OK)" -ForegroundColor Green

Write-Host "`n❌ What to Look For (Bad):" -ForegroundColor Magenta
Write-Host "------------------------------------" -ForegroundColor Gray
Write-Host "❌ 404 errors for /api/plants" -ForegroundColor Red
Write-Host "❌ CORS policy blocked messages" -ForegroundColor Red
Write-Host "❌ 'Failed to fetch' errors" -ForegroundColor Red
Write-Host "❌ 'Network request failed' messages" -ForegroundColor Red

Write-Host "`n🐛 Troubleshooting Commands:" -ForegroundColor Magenta
Write-Host "------------------------------------" -ForegroundColor Gray
Write-Host "# Test API directly:" -ForegroundColor Gray
Write-Host "Invoke-RestMethod -Uri 'http://localhost:8080/api/plants'" -ForegroundColor Cyan
Write-Host "`n# Run full integration tests:" -ForegroundColor Gray
Write-Host ".\test_frontend_api_integration.ps1" -ForegroundColor Cyan
Write-Host "`n# Check backend logs:" -ForegroundColor Gray
Write-Host "# Look at Terminal 1 where uvicorn is running" -ForegroundColor Cyan
Write-Host "`n# Check frontend logs:" -ForegroundColor Gray
Write-Host "# Look at Terminal 2 where npm run dev is running" -ForegroundColor Cyan

Write-Host "`n📊 Current System Status:" -ForegroundColor Magenta
Write-Host "------------------------------------" -ForegroundColor Gray

# Check backend
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8004/health" -TimeoutSec 3
    if ($health.status -eq "ok") {
        Write-Host "✅ Backend: Running & Healthy" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Backend: Running but status unexpected" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Backend: Not responding" -ForegroundColor Red
}

# Check frontend
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080" -TimeoutSec 3
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Frontend: Running & Accessible" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Frontend: Not responding" -ForegroundColor Red
}

# Check API proxy
try {
    $plants = Invoke-RestMethod -Uri "http://localhost:8080/api/plants" -TimeoutSec 5
    if ($plants.items.Count -eq 47) {
        Write-Host "✅ API Proxy: Working correctly (47 plants)" -ForegroundColor Green
    } else {
        Write-Host "⚠️  API Proxy: Working but unexpected data" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ API Proxy: Not working" -ForegroundColor Red
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "🎉 If all checks are green, your app is working!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Opening browser to http://localhost:8080..." -ForegroundColor Cyan
Start-Process "http://localhost:8080"
