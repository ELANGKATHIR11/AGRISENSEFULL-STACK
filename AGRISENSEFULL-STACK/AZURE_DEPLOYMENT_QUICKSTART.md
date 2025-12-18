# 🚀 AgriSense Azure Deployment - Quick Start Guide

**Last Updated**: December 6, 2025  
**Deployment Time**: ~30 minutes  
**Free Domains**: ✅ `.azurewebsites.net` and `.azurestaticapps.net` (FREE forever!)

---

## 📋 Prerequisites Checklist

- [x] ✅ GitHub CLI installed and authenticated
- [x] ✅ Azure CLI installed (version 2.80.0)
- [x] ✅ GitHub secrets configured (10 essential secrets)
- [x] ✅ GitHub environments created (dev, staging, production)
- [ ] ⚠️ Azure subscription needed (create free account below)

---

## 🆓 STEP 1: Create Free Azure Account

### Sign Up for Azure Free Account
1. **Visit**: https://azure.microsoft.com/free/
2. **Sign in** with your Microsoft account (or create one)
3. **Verify** your identity (phone + credit card for verification only)
4. **Get Benefits**:
   - 💵 **$200 credit** for 30 days
   - 🎁 **12 months** of popular free services
   - ♾️ **Always free** services (25+ products)

### What You Get for FREE
- **Static Web Apps**: Unlimited (100% free tier available)
- **App Service**: 10 free web apps
- **Cosmos DB**: 1000 RU/s + 25GB storage free
- **Container Registry**: Basic tier available
- **Application Insights**: 5GB data ingestion/month free

### Your Free Domains
```
Backend:  https://agrisense-dev-backend-<unique-id>.azurewebsites.net
Frontend: https://agrisense-dev-frontend-<unique-id>.azurestaticapps.net
```
**Note**: These `.azurewebsites.net` and `.azurestaticapps.net` domains are **completely free forever**!

---

## 🔧 STEP 2: Authenticate Azure CLI

After creating your Azure account:

```powershell
# Login to Azure
az login

# Verify subscription
az account show

# List available subscriptions
az account list --output table
```

**Expected Output**:
```
Name                          SubscriptionId                        State
----------------------------  ------------------------------------  -------
Azure subscription 1          xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx  Enabled
```

---

## 🚀 STEP 3: Deploy AgriSense (Automated)

### Option A: One-Command Deployment (Recommended)

```powershell
# Navigate to project
cd "D:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK"

# Run automated deployment
.\infrastructure\azure\deploy.ps1 -Environment dev
```

**What This Does**:
1. ✅ Creates Azure resource group
2. ✅ Deploys infrastructure (Bicep template)
3. ✅ Builds Docker images (backend + frontend)
4. ✅ Pushes images to Azure Container Registry
5. ✅ Deploys to App Service + Static Web App
6. ✅ Runs health checks
7. ✅ Displays deployment URLs

**Deployment Time**: ~30 minutes

### Option B: Step-by-Step Deployment

```powershell
# 1. Create resource group
az group create --name agrisense-dev-rg --location eastus

# 2. Deploy infrastructure
az deployment group create `
  --resource-group agrisense-dev-rg `
  --template-file infrastructure/azure/main.bicep `
  --parameters infrastructure/azure/parameters.dev.json

# 3. Get ACR credentials
$acrName = az deployment group show `
  --resource-group agrisense-dev-rg `
  --name main `
  --query properties.outputs.containerRegistryName.value `
  --output tsv

# 4. Login to ACR
az acr login --name $acrName

# 5. Build and push backend
docker build -f Dockerfile.azure -t ${acrName}.azurecr.io/agrisense-backend:latest .
docker push ${acrName}.azurecr.io/agrisense-backend:latest

# 6. Build and push frontend
docker build -f Dockerfile.frontend.azure -t ${acrName}.azurecr.io/agrisense-frontend:latest .
docker push ${acrName}.azurecr.io/agrisense-frontend:latest

# 7. Restart App Service
az webapp restart --name agrisense-dev-backend-<unique-id> --resource-group agrisense-dev-rg

