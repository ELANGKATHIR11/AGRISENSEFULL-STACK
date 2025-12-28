# GitHub Secrets Setup Guide

This guide explains how to configure the required GitHub Secrets to eliminate the 20 workflow validation warnings.

## Current Status
- ✅ Workflow syntax: Valid
- ⚠️ Secrets: Not configured (20 warnings) - **Use automated script below**
- ⚠️ Environments: Not created (3 warnings) - **Use automated script below**

## 🚀 FASTEST WAY: Automated Setup Script

We've created an automated PowerShell script that sets up all secrets and environments for you!

### Prerequisites
```powershell
# Install GitHub CLI if not already installed
winget install --id GitHub.cli

# Authenticate with GitHub
gh auth login

# Login to Azure (if using Azure)
az login
```

### Run the Setup Script
```powershell
# Navigate to the .github directory
cd "D:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK\.github"

# Run the setup script (interactive prompts)
.\setup-secrets.ps1

# Or for a specific repository
.\setup-secrets.ps1 -RepoOwner "ELANGKATHIR11" -RepoName "AGRISENSEFULL-STACK"

# Dry run to see what would be changed
.\setup-secrets.ps1 -DryRun
```

The script will:
1. ✅ Automatically fetch Azure configuration (if logged in)
2. ✅ Prompt for any missing values
3. ✅ Set all 17 required secrets
4. ✅ Create all 3 environments (dev, staging, production)
5. ✅ Verify configuration

**After running this script, all 20 warnings will be resolved!**

---

## Alternative: Manual Setup

## Required GitHub Secrets

### Azure Deployment Secrets (azure-deploy.yml)

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `AZURE_CONTAINER_REGISTRY` | Azure Container Registry name | From Azure Portal > Container registries |
| `AZURE_RESOURCE_GROUP` | Azure resource group name | From Azure Portal > Resource groups |
| `AZURE_ACR_USERNAME` | ACR admin username | Azure Portal > ACR > Access keys |
| `AZURE_ACR_PASSWORD` | ACR admin password | Azure Portal > ACR > Access keys |
| `AZURE_CREDENTIALS` | Service principal JSON | `az ad sp create-for-rbac --name "agrisense-sp" --role contributor --scopes /subscriptions/{subscription-id}/resourceGroups/{resource-group} --sdk-auth` |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID | `az account show --query id -o tsv` |
| `AZURE_BACKEND_APP_NAME` | Backend App Service name | From Azure Portal > App Services |
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | Static Web App deployment token | Azure Portal > Static Web Apps > Deployment token |
| `AZURE_FRONTEND_URL` | Frontend URL | From Azure Portal > Static Web Apps > URL |
| `VITE_API_URL` | Backend API URL for frontend | `https://{backend-app-name}.azurewebsites.net` |

### CD Pipeline Secrets (cd.yml)

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `STAGING_HOST` | Staging server hostname or IP | Your staging server address |
| `STAGING_USER` | SSH username for staging | Server admin username |
| `STAGING_SSH_KEY` | SSH private key for staging | Generate with `ssh-keygen` |
| `PROD_HOST` | Production server hostname or IP | Your production server address |
| `PROD_USER` | SSH username for production | Server admin username |
| `PROD_SSH_KEY` | SSH private key for production | Generate with `ssh-keygen` |
| `SLACK_WEBHOOK_URL` | Slack webhook for notifications (optional) | Slack > Incoming Webhooks |

## How to Add Secrets

### Step 1: Navigate to Repository Settings
1. Go to your GitHub repository
2. Click **Settings** tab
3. Click **Secrets and variables** > **Actions**

### Step 2: Add Each Secret
1. Click **New repository secret**
2. Enter the secret name (exactly as shown above)
3. Paste the secret value
4. Click **Add secret**

### Step 3: Create Environments (Optional but Recommended)
1. Go to **Settings** > **Environments**
2. Click **New environment**
3. Create environments named:
   - `dev`
   - `staging`
   - `production`
4. For each environment, you can add:
   - Required reviewers
   - Wait timers
   - Deployment branches

## Quick Setup Script (PowerShell)

```powershell
# Azure Login
az login

# Get Azure subscription ID
$subId = az account show --query id -o tsv
Write-Host "AZURE_SUBSCRIPTION_ID: $subId"

# Create service principal
$spJson = az ad sp create-for-rbac --name "agrisense-sp" --role contributor --scopes "/subscriptions/$subId" --sdk-auth
Write-Host "AZURE_CREDENTIALS: $spJson"

# Get ACR details (replace with your ACR name)
$acrName = "agrisenseacr"
$acrUsername = az acr credential show --name $acrName --query username -o tsv
$acrPassword = az acr credential show --name $acrName --query "passwords[0].value" -o tsv
Write-Host "AZURE_ACR_USERNAME: $acrUsername"
Write-Host "AZURE_ACR_PASSWORD: $acrPassword"
```

## Verifying Configuration

After adding secrets, the workflow validation warnings will disappear. You can verify by:

1. **Check Problems Panel**: The 20 warnings should be reduced to 0
2. **Run Workflow**: Go to **Actions** tab and manually trigger a workflow
3. **Review Logs**: Check if secrets are being accessed correctly

## Security Best Practices

- ✅ **Rotate secrets** every 90 days
- ✅ **Use least privilege** - only grant necessary permissions
- ✅ **Enable secret scanning** in repository settings
- ✅ **Use environment protection** for production deployments
- ✅ **Review access logs** regularly
- ❌ **Never commit secrets** to repository
- ❌ **Never log secrets** in workflow output

## Troubleshooting

### "Context access might be invalid"
This warning appears when secrets are referenced but not configured. Add the secret to resolve.

### "Value 'staging' is not valid"
Create the environment in Settings > Environments to resolve.

### Workflow fails with "Secret not found"
Ensure the secret name matches exactly (case-sensitive) and is added at the repository level, not organization level.

## Next Steps

After configuring secrets:
1. ✅ Commit and push your workflow changes
2. ✅ Verify warnings are resolved
3. ✅ Test workflows manually via Actions tab
4. ✅ Set up branch protection rules
5. ✅ Configure status checks for pull requests
