# Frontend-Backend API Integration Test Script
# Tests all critical endpoints through the Vite dev proxy
# Author: GitHub Copilot
# Date: December 18, 2025

$ErrorActionPreference = "Continue"
$frontendPort = 8080
$backendPort = 8004
$baseUrl = "http://localhost:$frontendPort"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "AgriSense Frontend-Backend Integration Test" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Test counters
$passed = 0
$failed = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET",
        [hashtable]$Body = $null,
        [int]$ExpectedStatus = 200,
        [scriptblock]$Validator = $null
    )
    
    Write-Host "Testing: $Name" -ForegroundColor Yellow
    Write-Host "  URL: $Url" -ForegroundColor Gray
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            TimeoutSec = 10
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json)
            $params.ContentType = "application/json"
        }
        
        $response = Invoke-RestMethod @params
        
        # Run validator if provided
        $validationPassed = $true
        if ($Validator) {
            $validationPassed = & $Validator $response
        }
        
        if ($validationPassed) {
            Write-Host "  ✅ PASSED" -ForegroundColor Green
            $script:passed++
            return $true
        } else {
            Write-Host "  ❌ FAILED (validation)" -ForegroundColor Red
            $script:failed++
            return $false
        }
        
    } catch {
        Write-Host "  ❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
            Write-Host "  Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Yellow
        }
        $script:failed++
        return $false
    }
}

Write-Host "1. Testing Backend Direct (Port $backendPort)" -ForegroundColor Magenta
Write-Host "--------------------------------------`n" -ForegroundColor Gray

Test-Endpoint `
    -Name "Backend Health Check" `
    -Url "http://localhost:$backendPort/health" `
    -Validator { param($r) $r.status -eq "ok" }

Test-Endpoint `
    -Name "Backend /plants Endpoint" `
    -Url "http://localhost:$backendPort/plants" `
    -Validator { param($r) $r.items.Count -eq 47 }

Write-Host "`n2. Testing Frontend Proxy (Port $frontendPort)" -ForegroundColor Magenta
Write-Host "--------------------------------------`n" -ForegroundColor Gray

Test-Endpoint `
    -Name "Frontend Health Check" `
    -Url "$baseUrl/health" `
    -Validator { param($r) $r.status -eq "ok" }

Test-Endpoint `
    -Name "Frontend /api/plants Proxy" `
    -Url "$baseUrl/api/plants" `
    -Validator { 
        param($r) 
        if ($r.items.Count -eq 47) {
            Write-Host "    Plants: $($r.items.Count) items" -ForegroundColor Cyan
            $r.items | Select-Object -First 5 | ForEach-Object { 
                Write-Host "      - $($_.label)" -ForegroundColor Gray 
            }
            return $true
        }
        return $false
    }

Test-Endpoint `
    -Name "Frontend /api/crops Proxy" `
    -Url "$baseUrl/api/crops" `
    -Validator { 
        param($r) 
        Write-Host "    Crop cards: $($r.Count) items" -ForegroundColor Cyan
        return $r.Count -ge 1
    }

Test-Endpoint `
    -Name "Frontend /api/soil/types Proxy" `
    -Url "$baseUrl/api/soil/types" `
    -Validator { 
        param($r) 
        if ($r.items) {
            Write-Host "    Soil types: $($r.items.Count) items ($($r.items -join ', '))" -ForegroundColor Cyan
            return $r.items.Count -ge 1
        }
        return $false
    }

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Test Results Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ Passed: $passed" -ForegroundColor Green
Write-Host "❌ Failed: $failed" -ForegroundColor Red
Write-Host "Total: $($passed + $failed)" -ForegroundColor Yellow

if ($failed -eq 0) {
    Write-Host "`n🎉 ALL TESTS PASSED! Frontend-Backend integration is working correctly!" -ForegroundColor Green
    Write-Host "`nYou can now access the application at: http://localhost:$frontendPort" -ForegroundColor Cyan
    exit 0
} else {
    Write-Host "`n⚠️  Some tests failed. Please review the errors above." -ForegroundColor Yellow
    exit 1
}
