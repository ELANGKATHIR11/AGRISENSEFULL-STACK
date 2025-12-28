# AgriSense Full-Stack Comprehensive Test Suite
# This PowerShell script tests every component of the AgriSense application

param(
    [string]$BaseUrl = "http://localhost:8004",
    [switch]$Verbose = $false
)

Write-Host "🌱 AgriSense Full-Stack Test Suite" -ForegroundColor Green
Write-Host "🔗 Testing URL: $BaseUrl" -ForegroundColor Yellow
Write-Host "📅 Test Date: $(Get-Date)" -ForegroundColor Gray
Write-Host ""

# Test Results Storage
$TestResults = @{
    Passed = 0
    Failed = 0
    Total = 0
    Details = @()
}

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET",
        [hashtable]$Body = $null,
        [string]$ExpectedContent = $null,
        [int]$ExpectedStatusCode = 200
    )
    
    $TestResults.Total++
    Write-Host "🧪 Testing: $Name" -ForegroundColor Cyan
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            ContentType = "application/json"
            UseBasicParsing = $true
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json -Depth 10)
        }
        
        $response = Invoke-RestMethod @params -ErrorAction Stop
        
        if ($ExpectedContent -and $response -notmatch $ExpectedContent) {
            throw "Expected content '$ExpectedContent' not found in response"
        }
        
        Write-Host "  ✅ PASS: $Name" -ForegroundColor Green
        $TestResults.Passed++
        $TestResults.Details += @{
            Test = $Name
            Status = "PASS"
            Response = $response
            Url = $Url
        }
        return $response
    }
    catch {
        Write-Host "  ❌ FAIL: $Name - $($_.Exception.Message)" -ForegroundColor Red
        $TestResults.Failed++
        $TestResults.Details += @{
            Test = $Name
            Status = "FAIL"
            Error = $_.Exception.Message
            Url = $Url
        }
        return $null
    }
}

function Test-WebPage {
    param(
        [string]$Name,
        [string]$Url
    )
    
    $TestResults.Total++
    Write-Host "🌐 Testing Web Page: $Name" -ForegroundColor Cyan
    
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -ErrorAction Stop
        
        if ($response.StatusCode -eq 200) {
            Write-Host "  ✅ PASS: $Name (Status: $($response.StatusCode))" -ForegroundColor Green
            $TestResults.Passed++
            $TestResults.Details += @{
                Test = $Name
                Status = "PASS"
                StatusCode = $response.StatusCode
                Url = $Url
            }
        } else {
            throw "Unexpected status code: $($response.StatusCode)"
        }
    }
    catch {
        Write-Host "  ❌ FAIL: $Name - $($_.Exception.Message)" -ForegroundColor Red
        $TestResults.Failed++
        $TestResults.Details += @{
            Test = $Name
            Status = "FAIL"
            Error = $_.Exception.Message
            Url = $Url
        }
    }
}

Write-Host "🔧 PHASE 1: Backend API Endpoints Testing" -ForegroundColor Magenta
Write-Host "================================================" -ForegroundColor Gray

# Test basic health endpoint
Test-Endpoint -Name "Server Health Check" -Url "$BaseUrl/"

# Test crops endpoint
$cropsResponse = Test-Endpoint -Name "Crops Database" -Url "$BaseUrl/crops" -ExpectedContent "items"

# Test chatbot endpoint
$chatResponse = Test-Endpoint -Name "Chatbot API" -Url "$BaseUrl/chatbot/ask" -Method "POST" -Body @{
    message = "What is rice?"
    zone_id = "Z1"
}

# Test tank status
Test-Endpoint -Name "Tank Status" -Url "$BaseUrl/tank/status?tank_id=T1"

# Test irrigation endpoints
Test-Endpoint -Name "Irrigation Start" -Url "$BaseUrl/irrigation/start" -Method "POST" -Body @{
    zone_id = "Z1"
    duration_s = 10
}

Test-Endpoint -Name "Irrigation Stop" -Url "$BaseUrl/irrigation/stop" -Method "POST" -Body @{
    zone_id = "Z1"
}