# 8. Deploy frontend to Static Web App
cd agrisense_app/frontend/farm-fortune-frontend-main
npm run build
az staticwebapp deploy --name agrisense-dev-frontend-<unique-id> --resource-group agrisense-dev-rg
```

---

## 🌍 STEP 4: Verify Deployment

### Check Backend Health
```powershell
# Get backend URL
$backendUrl = az webapp show `
  --name agrisense-dev-backend-<unique-id> `
  --resource-group agrisense-dev-rg `
  --query defaultHostName `
  --output tsv

# Test health endpoint
Invoke-WebRequest -Uri "https://$backendUrl/health"
```

**Expected Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-12-06T14:00:00Z"
}
```

### Check Frontend
```powershell
# Get frontend URL
$frontendUrl = az staticwebapp show `
  --name agrisense-dev-frontend-<unique-id> `
  --resource-group agrisense-dev-rg `
  --query defaultHostname `
  --output tsv

# Open in browser
Start-Process "https://$frontendUrl"
```

### Verify All Services
```powershell
# Check resource group status
az resource list --resource-group agrisense-dev-rg --output table
```

**Expected Resources**:
- ✅ App Service Plan (B1)
- ✅ App Service (backend)
- ✅ Static Web App (frontend)
- ✅ Container Registry (Basic)
- ✅ Cosmos DB Account
- ✅ Storage Account
- ✅ Key Vault
- ✅ Application Insights

---

## 📊 STEP 5: Monitor & Manage

### Application Insights Dashboard
```powershell
# Get Application Insights URL
az monitor app-insights component show `
  --app agrisense-dev-insights `
  --resource-group agrisense-dev-rg `
  --query appId `
  --output tsv
```

### View Logs
```powershell
# Stream backend logs
az webapp log tail `
  --name agrisense-dev-backend-<unique-id> `
  --resource-group agrisense-dev-rg

# View deployment history
az deployment group list `
  --resource-group agrisense-dev-rg `
  --output table
```

### Cost Management
```powershell
# Check current spending
az consumption usage list `
  --start-date 2025-12-01 `
  --end-date 2025-12-31 `
  --output table
```

---

## 💰 Cost Breakdown (Development Environment)

| Service | SKU | Monthly Cost | Free Credit |
|---------|-----|--------------|-------------|
| **App Service Plan** | B1 | $13.14/month | ✅ Covered |
| **Static Web App** | Free | $0.00/month | ✅ Always Free |
| **Container Registry** | Basic | $5.00/month | ✅ Covered |
| **Cosmos DB** | Serverless | ~$10.00/month | ✅ Covered |
| **Storage Account** | Standard LRS | ~$2.00/month | ✅ Covered |
| **Application Insights** | Basic | ~$5.00/month | ✅ Covered |
| **Key Vault** | Standard | ~$0.50/month | ✅ Covered |
| **TOTAL** | | **~$35.64/month** | **Covered by $200 credit** |

**Credit Duration**: 6+ months of development with $200 credit

---

## 🎯 Custom Domain Setup (Optional)

If you want a custom domain (e.g., `agrisense.com`, `agrisense.net`, `agrisense.app`):

### Buy Domain (~$12/year)
- **Namecheap**: https://www.namecheap.com/
- **Google Domains**: https://domains.google/
- **GoDaddy**: https://www.godaddy.com/

### Configure Custom Domain

**Backend (App Service)**:
```powershell
# Add custom domain
az webapp config hostname add `
  --webapp-name agrisense-dev-backend-<unique-id> `
  --resource-group agrisense-dev-rg `
  --hostname api.agrisense.com

# Enable HTTPS
az webapp config ssl bind `
  --certificate-thumbprint <cert-thumbprint> `
  --ssl-type SNI `
  --name agrisense-dev-backend-<unique-id> `
  --resource-group agrisense-dev-rg
```

**Frontend (Static Web App)**:
```powershell
# Add custom domain
az staticwebapp hostname set `
  --name agrisense-dev-frontend-<unique-id> `
  --resource-group agrisense-dev-rg `
  --hostname www.agrisense.com
