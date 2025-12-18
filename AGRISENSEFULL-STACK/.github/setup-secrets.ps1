# ===================================================================
# GitHub Secrets Setup Script
# Automatically configures all required secrets for AgriSense workflows
# ===================================================================

param(
    [Parameter(Mandatory=$false)]
    [string]$RepoOwner = "ELANGKATHIR11",
    
    [Parameter(Mandatory=$false)]
    [string]$RepoName = "AGRISENSEFULL-STACK",
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun
)

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "AgriSense GitHub Secrets Setup" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if GitHub CLI is installed
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "❌ GitHub CLI (gh) is not installed." -ForegroundColor Red
    Write-Host "Install from: https://cli.github.com/" -ForegroundColor Yellow
    Write-Host "Or run: winget install --id GitHub.cli" -ForegroundColor Yellow
    exit 1
}

# Check if authenticated
gh auth status 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Not authenticated with GitHub CLI" -ForegroundColor Red
    Write-Host "Run: gh auth login" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ GitHub CLI authenticated" -ForegroundColor Green
Write-Host ""

# Function to set a secret
function Set-GitHubSecret {
    param(
        [string]$Name,
        [string]$Value,
        [string]$Description
    )
    
    if ($DryRun) {
        Write-Host "  [DRY RUN] Would set: $Name" -ForegroundColor Yellow
        return
    }
    
    try {
        # Use gh secret set command
        $Value | gh secret set $Name --repo "$RepoOwner/$RepoName"
        Write-Host "  ✅ Set: $Name" -ForegroundColor Green
    }
    catch {
        Write-Host "  ❌ Failed to set: $Name" -ForegroundColor Red
        Write-Host "     Error: $_" -ForegroundColor Red
    }
}

# Function to create environment
function New-GitHubEnvironment {
    param(
        [string]$EnvName
    )
    
    if ($DryRun) {
        Write-Host "  [DRY RUN] Would create environment: $EnvName" -ForegroundColor Yellow
        return
    }
    
    try {
        # Create environment using GitHub API
        gh api -X PUT "repos/$RepoOwner/$RepoName/environments/$EnvName"
        Write-Host "  ✅ Created environment: $EnvName" -ForegroundColor Green
    }
    catch {
        Write-Host "  ⚠️  Environment may already exist: $EnvName" -ForegroundColor Yellow
    }
}

Write-Host "📋 Step 1: Collecting Azure Information" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Azure CLI is available
if (Get-Command az -ErrorAction SilentlyContinue) {
    Write-Host "Attempting to fetch Azure information..." -ForegroundColor Yellow
    
    # Get subscription ID
    $subscriptionId = az account show --query id -o tsv 2>$null
    
    if ($subscriptionId) {
        Write-Host "  Found Azure Subscription: $subscriptionId" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Not logged in to Azure CLI. Run: az login" -ForegroundColor Yellow
        $subscriptionId = Read-Host "  Enter AZURE_SUBSCRIPTION_ID manually (or press Enter to skip)"
    }
} else {
    Write-Host "  ⚠️  Azure CLI not installed. Manual input required." -ForegroundColor Yellow
    $subscriptionId = Read-Host "  Enter AZURE_SUBSCRIPTION_ID (or press Enter to skip)"
}

Write-Host ""
Write-Host "📝 Step 2: Collecting Secret Values" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Collect Azure secrets
Write-Host "Azure Container Registry Configuration:" -ForegroundColor White
$acrName = Read-Host "  AZURE_CONTAINER_REGISTRY name (e.g., agrisenseacr)"
$acrUsername = Read-Host "  AZURE_ACR_USERNAME"
$acrPassword = Read-Host "  AZURE_ACR_PASSWORD" -AsSecureString
$acrPasswordText = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($acrPassword))

Write-Host ""
Write-Host "Azure Resource Configuration:" -ForegroundColor White
$resourceGroup = Read-Host "  AZURE_RESOURCE_GROUP (e.g., agrisense-rg)"
$backendAppName = Read-Host "  AZURE_BACKEND_APP_NAME (App Service name)"
$staticWebAppToken = Read-Host "  AZURE_STATIC_WEB_APPS_API_TOKEN" -AsSecureString
$staticWebAppTokenText = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($staticWebAppToken))

