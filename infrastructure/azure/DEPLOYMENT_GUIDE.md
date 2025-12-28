# 🚀 AgriSense Azure Deployment Guide

**Complete deployment guide for AgriSense full-stack application on Azure**

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Initial Setup](#initial-setup)
4. [Infrastructure Deployment](#infrastructure-deployment)
5. [Application Deployment](#application-deployment)
6. [Post-Deployment Configuration](#post-deployment-configuration)
7. [Monitoring and Maintenance](#monitoring-and-maintenance)
8. [Troubleshooting](#troubleshooting)
9. [Cost Optimization](#cost-optimization)

---

## Prerequisites

### Required Tools

- **Azure CLI** >= 2.50.0: [Install](https://docs.microsoft.com/cli/azure/install-azure-cli)
- **Azure Bicep** >= 0.20.0: `az bicep install`
- **Docker** >= 24.0: [Install](https://docs.docker.com/get-docker/)
- **Git** >= 2.40.0
- **PowerShell** >= 7.3 (for scripts)
- **Python** >= 3.12.10 (for local testing)
- **Node.js** >= 20.0 (for frontend builds)

### Azure Subscription Requirements

- Active Azure subscription with:
  - Contributor or Owner role
  - Sufficient quota for:
    - App Service Plan (1 instance)
    - Container Registry (1 Basic/Standard)
    - Cosmos DB (Serverless)
    - Storage Account (1 Standard)
    - Static Web App (1 Free/Standard)
  - Billing enabled

### Cost Estimate

| Environment | Monthly Cost (USD) |
|-------------|-------------------|
| Development | $50-100 |
| Staging | $100-200 |
| Production | $200-500 |

---

## Architecture Overview

### Azure Services Used

```
┌─────────────────────────────────────────────────────────────────┐
│                         Azure Cloud                             │
│                                                                 │
│  ┌────────────────┐         ┌──────────────────┐              │
│  │ Static Web App │────────▶│  App Service     │              │
│  │  (Frontend)    │         │  (Backend API)   │              │
│  │  React + Vite  │         │  Python 3.12.10  │              │
│  └────────────────┘         └──────────────────┘              │
│         │                            │                          │
│         │                            │                          │
│         ▼                            ▼                          │
│  ┌─────────────────────────────────────────────┐              │
│  │          Azure Cosmos DB                    │              │
│  │  - SensorData container (/deviceId)        │              │
│  │  - Recommendations container (/fieldId)    │              │
│  │  - ChatHistory container (/userId)         │              │
│  └─────────────────────────────────────────────┘              │
│                            │                                    │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────┐              │
│  │     Azure Storage Account (Blob)            │              │
│  │  - ml-models (ML artifacts)                │              │
│  │  - sensor-data (historical data)           │              │
│  │  - logs (application logs)                 │              │
│  └─────────────────────────────────────────────┘              │
│                                                                 │
│  ┌────────────────┐    ┌──────────────┐    ┌───────────────┐ │
│  │ Container      │    │ Key Vault    │    │ Application   │ │
│  │ Registry (ACR) │    │ (Secrets)    │    │ Insights      │ │
│  └────────────────┘    └──────────────┘    └───────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Components

1. **Static Web App**: Hosts React frontend with global CDN
2. **App Service**: Runs FastAPI backend (Python 3.12.10)
3. **Container Registry**: Stores Docker images
4. **Cosmos DB**: NoSQL database for sensor data and recommendations
5. **Storage Account**: Blob storage for ML models and logs
6. **Key Vault**: Secure secrets management
7. **Application Insights**: Monitoring and diagnostics

---

## Initial Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/ELANGKATHIR11/AGRISENSEFULL-STACK.git
cd AGRISENSEFULL-STACK/AGRISENSEFULL-STACK
```

### Step 2: Login to Azure

```bash
az login
az account set --subscription "Your Subscription Name or ID"
```

### Step 3: Create Resource Group

```bash
# For development
az group create --name agrisense-dev-rg --location eastus

# For production
az group create --name agrisense-prod-rg --location eastus
```

### Step 4: Register Required Resource Providers

```bash
az provider register --namespace Microsoft.Web
az provider register --namespace Microsoft.ContainerRegistry
az provider register --namespace Microsoft.DocumentDB
az provider register --namespace Microsoft.Storage
az provider register --namespace Microsoft.KeyVault
az provider register --namespace Microsoft.Insights

# Verify registration (should show "Registered")
az provider show --namespace Microsoft.Web --query "registrationState"
```

---

## Infrastructure Deployment

### Option 1: Deploy Using Azure CLI (Recommended)

```bash
# Navigate to infrastructure directory
cd infrastructure/azure

# Deploy development environment
az deployment group create \
  --resource-group agrisense-dev-rg \
  --template-file main.bicep \
  --parameters parameters.dev.json \
  --name agrisense-deployment-$(date +%Y%m%d-%H%M%S)

# Deploy production environment
az deployment group create \
  --resource-group agrisense-prod-rg \
  --template-file main.bicep \
  --parameters parameters.prod.json \
  --name agrisense-deployment-$(date +%Y%m%d-%H%M%S)
```

### Option 2: Deploy Using PowerShell Script

```powershell
# From project root
.\infrastructure\azure\deploy.ps1 -Environment dev -ResourceGroup agrisense-dev-rg

# For production
.\infrastructure\azure\deploy.ps1 -Environment prod -ResourceGroup agrisense-prod-rg
```

### Step 5: Save Deployment Outputs

```bash
# Get deployment outputs
az deployment group show \
  --resource-group agrisense-dev-rg \
  --name <deployment-name> \
  --query properties.outputs
```

**Save these values** - you'll need them for GitHub Secrets:
- `containerRegistryName`
- `containerRegistryLoginServer`
- `backendAppUrl`
- `frontendAppUrl`
- `cosmosDbEndpoint`
- `keyVaultName`
- `appInsightsConnectionString`

---

## Application Deployment

### Method 1: GitHub Actions CI/CD (Recommended)

#### Step 1: Configure GitHub Secrets

Follow [infrastructure/azure/SECRETS_CONFIGURATION.md](./SECRETS_CONFIGURATION.md) to set up all required secrets.

#### Step 2: Configure Environments

1. Go to Repository Settings → Environments
2. Create `dev`, `staging`, `prod` environments
3. Configure deployment protection rules:
   - **dev**: No restrictions
   - **staging**: Require approval from 1 reviewer
   - **prod**: Require approval from 2 reviewers

#### Step 3: Push to Trigger Deployment

```bash
# Development deployment
git checkout develop
git push origin develop

# Production deployment (requires PR merge)
git checkout main
git merge develop
git push origin main
```

#### Step 4: Monitor Deployment

1. Go to GitHub Actions tab
2. Watch workflow progress
3. Verify all jobs complete successfully

### Method 2: Manual Deployment

#### Step 1: Build and Push Docker Images

```bash
# Login to Azure Container Registry
az acr login --name <your-acr-name>

# Build backend image
docker build -t <your-acr-name>.azurecr.io/agrisense/backend:latest -f Dockerfile.azure .

# Build frontend image
docker build -t <your-acr-name>.azurecr.io/agrisense/frontend:latest -f Dockerfile.frontend.azure .

# Push images
docker push <your-acr-name>.azurecr.io/agrisense/backend:latest
docker push <your-acr-name>.azurecr.io/agrisense/frontend:latest
```

#### Step 2: Deploy Backend to App Service

```bash
az webapp config container set \
  --name <backend-app-name> \
  --resource-group agrisense-dev-rg \
  --docker-custom-image-name <your-acr-name>.azurecr.io/agrisense/backend:latest \
  --docker-registry-server-url https://<your-acr-name>.azurecr.io \
  --docker-registry-server-user <acr-username> \
  --docker-registry-server-password <acr-password>

# Restart app
az webapp restart --name <backend-app-name> --resource-group agrisense-dev-rg
```

#### Step 3: Deploy Frontend to Static Web App

```bash
# Build frontend locally
cd agrisense_app/frontend/farm-fortune-frontend-main
npm ci
npm run build

# Deploy using Static Web App CLI
npx @azure/static-web-apps-cli deploy \
  --app-location dist \
  --deployment-token <your-deployment-token>
```

---

## Post-Deployment Configuration

### Step 1: Upload ML Models to Blob Storage

```bash
# Set storage account name
STORAGE_ACCOUNT="<your-storage-account-name>"

# Upload ML models
az storage blob upload-batch \
  --account-name $STORAGE_ACCOUNT \
  --destination ml-models \
  --source agrisense_app/backend/ml_models \
  --auth-mode login
```

### Step 2: Configure App Service Environment Variables

```bash
# Set backend app name
BACKEND_APP="<backend-app-name>"

# Configure environment variables
az webapp config appsettings set \
  --name $BACKEND_APP \
  --resource-group agrisense-dev-rg \
  --settings \
    AGRISENSE_ENV=production \
    PYTHON_VERSION=3.12 \
    AGRISENSE_DISABLE_ML=0 \
    LOG_LEVEL=INFO
```

### Step 3: Configure Cosmos DB

```bash
# Get Cosmos DB connection details
COSMOS_ENDPOINT=$(az cosmosdb show \
  --name <cosmos-account-name> \
  --resource-group agrisense-dev-rg \
  --query documentEndpoint -o tsv)

COSMOS_KEY=$(az cosmosdb keys list \
  --name <cosmos-account-name> \
  --resource-group agrisense-dev-rg \
  --query primaryMasterKey -o tsv)

# Add to app settings
az webapp config appsettings set \
  --name $BACKEND_APP \
  --resource-group agrisense-dev-rg \
  --settings \
    COSMOS_DB_ENDPOINT=$COSMOS_ENDPOINT \
    COSMOS_DB_KEY=$COSMOS_KEY
```

### Step 4: Configure Custom Domain (Optional)

```bash
# Add custom domain to Static Web App
az staticwebapp hostname set \
  --name <frontend-app-name> \
  --resource-group agrisense-dev-rg \
  --hostname www.yourdomain.com

# Configure SSL (automatic with Static Web Apps)
```

### Step 5: Enable Continuous Deployment

```bash
# Enable continuous deployment for App Service
az webapp deployment container config \
  --name $BACKEND_APP \
  --resource-group agrisense-dev-rg \
  --enable-cd true
```

---

## Monitoring and Maintenance

### Application Insights Queries

```kusto
-- Backend request errors
requests
| where timestamp > ago(1h)
| where success == false
| summarize count() by resultCode, operation_Name
| order by count_ desc

-- Backend performance
requests
| where timestamp > ago(1h)
| summarize avg(duration), percentile(duration, 95) by operation_Name

-- Frontend page views
pageViews
| where timestamp > ago(24h)
| summarize count() by name
| order by count_ desc
```

### Health Checks

```bash
# Backend health check
curl https://<backend-app-name>.azurewebsites.net/health

# Backend ready check
curl https://<backend-app-name>.azurewebsites.net/ready

# Frontend health check
curl https://<frontend-url>
```

### Log Streaming

```bash
# Stream backend logs
az webapp log tail --name <backend-app-name> --resource-group agrisense-dev-rg

# Download logs
az webapp log download --name <backend-app-name> --resource-group agrisense-dev-rg --log-file logs.zip
```

### Scaling

```bash
# Scale backend App Service
az appservice plan update \
  --name <app-service-plan-name> \
  --resource-group agrisense-dev-rg \
  --sku P1V2

# Enable autoscaling
az monitor autoscale create \
  --resource-group agrisense-dev-rg \
  --resource <app-service-plan-id> \
  --resource-type Microsoft.Web/serverfarms \
  --name agrisense-autoscale \
  --min-count 1 \
  --max-count 4 \
  --count 2
```

---

## Troubleshooting

### Backend Not Starting

**Symptoms**: App Service shows "Application Error" or 502 Bad Gateway

**Solutions**:
1. Check App Service logs:
   ```bash
   az webapp log tail --name <backend-app-name> --resource-group agrisense-dev-rg
   ```

2. Verify Docker image is pulling correctly:
   ```bash
   az webapp show --name <backend-app-name> --resource-group agrisense-dev-rg \
     --query siteConfig.linuxFxVersion
   ```

3. Check environment variables are set correctly:
   ```bash
   az webapp config appsettings list --name <backend-app-name> --resource-group agrisense-dev-rg
   ```

4. Verify Python version:
   - Image must use Python 3.12.10
   - Check `Dockerfile.azure` base image

### Cosmos DB Connection Issues

**Symptoms**: Backend returns 500 errors with Cosmos DB exceptions

**Solutions**:
1. Verify Cosmos DB endpoint and key:
   ```bash
   az cosmosdb show --name <cosmos-account-name> --resource-group agrisense-dev-rg
   ```

2. Check network access:
   - Ensure firewall allows App Service IP
   - Or enable "Allow access from Azure services"

3. Test connection:
   ```python
   from azure.cosmos import CosmosClient
   client = CosmosClient(url=<endpoint>, credential=<key>)
   database = client.get_database_client("AgriSense")
   ```

### Static Web App Not Loading

**Symptoms**: Frontend shows 404 or blank page

**Solutions**:
1. Verify build output directory:
   - Should be `dist` folder with `index.html`
   
2. Check build configuration:
   ```json
   {
     "outputLocation": "dist",
     "appLocation": "agrisense_app/frontend/farm-fortune-frontend-main"
   }
   ```

3. Rebuild and redeploy:
   ```bash
   cd agrisense_app/frontend/farm-fortune-frontend-main
   npm run build
   # Verify dist/ folder has index.html
   ```

### ML Models Not Loading

**Symptoms**: Disease detection/weed management returns errors

**Solutions**:
1. Verify blob storage connection:
   ```bash
   az storage blob list --account-name <storage-account> --container-name ml-models
   ```

2. Check App Service has storage account key:
   ```bash
   az webapp config appsettings show --name <backend-app-name> --resource-group agrisense-dev-rg \
     --setting-names AZURE_STORAGE_CONNECTION_STRING
   ```

3. Upload models if missing:
   ```bash
   az storage blob upload-batch \
     --account-name <storage-account> \
     --destination ml-models \
     --source agrisense_app/backend/ml_models
   ```

---

## Cost Optimization

### Development Environment

- Use **B1 App Service Plan** ($13/month)
- Use **Basic Container Registry** ($5/month)
- Use **Cosmos DB Serverless** (pay per request)
- Use **Free tier Static Web App**
- **Total**: ~$50-70/month

### Production Environment

- Use **P1V2 App Service Plan** ($73/month) with autoscaling
- Use **Standard Container Registry** ($20/month)
- Use **Cosmos DB with autoscale RUs** ($24+/month)
- Use **Standard tier Static Web App** ($9/month)
- Enable **Azure CDN** for frontend caching
- **Total**: ~$200-300/month

### Cost Saving Tips

1. **Stop non-production environments** when not in use:
   ```bash
   az webapp stop --name <app-name> --resource-group <rg>
   ```

2. **Use reserved capacity** for production (1-year or 3-year commitment)

3. **Enable Application Insights sampling** to reduce ingestion costs

4. **Set Cosmos DB TTL** to auto-delete old sensor data

5. **Use blob lifecycle management** to archive old logs to Cool tier

---

## Next Steps

After successful deployment:

1. ✅ Configure monitoring alerts in Application Insights
2. ✅ Set up Azure DevOps boards for issue tracking
3. ✅ Configure backup policies for Cosmos DB
4. ✅ Set up Azure Front Door for global distribution (optional)
5. ✅ Implement Azure API Management for API governance (optional)
6. ✅ Configure Azure IoT Hub for real sensor integration

---

## Support

- **Documentation**: `/documentation/`
- **Issues**: GitHub Issues
- **Azure Support**: [Azure Portal Support](https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade)

---

**Deployment Date**: December 6, 2025  
**Version**: 1.0.0  
**Tech Stack**: Python 3.12.10 | React 18.3.1 | Azure Cloud
