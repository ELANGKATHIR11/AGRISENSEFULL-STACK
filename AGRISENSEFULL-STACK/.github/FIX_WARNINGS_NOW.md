# 🚀 Fix GitHub Actions Warnings - 3 Methods

## Current Warnings: 20
- 17 Secret warnings (secrets not configured)
- 3 Environment warnings (environments not created)

## ⚡ METHOD 1: GitHub Web Interface (EASIEST - No Installation Required)

### Step 1: Install GitHub CLI (One-Time Setup)
```powershell
# Open PowerShell as Administrator and run:
winget install --id GitHub.cli

# Or download from: https://cli.github.com/
```

### Step 2: Authenticate
```powershell
gh auth login
# Follow the prompts:
# - Choose: GitHub.com
# - Choose: HTTPS
# - Authenticate with browser: Yes
# Login with your GitHub credentials
```

### Step 3: Set Secrets (Copy & Paste Each Command)
```powershell
# Navigate to project directory
cd "D:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK"

# Azure Secrets
echo "agrisenseacr" | gh secret set AZURE_CONTAINER_REGISTRY
echo "agrisense-rg" | gh secret set AZURE_RESOURCE_GROUP
echo "your-acr-username" | gh secret set AZURE_ACR_USERNAME
echo "your-acr-password" | gh secret set AZURE_ACR_PASSWORD
echo "your-subscription-id" | gh secret set AZURE_SUBSCRIPTION_ID
echo '{"clientId":"xxx","clientSecret":"xxx","subscriptionId":"xxx","tenantId":"xxx"}' | gh secret set AZURE_CREDENTIALS
echo "agrisense-backend-dev" | gh secret set AZURE_BACKEND_APP_NAME
echo "your-static-web-app-token" | gh secret set AZURE_STATIC_WEB_APPS_API_TOKEN
echo "https://agrisense-backend-dev.azurewebsites.net" | gh secret set VITE_API_URL
echo "https://agrisense.azurestaticapps.net" | gh secret set AZURE_FRONTEND_URL

# SSH Secrets (optional)
echo "staging.example.com" | gh secret set STAGING_HOST
echo "deploy" | gh secret set STAGING_USER
echo "-----BEGIN RSA PRIVATE KEY-----..." | gh secret set STAGING_SSH_KEY
echo "prod.example.com" | gh secret set PROD_HOST
echo "deploy" | gh secret set PROD_USER
echo "-----BEGIN RSA PRIVATE KEY-----..." | gh secret set PROD_SSH_KEY

# Slack (optional)
echo "https://hooks.slack.com/services/YOUR/WEBHOOK" | gh secret set SLACK_WEBHOOK_URL
```

### Step 4: Create Environments
```powershell
gh api -X PUT repos/ELANGKATHIR11/AGRISENSEFULL-STACK/environments/dev
gh api -X PUT repos/ELANGKATHIR11/AGRISENSEFULL-STACK/environments/staging
gh api -X PUT repos/ELANGKATHIR11/AGRISENSEFULL-STACK/environments/production
```

### Step 5: Verify
```powershell
gh secret list
```

**Result**: All 20 warnings will disappear! ✅

---

## 🖱️ METHOD 2: GitHub Website (No CLI Required)

### Step 1: Go to Repository Settings
1. Open browser: https://github.com/ELANGKATHIR11/AGRISENSEFULL-STACK
2. Click **Settings** tab (top right)
3. Click **Secrets and variables** → **Actions** (left sidebar)

### Step 2: Add Each Secret
For each secret below:
1. Click **New repository secret**
2. Copy the **Name** exactly
3. Enter your **Value**
4. Click **Add secret**

#### Required Secrets:

| Name | Example Value |
|------|---------------|
| `AZURE_CONTAINER_REGISTRY` | `agrisenseacr` |
| `AZURE_RESOURCE_GROUP` | `agrisense-rg` |
| `AZURE_ACR_USERNAME` | Your ACR username |
| `AZURE_ACR_PASSWORD` | Your ACR password |
| `AZURE_SUBSCRIPTION_ID` | `00000000-0000-0000-0000-000000000000` |
| `AZURE_CREDENTIALS` | `{"clientId":"...","clientSecret":"..."}` |
| `AZURE_BACKEND_APP_NAME` | `agrisense-backend-dev` |
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | Your token |
| `VITE_API_URL` | `https://agrisense-backend-dev.azurewebsites.net` |
| `AZURE_FRONTEND_URL` | `https://agrisense.azurestaticapps.net` |
| `STAGING_HOST` | `staging.example.com` (optional) |
| `STAGING_USER` | `deploy` (optional) |
| `STAGING_SSH_KEY` | Your SSH private key (optional) |
| `PROD_HOST` | `prod.example.com` (optional) |
| `PROD_USER` | `deploy` (optional) |
| `PROD_SSH_KEY` | Your SSH private key (optional) |
| `SLACK_WEBHOOK_URL` | Slack webhook (optional) |

### Step 3: Create Environments
1. Go to **Settings** → **Environments** (left sidebar)
2. Click **New environment**
3. Enter name: `dev` → Click **Configure environment**
4. Repeat for: `staging`, `production`

**Result**: All 20 warnings will disappear! ✅

---

## 🤖 METHOD 3: Run Automated Script (RECOMMENDED)

### Step 1: Install GitHub CLI
```powershell
winget install --id GitHub.cli
```

