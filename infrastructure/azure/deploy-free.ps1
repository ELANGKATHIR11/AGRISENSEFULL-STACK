# ===================================================================
# AgriSense Free Tier Azure Deployment Script
# Optimized for Azure Free Subscription
# ===================================================================

param(
    [string]$ResourceGroup = "agrisense-free-rg",
    [string]$Location = "eastus",
    [string]$ProjectName = "agrisense"
)

$ErrorActionPreference = "Stop"

# ===================================================================
# Helper Functions
# ===================================================================

function Write-Header {
    param([string]$Message)
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host " $Message" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
}

function Write-Step {
    param([string]$Message)
    Write-Host "➤ $Message" -ForegroundColor Yellow
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Blue
}

# ===================================================================
# Step 1: Verify Prerequisites
# ===================================================================

Write-Header "Step 1/7: Verifying Prerequisites"

# Check Azure CLI
Write-Step "Checking Azure CLI installation..."
try {
    $azVersion = az --version 2>&1 | Select-String "azure-cli" | Select-Object -First 1
    Write-Success "Azure CLI found: $azVersion"
} catch {
    Write-Error "Azure CLI not found. Please install from: https://aka.ms/installazurecli"
    exit 1
}

# Check Docker (optional but recommended)
Write-Step "Checking Docker installation..."
try {
    $dockerVersion = docker --version 2>&1
    Write-Success "Docker found: $dockerVersion"
    $hasDocker = $true
} catch {
    Write-Info "Docker not found. Will skip container build (can deploy later)."
    $hasDocker = $false
}

# ===================================================================
# Step 2: Azure Login
# ===================================================================

Write-Header "Step 2/7: Azure Login"

Write-Step "Checking Azure login status..."
$loginStatus = az account show 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Info "Not logged in. Opening browser for authentication..."
    az login
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Azure login failed"
        exit 1
    }
} else {
    Write-Success "Already logged in to Azure"
}

# Show current subscription
$subscription = az account show --query "{Name:name, ID:id, State:state}" -o json | ConvertFrom-Json
Write-Success "Using subscription: $($subscription.Name) ($($subscription.ID))"

# Confirm subscription
Write-Host "`nℹ️  This deployment will use your Azure subscription:" -ForegroundColor Yellow
Write-Host "   Name: $($subscription.Name)" -ForegroundColor White
Write-Host "   ID: $($subscription.ID)" -ForegroundColor White
Write-Host "`n⚠️  Estimated monthly cost: ~`$6 (mostly Container Registry)" -ForegroundColor Yellow
Write-Host "   Free trial credit: `$200 (lasts ~33 months)" -ForegroundColor Green

$confirm = Read-Host "`nContinue with deployment? (yes/no)"
if ($confirm -ne "yes") {
    Write-Info "Deployment cancelled by user"
    exit 0
}

# ===================================================================
# Step 3: Register Resource Providers
# ===================================================================

Write-Header "Step 3/7: Registering Azure Resource Providers"

$providers = @(
    "Microsoft.Web",
    "Microsoft.DocumentDB",
    "Microsoft.ContainerRegistry",
    "Microsoft.Storage",
    "Microsoft.Insights",
    "Microsoft.KeyVault"
)

foreach ($provider in $providers) {
    Write-Step "Registering $provider..."
    $state = az provider show --namespace $provider --query "registrationState" -o tsv 2>&1
    
    if ($state -eq "Registered") {
        Write-Success "$provider already registered"
    } else {
        az provider register --namespace $provider --wait
        Write-Success "$provider registered successfully"
    }
}

# ===================================================================
# Step 4: Create Resource Group
# ===================================================================

Write-Header "Step 4/7: Creating Resource Group"

Write-Step "Creating resource group: $ResourceGroup in $Location..."
$rgExists = az group exists --name $ResourceGroup

if ($rgExists -eq "true") {
    Write-Info "Resource group already exists"
} else {
    az group create --name $ResourceGroup --location $Location --tags "Project=AgriSense" "Environment=free" "ManagedBy=PowerShell"
    Write-Success "Resource group created: $ResourceGroup"
}

# ===================================================================
# Step 5: Deploy Infrastructure
# ===================================================================

