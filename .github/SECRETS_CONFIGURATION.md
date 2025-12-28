# GitHub Secrets Configuration Guide

## Required Secrets for CI/CD Pipeline

To enable the complete CD pipeline, configure the following secrets in your GitHub repository:

### Navigation
**Settings** → **Secrets and variables** → **Actions** → **New repository secret**

### Required Secrets

#### Staging Environment
- `STAGING_HOST` - IP address or hostname of staging server
- `STAGING_USER` - SSH username for staging deployment
- `STAGING_SSH_KEY` - Private SSH key for staging authentication

#### Production Environment
- `PROD_HOST` - IP address or hostname of production server
- `PROD_USER` - SSH username for production deployment
- `PROD_SSH_KEY` - Private SSH key for production authentication

#### Notifications
- `SLACK_WEBHOOK_URL` - Slack webhook URL for deployment notifications (optional)

#### Database
- `POSTGRES_PASSWORD` - PostgreSQL database password

### Example Values

```bash
STAGING_HOST=staging.agrisense.example.com
STAGING_USER=deploy
STAGING_SSH_KEY=-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
...
-----END OPENSSH PRIVATE KEY-----

PROD_HOST=agrisense.example.com
PROD_USER=deploy
PROD_SSH_KEY=<production-ssh-private-key>

SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX

POSTGRES_PASSWORD=SecurePassword123!
```

### Notes

1. **Environment warnings**: The "Context access might be invalid" warnings are expected until secrets are configured
2. **Environment configuration**: Environments `staging` and `production` must be configured in GitHub repository settings
3. **SSH Keys**: Generate separate SSH key pairs for staging and production
4. **Slack webhook**: Create a Slack app and incoming webhook at api.slack.com/apps

### Configuring GitHub Environments

1. Go to **Settings** → **Environments**
2. Click **New environment**
3. Create `staging` and `production` environments
4. Configure deployment protection rules (optional):
   - Required reviewers for production
   - Wait timer before deployment
   - Deployment branches (limit to `main` branch)

### Testing Without Secrets

The workflow will fail at deployment steps if secrets are not configured. To test:

1. **CI only**: Push to feature branches (CI workflow runs without secrets)
2. **Skip deployment**: Comment out deployment jobs in cd.yml temporarily
3. **Local testing**: Use docker-compose locally as documented in QUICK_START_DEPLOYMENT.md

### SSH Key Generation

```bash
# Generate SSH key pair
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/agrisense_deploy

# Add public key to target server
ssh-copy-id -i ~/.ssh/agrisense_deploy.pub user@server

# Copy private key content for GitHub secret
cat ~/.ssh/agrisense_deploy
```

## Slack Webhook Setup (Optional)

1. Go to https://api.slack.com/apps
2. Create New App → From scratch
3. Name: "AgriSense Deployment Bot"
4. Select workspace
5. **Incoming Webhooks** → Activate
6. **Add New Webhook to Workspace**
7. Select channel (e.g., #deployments)
8. Copy webhook URL and save as `SLACK_WEBHOOK_URL` secret

For more details, see: https://api.slack.com/messaging/webhooks