# Test recommendation endpoint
$recoResponse = Test-Endpoint -Name "Crop Recommendations" -Url "$BaseUrl/recommend" -Method "POST" -Body @{
    plant = "tomato"
    soil_type = "loamy"
    area_m2 = 100
    ph = 6.5
    moisture_pct = 30
    temperature_c = 25
    n_ppm = 50
    p_ppm = 20
    k_ppm = 40
}

# Test soil analysis
Test-Endpoint -Name "Soil Analysis" -Url "$BaseUrl/soil/analyze" -Method "POST" -Body @{
    ph = 6.5
    moisture_pct = 30
    temperature_c = 25
    ec_dS_m = 1.5
    n_ppm = 50
    p_ppm = 20
    k_ppm = 40
}

# Test alerts
Test-Endpoint -Name "Alerts System" -Url "$BaseUrl/alerts?zone_id=Z1&limit=5"

# Test dashboard summary
Test-Endpoint -Name "Dashboard Summary" -Url "$BaseUrl/dashboard/summary?zone_id=Z1&tank_id=T1&alerts_limit=5&events_limit=5"

# Test weather cache
Test-Endpoint -Name "Weather Cache" -Url "$BaseUrl/weather/cache?limit=5"

# Test edge capture
Test-Endpoint -Name "Edge Data Capture" -Url "$BaseUrl/edge/capture" -Method "POST" -Body @{
    zone_id = "Z1"
    tank_id = "T1"
    moisture_pct = 35
    temperature_c = 24
    ph = 6.8
}

Write-Host ""
Write-Host "🌐 PHASE 2: Frontend Integration Testing" -ForegroundColor Magenta
Write-Host "================================================" -ForegroundColor Gray

# Test main UI pages
Test-WebPage -Name "Main Dashboard" -Url "$BaseUrl/ui/"
Test-WebPage -Name "Crops Page" -Url "$BaseUrl/ui/crops"
Test-WebPage -Name "Chatbot Page" -Url "$BaseUrl/ui/chat"
Test-WebPage -Name "Recommend Page" -Url "$BaseUrl/ui/recommend"
Test-WebPage -Name "Soil Analysis Page" -Url "$BaseUrl/ui/soil-analysis"
Test-WebPage -Name "Live Stats Page" -Url "$BaseUrl/ui/live"
Test-WebPage -Name "Irrigation Page" -Url "$BaseUrl/ui/irrigation"
Test-WebPage -Name "Tank Page" -Url "$BaseUrl/ui/tank"
Test-WebPage -Name "Admin Page" -Url "$BaseUrl/ui/admin"
Test-WebPage -Name "Impact Graphs Page" -Url "$BaseUrl/ui/impact"

Write-Host ""
Write-Host "📊 PHASE 3: Data Validation Testing" -ForegroundColor Magenta
Write-Host "================================================" -ForegroundColor Gray

# Validate crops data
if ($cropsResponse -and $cropsResponse.items) {
    $cropCount = $cropsResponse.items.Count
    if ($cropCount -gt 0) {
        Write-Host "  ✅ PASS: Crops Database contains $cropCount crops" -ForegroundColor Green
        $TestResults.Passed++
        
        # Test specific crop data structure
        $sampleCrop = $cropsResponse.items[0]
        if ($sampleCrop.name -and $sampleCrop.id) {
            Write-Host "  ✅ PASS: Crop data structure is valid" -ForegroundColor Green
            $TestResults.Passed++
        } else {
            Write-Host "  ❌ FAIL: Crop data structure is invalid" -ForegroundColor Red
            $TestResults.Failed++
        }
    } else {
        Write-Host "  ❌ FAIL: Crops database is empty" -ForegroundColor Red
        $TestResults.Failed++
    }
    $TestResults.Total += 2
} else {
    Write-Host "  ❌ FAIL: Could not retrieve crops data" -ForegroundColor Red
    $TestResults.Failed++
    $TestResults.Total++
}

# Validate chatbot response
if ($chatResponse -and $chatResponse.answer) {
    Write-Host "  ✅ PASS: Chatbot provides intelligent responses" -ForegroundColor Green
    Write-Host "    Response: $($chatResponse.answer.Substring(0, [Math]::Min(100, $chatResponse.answer.Length)))..." -ForegroundColor Gray
    $TestResults.Passed++
} else {
    Write-Host "  ❌ FAIL: Chatbot is not responding properly" -ForegroundColor Red
    $TestResults.Failed++
}
$TestResults.Total++

