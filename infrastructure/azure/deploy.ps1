# ===================================================================
# Azure Deployment PowerShell Script
# AgriSense Full-Stack Deployment Automation
# ===================================================================

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('dev', 'staging', 'prod')]
    [string]$Environment,
    
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroup,
    
    [Parameter(Mandatory=$false)]
    [string]$Location = 'eastus',
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipInfrastructure,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipDocker,
    
    [Parameter(Mandatory=$false)]
    [switch]$Verbose
)

$ErrorActionPreference = 'Stop'
$VerbosePreference = if ($Verbose) { 'Continue' } else { 'SilentlyContinue' }

# ===================================================================
# Functions
# ===================================================================

function Write-Header {
    param([string]$Message)
    Write-Host "`n$('=' * 70)" -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host "$('=' * 70)`n" -ForegroundColor Cyan
}

function Write-Step {
    param([string]$Message)
    Write-Host "▶ $Message" -ForegroundColor Yellow
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

# ===================================================================
# Main Script
# ===================================================================

Write-Header "AgriSense Azure Deployment - $Environment Environment"

# Verify prerequisites
Write-Step "Checking prerequisites..."

# Check Azure CLI
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Error "Azure CLI not found. Please install: https://aka.ms/installazurecliwindows"
    exit 1
}
Write-Success "Azure CLI found"

# Check Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker not found. Please install: https://docs.docker.com/get-docker/"
    exit 1
}
Write-Success "Docker found"

# Check login status
Write-Step "Checking Azure login status..."
$account = az account show 2>&1 | ConvertFrom-Json
if (-not $account) {
    Write-Error "Not logged in to Azure. Please run: az login"
    exit 1
}
Write-Success "Logged in as: $($account.user.name)"
Write-Success "Subscription: $($account.name)"

# Create or verify resource group
Write-Step "Verifying resource group: $ResourceGroup"
$rgExists = az group exists --name $ResourceGroup
if ($rgExists -eq 'false') {
    Write-Step "Creating resource group..."
    az group create --name $ResourceGroup --location $Location | Out-Null
    Write-Success "Resource group created"
} else {
    Write-Success "Resource group exists"
}

# Deploy infrastructure
if (-not $SkipInfrastructure) {
    Write-Header "Deploying Infrastructure (Bicep)"
    
    $templateFile = "infrastructure/azure/main.bicep"
    $parametersFile = "infrastructure/azure/parameters.$Environment.json"
    
    if (-not (Test-Path $templateFile)) {
        Write-Error "Template file not found: $templateFile"
        exit 1
    }
    
    if (-not (Test-Path $parametersFile)) {
        Write-Error "Parameters file not found: $parametersFile"
        exit 1
    }
    
    Write-Step "Starting deployment..."
    $deploymentName = "agrisense-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    
    $deployment = az deployment group create `
        --resource-group $ResourceGroup `
        --template-file $templateFile `
        --parameters $parametersFile `
        --name $deploymentName `
        --output json | ConvertFrom-Json
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Infrastructure deployment failed"
        exit 1
    }
    
    Write-Success "Infrastructure deployed successfully"
    
    # Extract outputs
    $outputs = $deployment.properties.outputs
    $acrName = $outputs.containerRegistryName.value
    $acrServer = $outputs.containerRegistryLoginServer.value
    $backendUrl = $outputs.backendAppUrl.value
    $frontendUrl = $outputs.frontendAppUrl.value
    
    Write-Host "`nDeployment Outputs:" -ForegroundColor Cyan
    Write-Host "  Container Registry: $acrName" -ForegroundColor White
    Write-Host "  ACR Server: $acrServer" -ForegroundColor White
    Write-Host "  Backend URL: $backendUrl" -ForegroundColor White
    Write-Host "  Frontend URL: $frontendUrl" -ForegroundColor White
} else {
    Write-Header "Skipping Infrastructure Deployment"
    
    # Get existing ACR name
    Write-Step "Looking for existing Container Registry..."
    $registries = az acr list --resource-group $ResourceGroup --output json | ConvertFrom-Json
    if ($registries.Count -eq 0) {
        Write-Error "No Container Registry found in resource group"
        exit 1
    }
    $acrName = $registries[0].name
    $acrServer = $registries[0].loginServer
    Write-Success "Found ACR: $acrName"
}

