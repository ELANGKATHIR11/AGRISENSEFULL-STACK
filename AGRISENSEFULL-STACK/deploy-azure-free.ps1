# ===================================================================
# AgriSense Azure Free Tier Quick Start
# Run this script to deploy your project to Azure
# ===================================================================

Write-Host @"

╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🌾 AgriSense - Azure Free Tier Deployment                 ║
║                                                               ║
║   Smart Agriculture Platform                                 ║
║   Estimated Cost: ~`$6/month                                  ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Green

Write-Host "This script will deploy AgriSense to your Azure free subscription.`n" -ForegroundColor Cyan

# Step 1: Login to Azure
Write-Host "Step 1: Logging into Azure..." -ForegroundColor Yellow
Write-Host "A browser window will open for authentication.`n" -ForegroundColor White

az login

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Azure login failed. Please check your credentials." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Successfully logged into Azure!`n" -ForegroundColor Green

# Show current subscription
$subscription = az account show --query "{Name:name, ID:id}" -o json | ConvertFrom-Json
Write-Host "📋 Current Subscription:" -ForegroundColor Cyan
Write-Host "   Name: $($subscription.Name)" -ForegroundColor White
Write-Host "   ID: $($subscription.ID)`n" -ForegroundColor White

# Step 2: Confirm deployment
Write-Host "Step 2: Deployment Configuration" -ForegroundColor Yellow
Write-Host "   Resource Group: agrisense-free-rg" -ForegroundColor White
Write-Host "   Location: East US" -ForegroundColor White
Write-Host "   Tier: Free (F1 App Service + Free Cosmos DB)" -ForegroundColor White
Write-Host "   Estimated Cost: ~`$6/month" -ForegroundColor White
Write-Host "   Free Trial Credit: `$200 (lasts ~33 months)`n" -ForegroundColor Green

$confirm = Read-Host "Proceed with deployment? (yes/no)"

if ($confirm -ne "yes") {
    Write-Host "Deployment cancelled." -ForegroundColor Yellow
    exit 0
}

# Step 3: Run deployment
Write-Host "`nStep 3: Starting Deployment..." -ForegroundColor Yellow
Write-Host "This will take approximately 15-20 minutes.`n" -ForegroundColor White

$scriptPath = Join-Path $PSScriptRoot "infrastructure\azure\deploy-free.ps1"

if (-not (Test-Path $scriptPath)) {
    Write-Host "❌ Deployment script not found: $scriptPath" -ForegroundColor Red
    Write-Host "Make sure you're running this from the project root directory.`n" -ForegroundColor Yellow
    exit 1
}

# Execute deployment
& $scriptPath

Write-Host "`n✅ Deployment process completed!" -ForegroundColor Green
Write-Host "Check the output above for your application URLs.`n" -ForegroundColor Cyan
