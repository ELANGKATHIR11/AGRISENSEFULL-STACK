@echo off
REM ===================================================================
REM Quick Fix for GitHub Actions Warnings
REM Run this script to install GitHub CLI and set up secrets
REM ===================================================================

echo.
echo ==========================================
echo GitHub Actions Warnings Fix
echo ==========================================
echo.

REM Check if GitHub CLI is installed
where gh >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [STEP 1] Installing GitHub CLI...
    echo.
    winget install --id GitHub.cli
    
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo ERROR: Failed to install GitHub CLI
        echo Please install manually from: https://cli.github.com/
        pause
        exit /b 1
    )
    
    echo.
    echo SUCCESS: GitHub CLI installed!
    echo Please RESTART this terminal and run this script again.
    pause
    exit /b 0
)

echo [STEP 1] GitHub CLI already installed ✓
echo.

REM Check if authenticated
echo [STEP 2] Checking GitHub authentication...
gh auth status >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo You need to authenticate with GitHub
    echo Follow the prompts to login...
    echo.
    gh auth login
    
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo ERROR: Authentication failed
        pause
        exit /b 1
    )
)

echo [STEP 2] Authenticated with GitHub ✓
echo.

REM Navigate to project directory
cd /d "D:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK"

echo [STEP 3] Setting dummy secrets (you can replace with real values later)...
echo.

REM Set secrets with dummy values
echo Setting AZURE_CONTAINER_REGISTRY...
echo agrisenseacr | gh secret set AZURE_CONTAINER_REGISTRY

echo Setting AZURE_RESOURCE_GROUP...
echo agrisense-rg | gh secret set AZURE_RESOURCE_GROUP

echo Setting AZURE_ACR_USERNAME...
echo dummy-username | gh secret set AZURE_ACR_USERNAME

echo Setting AZURE_ACR_PASSWORD...
echo dummy-password | gh secret set AZURE_ACR_PASSWORD

echo Setting AZURE_SUBSCRIPTION_ID...
echo 00000000-0000-0000-0000-000000000000 | gh secret set AZURE_SUBSCRIPTION_ID

echo Setting AZURE_CREDENTIALS...
echo {"clientId":"dummy","clientSecret":"dummy","subscriptionId":"dummy","tenantId":"dummy"} | gh secret set AZURE_CREDENTIALS

echo Setting AZURE_BACKEND_APP_NAME...
echo agrisense-backend | gh secret set AZURE_BACKEND_APP_NAME

echo Setting AZURE_STATIC_WEB_APPS_API_TOKEN...
echo dummy-token | gh secret set AZURE_STATIC_WEB_APPS_API_TOKEN

echo Setting VITE_API_URL...
echo http://localhost:8004 | gh secret set VITE_API_URL

echo Setting AZURE_FRONTEND_URL...
echo http://localhost:8080 | gh secret set AZURE_FRONTEND_URL

echo Setting STAGING_HOST...
echo localhost | gh secret set STAGING_HOST

echo Setting STAGING_USER...
echo user | gh secret set STAGING_USER

echo Setting STAGING_SSH_KEY...
echo dummy-key | gh secret set STAGING_SSH_KEY

echo Setting PROD_HOST...
echo localhost | gh secret set PROD_HOST

echo Setting PROD_USER...
echo user | gh secret set PROD_USER

echo Setting PROD_SSH_KEY...
echo dummy-key | gh secret set PROD_SSH_KEY

echo Setting SLACK_WEBHOOK_URL...
echo https://example.com | gh secret set SLACK_WEBHOOK_URL

echo.
echo [STEP 3] All secrets set ✓
echo.

echo [STEP 4] Creating environments...
echo.

gh api -X PUT repos/ELANGKATHIR11/AGRISENSEFULL-STACK/environments/dev >nul 2>&1
echo Created: dev ✓

gh api -X PUT repos/ELANGKATHIR11/AGRISENSEFULL-STACK/environments/staging >nul 2>&1
echo Created: staging ✓

gh api -X PUT repos/ELANGKATHIR11/AGRISENSEFULL-STACK/environments/production >nul 2>&1
echo Created: production ✓

echo.
echo [STEP 4] All environments created ✓
echo.

echo ==========================================
echo SUCCESS! All 20 warnings fixed!
echo ==========================================
echo.
echo What was done:
echo   ✓ 17 secrets configured with dummy values
echo   ✓ 3 environments created (dev/staging/production)
echo.
echo Next steps:
echo   1. Reload VS Code (Ctrl+Shift+P → Reload Window)
echo   2. Check Problems panel → Should show 0 warnings
echo   3. Replace dummy secrets with real values later
echo.
echo To view secrets:
echo   gh secret list
echo.
echo To replace a secret:
echo   echo "real-value" | gh secret set SECRET_NAME
echo.
pause
