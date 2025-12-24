# Azure Free Tier Deployment Guide for AgriSense

## 🆓 Free Tier Services Used

Your AgriSense deployment will use these **free or low-cost** Azure services:

| Service | Free Tier Details | Monthly Cost |
|---------|-------------------|--------------|
| **App Service (F1 Free)** | 60 CPU minutes/day, 1GB RAM | **$0** |
| **Cosmos DB (Free Tier)** | 1000 RU/s, 25GB storage | **$0** (first 1000 RU/s) |
| **Static Web App (Free)** | 100GB bandwidth, custom domain | **$0** |
| **Storage Account** | 5GB blob storage, 20K transactions | **$0.23** |
| **Container Registry (Basic)** | 10GB storage | **$5** |
| **Application Insights** | 5GB data ingestion | **$0** |
| **Key Vault** | 10K transactions | **$0.50** |

**Total Estimated Cost: ~$6/month** (mostly Container Registry)

---

## 🚀 Quick Deployment Steps

### Step 1: Login to Azure
```powershell
# Login to Azure (will open browser)
az login

# Verify your subscription
az account show

# If you have multiple subscriptions, set the free one
az account list --output table
az account set --subscription "<your-subscription-id>"
```

### Step 2: Register Required Providers
```powershell
# Register Azure resource providers (required for first-time users)
az provider register --namespace Microsoft.Web
az provider register --namespace Microsoft.DocumentDB
az provider register --namespace Microsoft.ContainerRegistry
az provider register --namespace Microsoft.Storage
az provider register --namespace Microsoft.Insights
az provider register --namespace Microsoft.KeyVault

# Wait for registration (takes 2-5 minutes)
az provider show --namespace Microsoft.Web --query "registrationState"
```

### Step 3: Deploy Infrastructure
```powershell
cd "D:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK"

# Deploy using PowerShell script with free tier parameters
.\infrastructure\azure\deploy.ps1 `
  -Environment free `
  -ResourceGroup agrisense-free-rg `
  -Location eastus
```

**Alternative: Manual Azure CLI Deployment**
```powershell
# Create resource group
az group create --name agrisense-free-rg --location eastus

# Deploy Bicep template with free tier parameters
az deployment group create `
  --resource-group agrisense-free-rg `
  --template-file infrastructure/azure/main.bicep `
  --parameters infrastructure/azure/parameters.free.json `
  --parameters projectName=agrisense
```

---

## ⚠️ Free Tier Limitations & Workarounds

### App Service F1 (Free Tier)
**Limitations:**
- ❌ No custom domains
- ❌ 60 CPU minutes/day limit (~30 requests/day for ML models)
- ❌ Apps sleep after 20 minutes of inactivity
- ❌ No scale-out (1 instance only)

**Workarounds:**
1. **Disable ML models**: Set `AGRISENSE_DISABLE_ML=1` to reduce CPU usage
2. **Use rule-based logic**: Chatbot and recommendations work without ML
3. **Keep app warm**: Use Azure Logic App (free) to ping `/health` every 15 minutes
4. **Accept cold starts**: First request after sleep takes 30-60 seconds

**Upgrade Path**: B1 Basic ($13/month) removes most limitations

### Cosmos DB Free Tier
**Limitations:**
- ✅ 1000 RU/s throughput (sufficient for small-scale deployment)
- ✅ 25GB storage (enough for thousands of sensor readings)
- ❌ One free account per Azure subscription
- ❌ No SLA guarantee

**Workarounds:**
1. Already optimized with partition keys (`/deviceId`, `/fieldId`, `/userId`)
2. TTL enabled (auto-delete old data): 90 days for sensor data, 30 days for chat history
3. If you exceed limits, serverless pricing starts at $0.282/million RUs

### Container Registry Basic ($5/month)
**Limitations:**
- ✅ 10GB storage (sufficient for 2-3 Docker images)
- ❌ No free tier available

**Workarounds:**
1. **Use Docker Hub (Free)**: 1 private repo, unlimited public
   ```powershell
   # Push to Docker Hub instead of ACR
   docker login
   docker tag agrisense/backend:latest yourusername/agrisense-backend:latest
   docker push yourusername/agrisense-backend:latest
   ```
2. **Use GitHub Container Registry (Free)**: Included with GitHub account
3. **Accept the $5 cost**: Cheapest option for private Azure registry

---

## 🔧 Free Tier Optimizations

### Backend Configuration (.env)
```bash
# Disable resource-intensive features
AGRISENSE_DISABLE_ML=1              # No TensorFlow/PyTorch models
WORKERS=1                            # Single worker for F1 tier
LOG_LEVEL=WARNING                    # Reduce log volume
ENABLE_CACHE=true                    # Enable response caching
CACHE_TTL=3600                       # 1-hour cache to reduce DB queries