# Build and push Docker images
if (-not $SkipDocker) {
    Write-Header "Building and Pushing Docker Images"
    
    # Login to ACR
    Write-Step "Logging in to Azure Container Registry..."
    az acr login --name $acrName
    if ($LASTEXITCODE -ne 0) {
        Write-Error "ACR login failed"
        exit 1
    }
    Write-Success "Logged in to ACR"
    
    # Build backend
    Write-Step "Building backend Docker image..."
    $backendImage = "$acrServer/agrisense/backend:latest"
    $backendImageEnv = "$acrServer/agrisense/backend:$Environment"
    
    docker build -t $backendImage -t $backendImageEnv -f Dockerfile.azure .
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Backend image build failed"
        exit 1
    }
    Write-Success "Backend image built"
    
    # Push backend
    Write-Step "Pushing backend image..."
    docker push $backendImage
    docker push $backendImageEnv
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Backend image push failed"
        exit 1
    }
    Write-Success "Backend image pushed"
    
    # Build frontend
    Write-Step "Building frontend Docker image..."
    $frontendImage = "$acrServer/agrisense/frontend:latest"
    $frontendImageEnv = "$acrServer/agrisense/frontend:$Environment"
    
    docker build -t $frontendImage -t $frontendImageEnv -f Dockerfile.frontend.azure .
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Frontend image build failed"
        exit 1
    }
    Write-Success "Frontend image built"
    
    # Push frontend
    Write-Step "Pushing frontend image..."
    docker push $frontendImage
    docker push $frontendImageEnv
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Frontend image push failed"
        exit 1
    }
    Write-Success "Frontend image pushed"
} else {
    Write-Header "Skipping Docker Build"
}

# Deploy backend to App Service
Write-Header "Deploying Backend Application"

Write-Step "Finding backend App Service..."
$webapps = az webapp list --resource-group $ResourceGroup --output json | ConvertFrom-Json
$backendApp = $webapps | Where-Object { $_.name -like "*backend*" }

if (-not $backendApp) {
    Write-Error "Backend App Service not found in resource group"
    exit 1
}

$backendAppName = $backendApp.name
Write-Success "Found App Service: $backendAppName"

Write-Step "Updating App Service container..."
az webapp config container set `
    --name $backendAppName `
    --resource-group $ResourceGroup `
    --docker-custom-image-name "$acrServer/agrisense/backend:$Environment" `
    --docker-registry-server-url "https://$acrServer" | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to update App Service container"
    exit 1
}
Write-Success "Container configuration updated"

Write-Step "Restarting App Service..."
az webapp restart --name $backendAppName --resource-group $ResourceGroup | Out-Null
Write-Success "App Service restarted"

# Wait for health check
Write-Step "Waiting for backend to be healthy (max 2 minutes)..."
$backendUrl = "https://$backendAppName.azurewebsites.net/health"
$maxAttempts = 24
$attempt = 0
$healthy = $false

while ($attempt -lt $maxAttempts -and -not $healthy) {
    Start-Sleep -Seconds 5
    try {
        $response = Invoke-WebRequest -Uri $backendUrl -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            $healthy = $true
        }
    } catch {
        # Continue waiting
    }
    $attempt++
    Write-Host "." -NoNewline
}

Write-Host ""
if ($healthy) {
    Write-Success "Backend is healthy!"
} else {
    Write-Error "Backend health check timed out. Check logs: az webapp log tail --name $backendAppName --resource-group $ResourceGroup"
}

# Summary
Write-Header "Deployment Complete!"

Write-Host "`nDeployment Summary:" -ForegroundColor Cyan
Write-Host "  Environment: $Environment" -ForegroundColor White
Write-Host "  Resource Group: $ResourceGroup" -ForegroundColor White
Write-Host "  Backend URL: https://$backendAppName.azurewebsites.net" -ForegroundColor White
Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "  1. Verify backend: https://$backendAppName.azurewebsites.net/health" -ForegroundColor White
Write-Host "  2. Check logs: az webapp log tail --name $backendAppName --resource-group $ResourceGroup" -ForegroundColor White
Write-Host "  3. Deploy frontend via Static Web App (see DEPLOYMENT_GUIDE.md)" -ForegroundColor White
Write-Host ""
