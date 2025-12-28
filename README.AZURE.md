# 🌾 AgriSense - Azure Deployment

**Smart Agriculture Platform deployed on Microsoft Azure**

[![Python 3.12.10](https://img.shields.io/badge/Python-3.12.10-blue.svg)](https://www.python.org/downloads/release/python-31210/)
[![React 18.3.1](https://img.shields.io/badge/React-18.3.1-61DAFB.svg)](https://react.dev/)
[![Azure](https://img.shields.io/badge/Azure-Cloud-0078D4.svg)](https://azure.microsoft.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🚀 Quick Deploy to Azure

### Prerequisites

- Azure subscription with Contributor role
- Azure CLI >= 2.50.0
- Docker >= 24.0
- Git

### One-Command Deployment

```bash
# Clone repository
git clone https://github.com/ELANGKATHIR11/AGRISENSEFULL-STACK.git
cd AGRISENSEFULL-STACK/AGRISENSEFULL-STACK

# Deploy to Azure (development)
.\infrastructure\azure\deploy.ps1 -Environment dev -ResourceGroup agrisense-dev-rg

# Deploy to Azure (production)
.\infrastructure\azure\deploy.ps1 -Environment prod -ResourceGroup agrisense-prod-rg
```

---

## 📋 What's Deployed

### Azure Resources Created

| Service | Purpose | SKU |
|---------|---------|-----|
| **App Service (Linux)** | Backend API (Python 3.12.10 + FastAPI) | B1 (dev) / P1V2 (prod) |
| **Static Web App** | Frontend (React + Vite) | Free (dev) / Standard (prod) |
| **Container Registry** | Docker images | Basic (dev) / Standard (prod) |
| **Cosmos DB** | NoSQL database (serverless) | Serverless |
| **Storage Account** | ML models & logs | Standard LRS/ZRS |
| **Key Vault** | Secrets management | Standard |
| **Application Insights** | Monitoring & diagnostics | Pay-as-you-go |
| **Log Analytics** | Centralized logging | PerGB2018 |

### Architecture

```
Internet
   │
   ├──▶ Azure Static Web App (Frontend)
   │         │
   │         └──▶ Azure App Service (Backend API)
   │                   │
   │                   ├──▶ Azure Cosmos DB (Sensor data)
   │                   ├──▶ Azure Blob Storage (ML models)
   │                   ├──▶ Azure Key Vault (Secrets)
   │                   └──▶ Application Insights (Telemetry)
   │
   └──▶ Azure Container Registry (Docker images)
```

---

## 🔧 Configuration

### Required GitHub Secrets

Set these in GitHub Settings → Secrets and variables → Actions:

| Secret Name | Description |
|-------------|-------------|
| `AZURE_CREDENTIALS` | Service Principal JSON |
| `AZURE_SUBSCRIPTION_ID` | Azure Subscription ID |
| `AZURE_CONTAINER_REGISTRY` | ACR name |
| `AZURE_ACR_PASSWORD` | ACR admin password |
| `AZURE_BACKEND_APP_NAME` | Backend App Service name |
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | Static Web App token |
| `VITE_API_URL` | Backend API URL for frontend |

**See**: [infrastructure/azure/SECRETS_CONFIGURATION.md](./infrastructure/azure/SECRETS_CONFIGURATION.md)

### Environment Variables

Copy `.env.azure.dev.example` or `.env.azure.prod.example`:

```bash
cp .env.azure.dev.example .env.azure.dev
# Edit .env.azure.dev with your Azure resource names
```

---

## 📚 Documentation

- **[Deployment Guide](./infrastructure/azure/DEPLOYMENT_GUIDE.md)** - Complete deployment walkthrough
- **[Secrets Configuration](./infrastructure/azure/SECRETS_CONFIGURATION.md)** - GitHub Secrets setup
- **[Architecture Diagram](./ARCHITECTURE_DIAGRAM.md)** - System architecture
- **[Python 3.12.10 Guide](./PYTHON_312_QUICK_REFERENCE.md)** - Python optimization details

---

## 🔄 CI/CD Pipeline

GitHub Actions workflow automatically:

1. ✅ Builds and tests backend (Python 3.12.10)
2. ✅ Builds and tests frontend (React + TypeScript)
3. ✅ Builds Docker images
4. ✅ Pushes to Azure Container Registry
5. ✅ Deploys infrastructure (Bicep)
6. ✅ Deploys backend to App Service
7. ✅ Deploys frontend to Static Web App
8. ✅ Runs smoke tests

**Trigger**: Push to `main`, `staging`, or `develop` branches

---

## 🧪 Testing Deployed Application

### Backend Health Checks

```bash
# Health check
curl https://<backend-app-name>.azurewebsites.net/health

# Ready check
curl https://<backend-app-name>.azurewebsites.net/ready

# API documentation
https://<backend-app-name>.azurewebsites.net/docs
```

### Frontend

```bash
# Open in browser
https://<frontend-app-name>.azurestaticapps.net
```

---

## 💰 Cost Estimate

### Development Environment (~$50-70/month)

- App Service Plan B1: $13/month
- Container Registry Basic: $5/month
- Cosmos DB Serverless: ~$10/month
- Storage Account: ~$2/month
- Static Web App Free: $0/month
- Application Insights: ~$5/month

### Production Environment (~$200-300/month)

- App Service Plan P1V2: $73/month
- Container Registry Standard: $20/month
- Cosmos DB with autoscale: ~$50/month
- Storage Account + CDN: ~$20/month
- Static Web App Standard: $9/month
- Application Insights: ~$30/month

**Reduce costs**:
- Stop dev/staging environments when not in use
- Use reserved capacity for production
- Enable Cosmos DB TTL for auto-cleanup

---

## 🔐 Security

### Built-in Security Features

- ✅ **HTTPS-only** - All traffic encrypted
- ✅ **Managed identities** - Passwordless authentication
- ✅ **Key Vault** - Secure secrets storage
- ✅ **RBAC** - Role-based access control
- ✅ **Network security** - Private endpoints option
- ✅ **Continuous backup** - Cosmos DB point-in-time restore

### Security Checklist

- [ ] Rotate secrets regularly
- [ ] Enable Azure Defender for Cloud
- [ ] Configure firewall rules for Cosmos DB
- [ ] Use private endpoints for production
- [ ] Enable WAF for Static Web App
- [ ] Set up Azure Policy for compliance

---

## 📊 Monitoring

### Application Insights Dashboards

Access monitoring at: Azure Portal → Application Insights → `agrisense-<env>-insights`

**Pre-configured queries**:
- Request failures and exceptions
- Performance metrics (p95, p99)
- Custom events and traces
- Dependency call durations

### Alerts

Set up alerts for:
- Backend response time > 2s
- Error rate > 5%
- Cosmos DB RU consumption > 80%
- Storage account capacity > 80%

---

## 🛠 Troubleshooting

### Backend Not Starting

```bash
# Check logs
az webapp log tail --name <backend-app-name> --resource-group <rg-name>

# View deployment logs
az webapp log deployment show --name <backend-app-name> --resource-group <rg-name>

# SSH into container
az webapp ssh --name <backend-app-name> --resource-group <rg-name>
```

### Frontend Not Loading

```bash
# Check Static Web App logs
az staticwebapp logs --name <frontend-app-name> --resource-group <rg-name>

# Verify build output
cd agrisense_app/frontend/farm-fortune-frontend-main
npm run build
ls dist/  # Should have index.html
```

### Database Connection Issues

```bash
# Test Cosmos DB connection
az cosmosdb show --name <cosmos-account-name> --resource-group <rg-name>

# Check firewall rules
az cosmosdb show --name <cosmos-account-name> --resource-group <rg-name> \
  --query "ipRules"
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

---

## 📞 Support

- **Documentation**: [/documentation/](./documentation/)
- **Issues**: [GitHub Issues](https://github.com/ELANGKATHIR11/AGRISENSEFULL-STACK/issues)
- **Azure Support**: [Azure Portal](https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade)

---

**Deployed with**: Azure Container Apps | Python 3.12.10 | React 18.3.1  
**Last Updated**: December 6, 2025