# Cosmos DB connection (auto-configured by deployment)
COSMOS_ENDPOINT=https://<cosmos-account>.documents.azure.com
COSMOS_KEY=<from-key-vault>
COSMOS_DATABASE=AgriSense
```

### Frontend Configuration
```bash
# Static Web App (free tier)
VITE_API_URL=https://<backend-app-name>.azurewebsites.net
```

---

## 📊 Monitoring Free Tier Usage

### Check App Service Quota
```powershell
# View CPU minutes used today
az monitor metrics list `
  --resource "/subscriptions/<sub-id>/resourceGroups/agrisense-free-rg/providers/Microsoft.Web/sites/<app-name>" `
  --metric "CpuTime" `
  --start-time (Get-Date).AddHours(-24).ToString("yyyy-MM-ddTHH:mm:ss") `
  --end-time (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
```

### Check Cosmos DB RU/s Usage
```powershell
# View request units consumed
az cosmosdb sql database throughput show `
  --account-name <cosmos-account> `
  --name AgriSense `
  --resource-group agrisense-free-rg
```

### View Application Insights
```powershell
# Open in browser
az portal show --resource-group agrisense-free-rg --name <app-insights-name>
```

---

## 🛠️ Troubleshooting Free Tier Issues

### Issue 1: "App Service quota exceeded"
**Symptom**: 503 Service Unavailable after ~30 requests
**Solution**:
```powershell
# Check quota usage
az webapp show --name <app-name> --resource-group agrisense-free-rg --query "siteConfig.limits"

# Wait until next day (quota resets at midnight UTC)
# Or upgrade to B1 tier:
az appservice plan update --name <plan-name> --resource-group agrisense-free-rg --sku B1
```

### Issue 2: "Container Registry quota exceeded"
**Symptom**: Cannot push Docker images (10GB limit reached)
**Solution**:
```powershell
# List images and sizes
az acr repository list --name <acr-name>

# Delete old images
az acr repository delete --name <acr-name> --image agrisense/backend:old-tag --yes

# Or switch to Docker Hub (free)
```

### Issue 3: "Cosmos DB free tier already used"
**Symptom**: Deployment fails with "Free tier account already exists"
**Solution**:
- Azure allows only ONE free Cosmos DB per subscription
- Check existing accounts: `az cosmosdb list --output table`
- Options:
  1. Delete old free tier account
  2. Use serverless pricing (~$10/month for low usage)
  3. Create new Azure subscription (new free tier eligibility)

### Issue 4: "App sleeps after 20 minutes"
**Symptom**: First request takes 30-60 seconds (cold start)
**Solution**:
```powershell
# Option 1: Keep app warm with Logic App (free tier)
# - Create Logic App with HTTP trigger
# - Run every 15 minutes: GET https://<app-name>.azurewebsites.net/health

# Option 2: Upgrade to B1 ($13/month) - Always On feature
az appservice plan update --name <plan-name> --resource-group agrisense-free-rg --sku B1
```

---

## 💡 Cost-Saving Tips

1. **Stop when not in use**:
   ```powershell
   # Stop app service (keeps configuration)
   az webapp stop --name <app-name> --resource-group agrisense-free-rg
   
   # Start when needed
   az webapp start --name <app-name> --resource-group agrisense-free-rg
   ```

2. **Delete test deployments**:
   ```powershell
   # Delete entire resource group (removes ALL resources)
   az group delete --name agrisense-free-rg --yes --no-wait
   ```

3. **Monitor costs**:
   ```powershell
   # View current month costs
   az consumption usage list --query "[?properties.instanceId contains 'agrisense']" --output table
   ```

4. **Set spending limit**:
   - Azure portal → Cost Management → Budgets
   - Create alert at $10/month

---

## 🎯 Post-Deployment Checklist

### Immediate (Day 1)
- [ ] Login to Azure: `az login`
- [ ] Register providers (wait 5 minutes)
- [ ] Deploy infrastructure
- [ ] Verify backend health: `https://<app-name>.azurewebsites.net/health`
- [ ] Verify frontend loads: `https://<frontend-app-name>.azurestaticapps.net`
- [ ] Test irrigation feature (rule-based, no ML)
- [ ] Test chatbot (works without ML)

### Week 1
- [ ] Set up cost alerts ($10 threshold)
- [ ] Configure keep-warm Logic App (optional)
- [ ] Upload ML models to blob storage (if upgrading to B1)
- [ ] Test all 5 languages on frontend
- [ ] Monitor CPU quota usage

### Ongoing
- [ ] Review costs weekly in Azure Portal
- [ ] Clean up old container images
- [ ] Check Cosmos DB storage usage (<25GB)
- [ ] Test disaster recovery (backup/restore)

---

## 🚀 Upgrade Path (When Ready)

When your free trial $200 credit is exhausted or you need more resources:

| Tier | Monthly Cost | Benefits |
|------|--------------|----------|
| **Current: Free** | ~$6 | Good for testing, limited usage |
| **Basic: B1** | ~$20 | Always On, no CPU limits, 1.75GB RAM |
| **Standard: S1** | ~$80 | Auto-scale, custom domains, SSL |
| **Premium: P1V2** | ~$75 | Zone redundancy, VNet integration |

**Upgrade Command**:
```powershell
# Upgrade App Service Plan to B1
az appservice plan update --name <plan-name> --resource-group agrisense-free-rg --sku B1

# Enable Always On
az webapp config set --name <app-name> --resource-group agrisense-free-rg --always-on true

# Re-enable ML models
az webapp config appsettings set --name <app-name> --resource-group agrisense-free-rg --settings AGRISENSE_DISABLE_ML=0
```

---

## 📚 Additional Resources

- **Azure Free Account**: https://azure.microsoft.com/free/
- **Free Services List**: https://azure.microsoft.com/pricing/free-services/
- **Cost Calculator**: https://azure.microsoft.com/pricing/calculator/
- **AgriSense Deployment Guide**: `DEPLOYMENT_GUIDE.md`
- **Secrets Configuration**: `SECRETS_CONFIGURATION.md`

---

**Deployment Time**: ~30 minutes  
**Expected Cost**: ~$6/month (mostly Container Registry)  
**Free Trial Credit**: $200 (lasts ~33 months at this rate)