Write-Header "Step 5/7: Deploying Azure Infrastructure"

Write-Step "Deploying Bicep template with free tier configuration..."
Write-Info "This may take 10-15 minutes. Deploying:"
Write-Host "   • App Service (F1 Free tier)" -ForegroundColor White
Write-Host "   • Cosmos DB (Free tier - 1000 RU/s)" -ForegroundColor White
Write-Host "   • Container Registry (Basic - `$5/month)" -ForegroundColor White
Write-Host "   • Storage Account (5GB free)" -ForegroundColor White
Write-Host "   • Static Web App (Free tier)" -ForegroundColor White
Write-Host "   • Application Insights (5GB free)" -ForegroundColor White
Write-Host "   • Key Vault (~`$0.50/month)" -ForegroundColor White

$deploymentName = "agrisense-free-deployment-$(Get-Date -Format 'yyyyMMddHHmmss')"

$templateFile = Join-Path $PSScriptRoot "main.bicep"
$parametersFile = Join-Path $PSScriptRoot "parameters.free.json"

if (-not (Test-Path $templateFile)) {
    Write-Error "Template file not found: $templateFile"
    exit 1
}

if (-not (Test-Path $parametersFile)) {
    Write-Error "Parameters file not found: $parametersFile"
    Write-Info "Expected file: $parametersFile"
    exit 1
}

try {
    $deployment = az deployment group create `
        --name $deploymentName `
        --resource-group $ResourceGroup `
        --template-file $templateFile `
        --parameters $parametersFile `
        --parameters projectName=$ProjectName `
        --output json | ConvertFrom-Json
    
    Write-Success "Infrastructure deployment completed"
    
    # Extract outputs
    $outputs = $deployment.properties.outputs
    $backendUrl = $outputs.backendUrl.value
    $frontendUrl = $outputs.frontendUrl.value
    $acrName = $outputs.containerRegistryName.value
    $cosmosEndpoint = $outputs.cosmosDbEndpoint.value
    
    Write-Success "Backend App URL: $backendUrl"
    Write-Success "Frontend App URL: $frontendUrl"
    Write-Success "Container Registry: $acrName"
    Write-Success "Cosmos DB Endpoint: $cosmosEndpoint"
    
} catch {
    Write-Error "Infrastructure deployment failed: $_"
    Write-Info "Check Azure Portal for deployment details"
    exit 1
}

# ===================================================================
# Step 6: Configure Backend Environment
# ===================================================================

Write-Header "Step 6/7: Configuring Backend Environment"

Write-Step "Setting backend application settings for free tier..."

# Get backend app name from deployment
$backendAppName = $outputs.backendAppServiceName.value

# Configure app settings optimized for free tier
$appSettings = @(
    "AGRISENSE_DISABLE_ML=1",  # Disable ML to reduce CPU usage
    "WORKERS=1",                # Single worker for F1 tier
    "LOG_LEVEL=WARNING",        # Reduce log volume
    "ENABLE_CACHE=true",        # Enable caching
    "CACHE_TTL=3600",          # 1-hour cache
    "COSMOS_ENDPOINT=$cosmosEndpoint"
)

az webapp config appsettings set `
    --name $backendAppName `
    --resource-group $ResourceGroup `
    --settings $appSettings `
    --output none

Write-Success "Backend environment configured for free tier"

# ===================================================================
# Step 7: Docker Build & Push (Optional)
# ===================================================================

Write-Header "Step 7/7: Docker Images"