```

### DNS Configuration
Add these records to your domain DNS:

**Backend API**:
```
Type: CNAME
Name: api
Value: agrisense-dev-backend-<unique-id>.azurewebsites.net
TTL: 3600
```

**Frontend**:
```
Type: CNAME
Name: www
Value: agrisense-dev-frontend-<unique-id>.azurestaticapps.net
TTL: 3600
```

---

## 🔧 Troubleshooting

### Issue 1: Deployment Fails
```powershell
# Check deployment logs
az deployment group show `
  --resource-group agrisense-dev-rg `
  --name main `
  --query properties.error

# Retry deployment
.\infrastructure\azure\deploy.ps1 -Environment dev
```

### Issue 2: Backend Not Starting
```powershell
# Check container logs
az webapp log tail `
  --name agrisense-dev-backend-<unique-id> `
  --resource-group agrisense-dev-rg

# Verify container registry credentials
az acr credential show --name <acr-name>

# Restart app
az webapp restart `
  --name agrisense-dev-backend-<unique-id> `
  --resource-group agrisense-dev-rg
```

### Issue 3: Frontend Not Loading
```powershell
# Check Static Web App deployment
az staticwebapp show `
  --name agrisense-dev-frontend-<unique-id> `
  --resource-group agrisense-dev-rg

# Redeploy frontend
cd agrisense_app/frontend/farm-fortune-frontend-main
npm run build
az staticwebapp deploy --name agrisense-dev-frontend-<unique-id>
```

### Issue 4: Database Connection Errors
```powershell
# Get Cosmos DB connection string
az cosmosdb keys list `
  --name agrisense-dev-cosmos-<unique-id> `
  --resource-group agrisense-dev-rg `
  --type connection-strings

# Update App Service configuration
az webapp config appsettings set `
  --name agrisense-dev-backend-<unique-id> `
  --resource-group agrisense-dev-rg `
  --settings COSMOS_CONNECTION_STRING="<connection-string>"
```

---

## 📚 Additional Resources

- **Azure Portal**: https://portal.azure.com/
- **Deployment Guide**: `DEPLOYMENT_GUIDE.md`
- **Infrastructure Code**: `infrastructure/azure/main.bicep`
- **Docker Configuration**: `Dockerfile.azure`, `Dockerfile.frontend.azure`
- **GitHub Actions**: `.github/workflows/azure-deploy.yml`
- **Secrets Configuration**: `.github/SECRETS_SETUP_GUIDE.md`

---

## ✅ Post-Deployment Checklist

After successful deployment:

- [ ] ✅ Verify backend health endpoint responds
- [ ] ✅ Verify frontend loads correctly
- [ ] ✅ Test irrigation recommendation feature
- [ ] ✅ Test disease detection feature
- [ ] ✅ Test chatbot functionality
- [ ] ✅ Verify database connectivity (Cosmos DB)
- [ ] ✅ Check Application Insights for errors
- [ ] ✅ Set up alerts for failures
- [ ] ✅ Configure auto-scaling if needed
- [ ] ✅ Enable backup policies
- [ ] ✅ Document deployment URLs
- [ ] ✅ Share URLs with team

---

## 🎉 Success!

Your AgriSense application is now live on Azure with FREE domains:

```
🌐 Frontend: https://agrisense-dev-frontend-<unique-id>.azurestaticapps.net
🔌 Backend:  https://agrisense-dev-backend-<unique-id>.azurewebsites.net/health
📊 Insights: Azure Portal → Application Insights
💰 Cost:     ~$28-35/month (covered by $200 free credit for 6+ months)
```

**Next Steps**:
1. Test all features in production
2. Set up monitoring alerts
3. Configure CI/CD for automatic deployments
4. Consider custom domain for professional look
5. Scale resources based on usage

---

**Need Help?**
- Azure Support: https://azure.microsoft.com/support/
- Project Documentation: `documentation/` folder
- GitHub Issues: Create issue in repository
