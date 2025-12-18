# ===================================================================
# GitHub Secrets Configuration Guide for Azure Deployment
# ===================================================================

This document lists all GitHub Secrets required for the Azure deployment pipeline.

## 🔐 Required GitHub Secrets

Navigate to: Repository Settings → Secrets and variables → Actions → New repository secret

### Azure Authentication

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `AZURE_CREDENTIALS` | Service Principal JSON for Azure login | See "Creating Service Principal" section below |
| `AZURE_SUBSCRIPTION_ID` | Azure Subscription ID | Azure Portal → Subscriptions |
| `AZURE_TENANT_ID` | Azure Active Directory Tenant ID | Azure Portal → Azure Active Directory → Properties |

### Azure Container Registry

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `AZURE_CONTAINER_REGISTRY` | ACR name (without .azurecr.io) | From Bicep deployment output |
| `AZURE_ACR_USERNAME` | ACR admin username | Azure Portal → Container Registry → Access keys |
| `AZURE_ACR_PASSWORD` | ACR admin password | Azure Portal → Container Registry → Access keys |

### Resource Group

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `AZURE_RESOURCE_GROUP` | Resource group name for deployment | Created during initial setup |

### App Services

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `AZURE_BACKEND_APP_NAME` | Backend App Service name | From Bicep deployment output |
| `AZURE_FRONTEND_URL` | Frontend Static Web App URL | From Bicep deployment output |
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | Static Web App deployment token | Azure Portal → Static Web App → Manage deployment token |

### Application Configuration

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `VITE_API_URL` | Backend API URL for frontend | `https://<backend-app-name>.azurewebsites.net` |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | Generate with: `openssl rand -hex 32` |
| `AGRISENSE_ADMIN_TOKEN` | Admin API authentication token | Generate with: `openssl rand -hex 32` |

### Database (Cosmos DB)

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `COSMOS_DB_ENDPOINT` | Cosmos DB endpoint URL | From Bicep deployment output |
| `COSMOS_DB_KEY` | Cosmos DB primary key | Azure Portal → Cosmos DB → Keys |

### Storage Account

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `AZURE_STORAGE_CONNECTION_STRING` | Storage account connection string | Azure Portal → Storage Account → Access keys |

### Application Insights

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | App Insights connection string | From Bicep deployment output |

---

## 🔧 Creating Azure Service Principal

The `AZURE_CREDENTIALS` secret requires a Service Principal with Contributor role:

### Step 1: Create Service Principal via Azure CLI

```bash
az ad sp create-for-rbac \
  --name "agrisense-github-actions" \
  --role contributor \
  --scopes /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/<RESOURCE_GROUP> \
  --sdk-auth
```

### Step 2: Copy the JSON Output

The command will output JSON like this:

```json
{
  "clientId": "xxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx",
  "clientSecret": "xxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx",
  "subscriptionId": "xxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx",
  "tenantId": "xxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

### Step 3: Add to GitHub Secrets

Copy the entire JSON and add it as the `AZURE_CREDENTIALS` secret in GitHub.

---

## 🚀 Deployment Environments

Configure GitHub Environments for approval workflows:

1. **Repository Settings** → **Environments** → **New environment**

2. Create three environments:
   - `dev` - Auto-deploy on push to develop branch
   - `staging` - Require approval, deploy on push to staging branch
   - `prod` - Require approval, deploy on push to main branch

3. For each environment, configure:
   - **Environment secrets** (override repository secrets if needed)
   - **Deployment branches** (restrict which branches can deploy)
   - **Required reviewers** (for staging and prod)

---

## 🔄 Quick Setup Script

Use this PowerShell script to set up all required secrets:

```powershell
# Set variables
$SUBSCRIPTION_ID = "your-subscription-id"
$RESOURCE_GROUP = "agrisense-dev-rg"
$LOCATION = "eastus"

# Create Service Principal
$SP_OUTPUT = az ad sp create-for-rbac `
  --name "agrisense-github-actions" `
  --role contributor `
  --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP" `
  --sdk-auth

Write-Host "✅ Service Principal created. Add this to AZURE_CREDENTIALS secret:"
Write-Host $SP_OUTPUT

# Generate secrets
$JWT_SECRET = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
$ADMIN_TOKEN = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})

Write-Host "`n✅ Generated JWT_SECRET_KEY: $JWT_SECRET"
Write-Host "✅ Generated AGRISENSE_ADMIN_TOKEN: $ADMIN_TOKEN"

Write-Host "`n📋 Copy these values to GitHub Secrets"
```

---

## ✅ Verification Checklist

Before running the deployment pipeline, verify:

- [ ] All 15+ secrets are added to GitHub repository
- [ ] Service Principal has Contributor role on resource group
- [ ] Azure subscription has sufficient quota for resources
- [ ] Container Registry admin user is enabled
- [ ] Static Web App deployment token is valid
- [ ] Environment secrets are configured (if using environments)

---

## 🔍 Troubleshooting

### Secret Not Found Error
- Verify secret name matches exactly (case-sensitive)
- Check if secret is added at repository level (not environment level)

### Authentication Failed
- Regenerate Service Principal credentials
- Verify `AZURE_CREDENTIALS` JSON is valid
- Check Service Principal has correct permissions

### Container Registry Login Failed
- Enable admin user in ACR settings
- Regenerate ACR passwords
- Verify `AZURE_ACR_PASSWORD` is the password, not username

### Static Web App Deployment Failed
- Regenerate deployment token
- Verify token has not expired
- Check Static Web App exists in Azure Portal

---

## 📚 Additional Resources

- [Azure Service Principal documentation](https://learn.microsoft.com/azure/active-directory/develop/howto-create-service-principal-portal)
- [GitHub Actions secrets documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Azure Container Registry authentication](https://learn.microsoft.com/azure/container-registry/container-registry-authentication)