# Validate recommendation system
if ($recoResponse -and $recoResponse.water_liters) {
    Write-Host "  ✅ PASS: Recommendation system provides water calculations" -ForegroundColor Green
    Write-Host "    Water needed: $($recoResponse.water_liters) liters" -ForegroundColor Gray
    $TestResults.Passed++
} else {
    Write-Host "  ❌ FAIL: Recommendation system is not working" -ForegroundColor Red
    $TestResults.Failed++
}
$TestResults.Total++

Write-Host ""
Write-Host "🔬 PHASE 4: ML Pipeline Testing" -ForegroundColor Magenta
Write-Host "================================================" -ForegroundColor Gray

# Test if ML models are available (even if disabled)
$mlModelsPath = "d:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK\agrisense_app\backend"
$modelFiles = @("water_model.keras", "fert_model.keras", "water_model.joblib", "fert_model.joblib")

foreach ($modelFile in $modelFiles) {
    $modelPath = Join-Path $mlModelsPath $modelFile
    if (Test-Path $modelPath) {
        Write-Host "  ✅ PASS: ML Model found - $modelFile" -ForegroundColor Green
        $TestResults.Passed++
    } else {
        Write-Host "  ⚠️  INFO: ML Model not found - $modelFile (may use rule-based fallback)" -ForegroundColor Yellow
    }
    $TestResults.Total++
}

# Test dataset files
$datasetFiles = @("india_crop_dataset.csv", "sikkim_crop_dataset.csv")
foreach ($datasetFile in $datasetFiles) {
    $datasetPath = Join-Path $mlModelsPath $datasetFile
    if (Test-Path $datasetPath) {
        Write-Host "  ✅ PASS: Dataset found - $datasetFile" -ForegroundColor Green
        $TestResults.Passed++
    } else {
        # Check alternate locations
        $altPath = "d:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK\$datasetFile"
        if (Test-Path $altPath) {
            Write-Host "  ✅ PASS: Dataset found at alternate location - $datasetFile" -ForegroundColor Green
            $TestResults.Passed++
        } else {
            Write-Host "  ❌ FAIL: Dataset not found - $datasetFile" -ForegroundColor Red
            $TestResults.Failed++
        }
    }
    $TestResults.Total++
}

Write-Host ""
Write-Host "📋 TEST RESULTS SUMMARY" -ForegroundColor White -BackgroundColor DarkBlue
Write-Host "================================================" -ForegroundColor Gray
Write-Host "🎯 Total Tests: $($TestResults.Total)" -ForegroundColor White
Write-Host "✅ Passed: $($TestResults.Passed)" -ForegroundColor Green
Write-Host "❌ Failed: $($TestResults.Failed)" -ForegroundColor Red
$passRate = [math]::Round(($TestResults.Passed / $TestResults.Total) * 100, 1)
Write-Host "📊 Pass Rate: $passRate%" -ForegroundColor Yellow

if ($passRate -ge 90) {
    Write-Host "🏆 EXCELLENT: Your AgriSense application is working exceptionally well!" -ForegroundColor Green
} elseif ($passRate -ge 70) {
    Write-Host "👍 GOOD: Your AgriSense application is working well with minor issues" -ForegroundColor Yellow
} else {
    Write-Host "⚠️  NEEDS ATTENTION: Several components need fixes" -ForegroundColor Red
}

Write-Host ""
Write-Host "📁 Detailed Results:" -ForegroundColor White
$TestResults.Details | ForEach-Object {
    $status = if ($_.Status -eq "PASS") { "✅" } else { "❌" }
    Write-Host "  $status $($_.Test)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "🔚 Test completed at $(Get-Date)" -ForegroundColor Gray

# Export results to JSON for further analysis
$resultsPath = "d:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK\test_results_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
$TestResults | ConvertTo-Json -Depth 10 | Out-File $resultsPath
Write-Host "📄 Detailed results saved to: $resultsPath" -ForegroundColor Cyan