Write-Host ""
Write-Host "Azure Credentials:" -ForegroundColor White
Write-Host "  To generate AZURE_CREDENTIALS, run:" -ForegroundColor Yellow
Write-Host "  az ad sp create-for-rbac --name 'agrisense-sp' --role contributor --scopes /subscriptions/$subscriptionId --sdk-auth" -ForegroundColor Yellow
$azureCredentials = Read-Host "  Paste AZURE_CREDENTIALS JSON"

Write-Host ""
Write-Host "Frontend Configuration:" -ForegroundColor White
$viteApiUrl = Read-Host "  VITE_API_URL (e.g., https://$backendAppName.azurewebsites.net)"
$frontendUrl = Read-Host "  AZURE_FRONTEND_URL (e.g., https://agrisense.azurestaticapps.net)"

Write-Host ""
Write-Host "SSH Configuration (for CD pipeline):" -ForegroundColor White
$stagingHost = Read-Host "  STAGING_HOST (or press Enter to skip)"
if ($stagingHost) {
    $stagingUser = Read-Host "  STAGING_USER"
    $stagingKey = Read-Host "  STAGING_SSH_KEY (paste private key, end with empty line)"
    $prodHost = Read-Host "  PROD_HOST"
    $prodUser = Read-Host "  PROD_USER"
    $prodKey = Read-Host "  PROD_SSH_KEY (paste private key)"
}

Write-Host ""
Write-Host "Optional - Slack Notifications:" -ForegroundColor White
$slackWebhook = Read-Host "  SLACK_WEBHOOK_URL (or press Enter to skip)"

Write-Host ""
Write-Host "🚀 Step 3: Setting GitHub Secrets" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Set Azure secrets
Set-GitHubSecret "AZURE_CONTAINER_REGISTRY" $acrName "Azure Container Registry name"
Set-GitHubSecret "AZURE_RESOURCE_GROUP" $resourceGroup "Azure resource group"
Set-GitHubSecret "AZURE_ACR_USERNAME" $acrUsername "ACR username"
Set-GitHubSecret "AZURE_ACR_PASSWORD" $acrPasswordText "ACR password"
Set-GitHubSecret "AZURE_SUBSCRIPTION_ID" $subscriptionId "Azure subscription ID"
Set-GitHubSecret "AZURE_CREDENTIALS" $azureCredentials "Azure service principal"
Set-GitHubSecret "AZURE_BACKEND_APP_NAME" $backendAppName "Backend App Service name"
Set-GitHubSecret "AZURE_STATIC_WEB_APPS_API_TOKEN" $staticWebAppTokenText "Static Web App token"
Set-GitHubSecret "VITE_API_URL" $viteApiUrl "Backend API URL"
Set-GitHubSecret "AZURE_FRONTEND_URL" $frontendUrl "Frontend URL"

# Set SSH secrets if provided
if ($stagingHost) {
    Set-GitHubSecret "STAGING_HOST" $stagingHost "Staging server host"
    Set-GitHubSecret "STAGING_USER" $stagingUser "Staging SSH user"
    Set-GitHubSecret "STAGING_SSH_KEY" $stagingKey "Staging SSH key"
    Set-GitHubSecret "PROD_HOST" $prodHost "Production server host"
    Set-GitHubSecret "PROD_USER" $prodUser "Production SSH user"
    Set-GitHubSecret "PROD_SSH_KEY" $prodKey "Production SSH key"
}

# Set Slack webhook if provided
if ($slackWebhook) {
    Set-GitHubSecret "SLACK_WEBHOOK_URL" $slackWebhook "Slack webhook URL"
}

Write-Host ""
Write-Host "🌍 Step 4: Creating Environments" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

New-GitHubEnvironment "dev"
New-GitHubEnvironment "staging"
New-GitHubEnvironment "production"

Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""

if ($DryRun) {
    Write-Host "This was a DRY RUN. No changes were made." -ForegroundColor Yellow
    Write-Host "Run without -DryRun flag to apply changes." -ForegroundColor Yellow
} else {
    Write-Host "All secrets have been configured." -ForegroundColor Green
    Write-Host "All environments have been created." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Verify secrets: gh secret list --repo $RepoOwner/$RepoName" -ForegroundColor White
    Write-Host "  2. Check workflows: Visit https://github.com/$RepoOwner/$RepoName/actions" -ForegroundColor White
    Write-Host "  3. Test deployment: Manually trigger a workflow" -ForegroundColor White
}

Write-Host ""