if ($hasDocker) {
    Write-Step "Would you like to build and deploy Docker containers now? (yes/no)"
    Write-Info "This requires Docker Desktop and will take 10-15 minutes"
    Write-Info "You can skip this and deploy later using GitHub Actions"
    
    $buildDocker = Read-Host "Build Docker images now?"
    
    if ($buildDocker -eq "yes") {
        Write-Step "Logging into Azure Container Registry..."
        az acr login --name $acrName
        
        Write-Step "Building backend Docker image..."
        $backendImage = "$acrName.azurecr.io/agrisense/backend:latest"
        docker build -f Dockerfile.azure -t $backendImage --build-arg PYTHON_VERSION=3.12.10 .
        
        Write-Step "Pushing backend image..."
        docker push $backendImage
        
        Write-Step "Building frontend Docker image..."
        $frontendImage = "$acrName.azurecr.io/agrisense/frontend:latest"
        $apiUrl = "https://$backendAppName.azurewebsites.net"
        docker build -f Dockerfile.frontend.azure -t $frontendImage --build-arg VITE_API_URL=$apiUrl .
        
        Write-Step "Pushing frontend image..."
        docker push $frontendImage
        
        Write-Success "Docker images built and pushed successfully"
        
        # Update App Service to use new container
        Write-Step "Updating App Service container..."
        az webapp config container set `
            --name $backendAppName `
            --resource-group $ResourceGroup `
            --docker-custom-image-name $backendImage `
            --docker-registry-server-url "https://$acrName.azurecr.io"
        
        az webapp restart --name $backendAppName --resource-group $ResourceGroup
        
        Write-Success "Backend container deployed and restarted"
    } else {
        Write-Info "Skipping Docker build. Deploy later using:"
        Write-Host "   1. GitHub Actions (automated)" -ForegroundColor White
        Write-Host "   2. Manual: docker build + docker push + az webapp config" -ForegroundColor White
    }
} else {
    Write-Info "Docker not available. Deploy containers using:"
    Write-Host "   • Install Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor White
    Write-Host "   • Or use GitHub Actions for automated deployment" -ForegroundColor White
}

# ===================================================================
# Deployment Summary
# ===================================================================

Write-Header "Deployment Complete! 🎉"

Write-Host "Your AgriSense application has been deployed to Azure (Free Tier)" -ForegroundColor Green
Write-Host ""
Write-Host "📦 Resources Created:" -ForegroundColor Cyan
Write-Host "   Resource Group: $ResourceGroup" -ForegroundColor White
Write-Host "   Location: $Location" -ForegroundColor White
Write-Host ""
Write-Host "🌐 URLs:" -ForegroundColor Cyan
Write-Host "   Backend API: $backendUrl" -ForegroundColor White
Write-Host "   Frontend App: $frontendUrl" -ForegroundColor White
Write-Host ""
Write-Host "💰 Estimated Monthly Cost: ~`$6" -ForegroundColor Yellow
Write-Host "   • App Service F1: `$0 (free)" -ForegroundColor White
Write-Host "   • Cosmos DB: `$0 (free tier)" -ForegroundColor White
Write-Host "   • Storage: `$0.23" -ForegroundColor White
Write-Host "   • Container Registry: `$5" -ForegroundColor White
Write-Host "   • Other: ~`$1" -ForegroundColor White
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Wait 2-3 minutes for services to start" -ForegroundColor White
Write-Host "   2. Test backend: curl $backendUrl/health" -ForegroundColor White
Write-Host "   3. Test frontend: Open $frontendUrl in browser" -ForegroundColor White
Write-Host "   4. Configure GitHub Actions for automatic deployments" -ForegroundColor White
Write-Host "   5. Monitor costs: Azure Portal > Cost Management" -ForegroundColor White
Write-Host ""
Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "   • Free Tier Guide: AZURE_FREE_TIER_DEPLOYMENT.md" -ForegroundColor White
Write-Host "   • Full Deployment Guide: DEPLOYMENT_GUIDE.md" -ForegroundColor White
Write-Host "   • Troubleshooting: README.AZURE.md" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  Free Tier Limitations:" -ForegroundColor Yellow
Write-Host "   • F1 App Service: 60 CPU minutes/day, sleeps after 20min inactivity" -ForegroundColor White
Write-Host "   • First request after sleep: 30-60 seconds (cold start)" -ForegroundColor White
Write-Host "   • ML models disabled (set AGRISENSE_DISABLE_ML=1)" -ForegroundColor White
Write-Host "   • Upgrade to B1 (`$13/month) for always-on and no limits" -ForegroundColor White
Write-Host ""
Write-Host "🔍 Monitor Deployment:" -ForegroundColor Cyan
Write-Host "   az webapp log tail --name $backendAppName --resource-group $ResourceGroup" -ForegroundColor White
Write-Host ""
Write-Host "Thank you for using AgriSense! 🌾" -ForegroundColor Green