### Step 2: Authenticate
```powershell
gh auth login
```

### Step 3: Run the Setup Script
```powershell
cd "D:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK\.github"
.\setup-secrets.ps1
```

The script will:
- ✅ Prompt for each secret value
- ✅ Auto-fetch Azure values (if logged in with `az login`)
- ✅ Set all secrets in GitHub
- ✅ Create all environments
- ✅ Verify configuration

**Result**: All 20 warnings will disappear! ✅

---

## 🎯 QUICK START: Test with Dummy Values

If you just want to eliminate the warnings for development:

```powershell
# Install GitHub CLI
winget install --id GitHub.cli

# Authenticate
gh auth login

# Set dummy values (replace with real values later)
cd "D:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK"

gh secret set AZURE_CONTAINER_REGISTRY --body "agrisenseacr"
gh secret set AZURE_RESOURCE_GROUP --body "agrisense-rg"
gh secret set AZURE_ACR_USERNAME --body "dummy-username"
gh secret set AZURE_ACR_PASSWORD --body "dummy-password"
gh secret set AZURE_SUBSCRIPTION_ID --body "00000000-0000-0000-0000-000000000000"
gh secret set AZURE_CREDENTIALS --body '{"clientId":"dummy","clientSecret":"dummy","subscriptionId":"dummy","tenantId":"dummy"}'
gh secret set AZURE_BACKEND_APP_NAME --body "agrisense-backend"
gh secret set AZURE_STATIC_WEB_APPS_API_TOKEN --body "dummy-token"
gh secret set VITE_API_URL --body "http://localhost:8004"
gh secret set AZURE_FRONTEND_URL --body "http://localhost:8080"
gh secret set STAGING_HOST --body "localhost"
gh secret set STAGING_USER --body "user"
gh secret set STAGING_SSH_KEY --body "dummy-key"
gh secret set PROD_HOST --body "localhost"
gh secret set PROD_USER --body "user"
gh secret set PROD_SSH_KEY --body "dummy-key"
gh secret set SLACK_WEBHOOK_URL --body "https://example.com"

# Create environments
gh api -X PUT repos/ELANGKATHIR11/AGRISENSEFULL-STACK/environments/dev
gh api -X PUT repos/ELANGKATHIR11/AGRISENSEFULL-STACK/environments/staging
gh api -X PUT repos/ELANGKATHIR11/AGRISENSEFULL-STACK/environments/production

# Verify
gh secret list
```

**Result**: All 20 warnings gone! You can replace with real values later.

---

## 📋 How to Get Real Azure Values

### AZURE_SUBSCRIPTION_ID
```powershell
az login
az account show --query id -o tsv
```

### AZURE_CREDENTIALS
```powershell
$subId = az account show --query id -o tsv
az ad sp create-for-rbac --name "agrisense-sp" --role contributor --scopes "/subscriptions/$subId" --sdk-auth
```

### AZURE_ACR_USERNAME & AZURE_ACR_PASSWORD
```powershell
az acr credential show --name agrisenseacr --query username -o tsv
az acr credential show --name agrisenseacr --query "passwords[0].value" -o tsv
```

### AZURE_STATIC_WEB_APPS_API_TOKEN
1. Go to Azure Portal
2. Navigate to your Static Web App
3. Click **Deployment tokens** → Copy the token

---

## ❓ FAQ

### Q: Why can't VS Code fix these warnings automatically?
**A**: These are secrets stored in GitHub's secure vault. VS Code can only read them, not write them. You must configure them via GitHub's interface or API.

### Q: Will the workflows work without configuring secrets?
**A**: The workflows will run but fail at deployment steps that require secrets. Build/test steps will work fine.

### Q: Do I need all 17 secrets?
**A**: No! You only need:
- **For local development**: None
- **For Azure deployment**: 10 Azure secrets
- **For SSH deployment**: 6 SSH secrets (optional)
- **For Slack notifications**: 1 Slack secret (optional)

### Q: Can I test locally without secrets?
**A**: Yes! Just use the `.env.example` file:
```powershell
Copy-Item .env.example .env.local
# Edit .env.local with your values
```

### Q: How long does it take to fix?
**A**: 
- Method 1 (CLI): 5 minutes
- Method 2 (Web): 10 minutes
- Method 3 (Script): 5 minutes

---

## ✅ Verification Checklist

After configuration:
- [ ] Run: `gh secret list` - Should show 17 secrets
- [ ] Check VS Code Problems panel - Should show 0 warnings
- [ ] Go to repository Settings > Environments - Should see dev/staging/production
- [ ] Trigger a workflow manually - Should start without errors
- [ ] Review workflow logs - Secrets should be accessible (shown as ***)

---

## 🆘 Troubleshooting

### GitHub CLI not recognized
```powershell
# Restart PowerShell after installation
# Or add to PATH manually
```

### "Secret not found" error in workflow
- Check secret name spelling (case-sensitive)
- Verify secret is at repository level, not organization level
- Re-set the secret

### Environment warnings still showing
- Refresh VS Code (Ctrl+Shift+P → "Reload Window")
- Verify environments exist in GitHub Settings
- Check workflow file references correct environment names

---

## 🎉 Success!

Once configured, you'll see:
- ✅ 0 warnings in VS Code Problems panel
- ✅ All secrets visible in `gh secret list`
- ✅ All environments visible in GitHub Settings
- ✅ Workflows can run successfully

**Choose your method above and get started!** 🚀
