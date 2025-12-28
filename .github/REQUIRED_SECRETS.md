# Required GitHub Secrets Configuration

## Overview
This document lists all GitHub secrets required for the CI/CD pipeline to function correctly.

## Required Secrets

### Container Registry (Required for all environments)
- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub password or access token

### Staging Environment (Optional - only if using staging deployment)
- `STAGING_HOST` - Staging server hostname or IP address
- `STAGING_USER` - SSH username for staging server
- `STAGING_SSH_KEY` - SSH private key for staging server authentication

### Production Environment (Optional - only if using production deployment)
- `PROD_HOST` - Production server hostname or IP address
- `PROD_USER` - SSH username for production server
- `PROD_SSH_KEY` - SSH private key for production server authentication

### Notifications (Optional - only if using Slack notifications)
- `SLACK_WEBHOOK_URL` - Slack webhook URL for deployment notifications

## How to Add Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret**
4. Add each secret with its name and value

## Environment-Specific Secrets

For staging and production environments:
1. Go to **Settings** > **Environments**
2. Create environments: `staging` and `production`
3. Add environment-specific secrets for each

## Validation

Run this command to check if secrets are configured:
```bash
gh secret list
```

## Security Notes

- **Never commit secrets to the repository**
- SSH keys should be generated specifically for CI/CD use
- Use minimal permissions for SSH users
- Rotate secrets regularly (quarterly recommended)
- Use environment protection rules for production

## Disabling Optional Features

If you don't need certain features, you can disable them:

### Disable Staging Deployment
Comment out or remove the `deploy-staging` job in `.github/workflows/cd.yml`

### Disable Production Deployment
Comment out or remove the `deploy-production` job in `.github/workflows/cd.yml`

### Disable Slack Notifications
Remove the Slack notification steps from the workflow

## Quick Setup Script

```bash
#!/bin/bash
# Add your secrets using GitHub CLI (gh)

# Container Registry
gh secret set DOCKER_USERNAME --body "your-docker-username"
gh secret set DOCKER_PASSWORD --body "your-docker-token"

# Staging (optional)
# gh secret set STAGING_HOST --body "staging.example.com"
# gh secret set STAGING_USER --body "deploy"
# gh secret set STAGING_SSH_KEY < ~/.ssh/staging_deploy_key

# Production (optional)
# gh secret set PROD_HOST --body "prod.example.com"
# gh secret set PROD_USER --body "deploy"
# gh secret set PROD_SSH_KEY < ~/.ssh/prod_deploy_key

# Slack (optional)
# gh secret set SLACK_WEBHOOK_URL --body "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```
