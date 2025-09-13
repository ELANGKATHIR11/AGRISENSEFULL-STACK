# Deploy AgriSense to Azure Container Apps

This repo includes Azure infrastructure-as-code (Bicep) and an `azure.yaml` so you can deploy with a single command using the Azure Developer CLI (azd).

## Prerequisites

- Azure account (Azure for Students works)
- Azure CLI and Azure Developer CLI installed
- Docker (for local builds if you prefer)

## One-time setup

1. Sign in
2. Initialize environment (you'll be prompted for an environment name, e.g. `dev`)
3. Provision infra and deploy

    ```powershell
    azd auth login
    azd init -e dev
    azd up
    ```

This provisions:

- Log Analytics workspace
- Azure Container Apps environment
- Azure Container Registry
- User-assigned managed identity with AcrPull
- Container App with public ingress

Outputs will include the public FQDN for the app. Visit:

- <https://YOUR-FQDN/ui>
- <https://YOUR-FQDN/health>

## Configuration

Infra parameters are in `infra/bicep/main.parameters.json`:

- `location`: Azure region (default `eastus`)
- `containerPort`: defaults to 8004
- `allowedOrigins`: CORS origins (default `*`)
- `ingressAllowInsecure`: allow HTTP in addition to HTTPS

Runtime environment variables are set in `infra/bicep/main.bicep` under the container env array. Common vars:

- `ALLOWED_ORIGINS`: comma-separated CORS list
- `AGRISENSE_DISABLE_ML`: set `1` to skip TensorFlow loading (keeps image light)
- `AGRISENSE_DATA_DIR`: `/data` (mounted as EmptyDir by default)
- `PORT`: `8004`

Database path:

- The backend honors `AGRISENSE_DB_PATH` and `AGRISENSE_DATA_DIR`. By default, it writes `sensors.db` to `/data/sensors.db` which is an ephemeral EmptyDir.
- For persistence across revisions, switch the `volumes` section in `infra/bicep/main.bicep` to use an Azure Files volume.

## Make changes and redeploy

- App code changes (no infra change):

    ```powershell
    azd deploy
    ```

- Infra changes (Bicep):

    ```powershell
    azd provision
    azd deploy
    ```

## Optional: secure CORS

Set `allowedOrigins` in `infra/bicep/main.parameters.json` to your frontend origin or leave as `*` during initial testing.

## Troubleshooting

- Check Container App logs:

    ```powershell
    az containerapp logs show --name agrisense-api --resource-group <rg>
    ```

- Verify health endpoints: `/health`, `/ready`
- Ensure the image was pushed to ACR and the managed identity has `AcrPull` on the registry

---

If you prefer App Service instead of Container Apps, we can add an alternate IaC path.
