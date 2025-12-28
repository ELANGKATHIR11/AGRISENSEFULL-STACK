// ===================================================================
// AgriSense Azure Infrastructure - Main Bicep Template
// Python 3.12.10 + React 18.3.1 Full-Stack Deployment
// ===================================================================

@description('Environment name (dev, staging, prod)')
@allowed(['dev', 'staging', 'prod', 'free'])
param environment string = 'dev'

@description('Azure region for resources')
param location string = resourceGroup().location

@description('Project name prefix')
param projectName string = 'agrisense'

@description('Unique suffix for globally unique names')
param uniqueSuffix string = uniqueString(resourceGroup().id)

@description('Enable Cosmos DB deployment')
param enableCosmosDb bool = true

@description('Enable Application Insights')
param enableAppInsights bool = true

@description('SKU for App Service Plan')
@allowed(['F1', 'B1', 'B2', 'S1', 'S2', 'P1V2', 'P2V2'])
param appServicePlanSku string = environment == 'prod' ? 'P1V2' : environment == 'free' ? 'F1' : 'B1'

@description('Deployment timestamp')
param deploymentTimestamp string = utcNow('yyyyMMddHHmmss')

// ===================================================================
// Variables
// ===================================================================

var resourcePrefix = '${projectName}-${environment}'
var containerRegistryName = replace('${projectName}${environment}${uniqueSuffix}', '-', '')
var cosmosDbAccountName = '${resourcePrefix}-cosmos-${uniqueSuffix}'
var storageAccountName = replace('${projectName}${environment}${uniqueSuffix}', '-', '')
var appServicePlanName = '${resourcePrefix}-plan'
var backendAppName = '${resourcePrefix}-backend-${uniqueSuffix}'
var frontendAppName = '${resourcePrefix}-frontend-${uniqueSuffix}'
var appInsightsName = '${resourcePrefix}-insights'
var keyVaultName = '${resourcePrefix}-kv-${uniqueSuffix}'

var tags = {
  Environment: environment
  Project: 'AgriSense'
  ManagedBy: 'Bicep'
  DeploymentDate: substring(deploymentTimestamp, 0, 8)
}

// ===================================================================
// Container Registry - For Docker images
// ===================================================================

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: containerRegistryName
  location: location
  tags: tags
  sku: {
    name: environment == 'prod' ? 'Standard' : 'Basic'
  }
  properties: {
    adminUserEnabled: true
    publicNetworkAccess: 'Enabled'
    zoneRedundancy: environment == 'prod' ? 'Enabled' : 'Disabled'
  }
}

// ===================================================================
// Storage Account - For ML models, sensor data, logs
// ===================================================================

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: environment == 'prod' ? 'Standard_ZRS' : 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

// Blob containers for ML models and sensor data
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
}

resource mlModelsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'ml-models'
  properties: {
    publicAccess: 'None'
  }
}

resource sensorDataContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'sensor-data'
  properties: {
    publicAccess: 'None'
  }
}

resource logsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'logs'
  properties: {
    publicAccess: 'None'
  }
}

// ===================================================================
// Cosmos DB - For production sensor readings and recommendations
// ===================================================================

resource cosmosDbAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = if (enableCosmosDb) {
  name: cosmosDbAccountName
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: environment == 'prod'
      }
    ]
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
    backupPolicy: {
      type: 'Continuous'
      continuousModeProperties: {
        tier: environment == 'prod' ? 'Continuous7Days' : 'Continuous7Days'
      }
    }
  }
}

resource cosmosDbDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = if (enableCosmosDb) {
  parent: cosmosDbAccount
  name: 'AgriSense'
  properties: {
    resource: {
      id: 'AgriSense'
    }
  }
}

// SensorData container - partition by deviceId
resource sensorDataContainerCosmos 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = if (enableCosmosDb) {
  parent: cosmosDbDatabase
  name: 'SensorData'
  properties: {
    resource: {
      id: 'SensorData'
      partitionKey: {
        paths: ['/deviceId']
        kind: 'Hash'
      }
      defaultTtl: 7776000 // 90 days
      indexingPolicy: {
        automatic: true
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
      }
    }
  }
}

// Recommendations container - partition by fieldId
resource recommendationsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = if (enableCosmosDb) {
  parent: cosmosDbDatabase
  name: 'Recommendations'
  properties: {
    resource: {
      id: 'Recommendations'
      partitionKey: {
        paths: ['/fieldId']
        kind: 'Hash'
      }
      indexingPolicy: {
        automatic: true
        indexingMode: 'consistent'
      }
    }
  }
}

// ChatHistory container - partition by userId
resource chatHistoryContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = if (enableCosmosDb) {
  parent: cosmosDbDatabase
  name: 'ChatHistory'
  properties: {
    resource: {
      id: 'ChatHistory'
      partitionKey: {
        paths: ['/userId']
        kind: 'Hash'
      }
      defaultTtl: 2592000 // 30 days
    }
  }
}

// ===================================================================
// Application Insights - Monitoring and diagnostics
// ===================================================================

resource appInsights 'Microsoft.Insights/components@2020-02-02' = if (enableAppInsights) {
  name: appInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: '${resourcePrefix}-logs'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: environment == 'prod' ? 90 : 30
  }
}

// ===================================================================
// Key Vault - Secrets management
// ===================================================================

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enabledForDeployment: true
    enabledForTemplateDeployment: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// ===================================================================
// App Service Plan - Compute resources
// ===================================================================

resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanName
  location: location
  tags: tags
  sku: {
    name: appServicePlanSku
  }
  kind: 'linux'
  properties: {
    reserved: true
    zoneRedundant: environment == 'prod'
  }
}

// ===================================================================
// Backend App Service - Python 3.12 FastAPI
// ===================================================================

resource backendApp 'Microsoft.Web/sites@2023-01-01' = {
  name: backendAppName
  location: location
  tags: union(tags, { 'hidden-link: /app-insights-resource-id': appInsights.id })
  kind: 'app,linux,container'
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    clientAffinityEnabled: false
    siteConfig: {
      linuxFxVersion: 'DOCKER|${containerRegistry.name}.azurecr.io/${projectName}/backend:latest'
      alwaysOn: environment == 'prod'
      http20Enabled: true
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      healthCheckPath: '/health'
      appSettings: [
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'false'
        }
        {
          name: 'DOCKER_REGISTRY_SERVER_URL'
          value: 'https://${containerRegistry.name}.azurecr.io'
        }
        {
          name: 'DOCKER_REGISTRY_SERVER_USERNAME'
          value: containerRegistry.name
        }
        {
          name: 'DOCKER_REGISTRY_SERVER_PASSWORD'
          value: containerRegistry.listCredentials().passwords[0].value
        }
        {
          name: 'AGRISENSE_ENV'
          value: environment
        }
        {
          name: 'PYTHON_VERSION'
          value: '3.12'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: enableAppInsights && appInsights != null ? appInsights!.properties.ConnectionString : ''
        }
        {
          name: 'AZURE_STORAGE_CONNECTION_STRING'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
        }
        {
          name: 'COSMOS_DB_ENDPOINT'
          value: enableCosmosDb && cosmosDbAccount != null ? cosmosDbAccount!.properties.documentEndpoint : ''
        }
        {
          name: 'COSMOS_DB_KEY'
          value: enableCosmosDb && cosmosDbAccount != null ? cosmosDbAccount!.listKeys().primaryMasterKey : ''
        }
        {
          name: 'KEY_VAULT_URL'
          value: keyVault.properties.vaultUri
        }
      ]
    }
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// ===================================================================
// Frontend Static Web App - React + Vite
// ===================================================================

resource frontendStaticWebApp 'Microsoft.Web/staticSites@2023-01-01' = {
  name: frontendAppName
  location: location
  tags: tags
  sku: {
    name: environment == 'prod' ? 'Standard' : 'Free'
    tier: environment == 'prod' ? 'Standard' : 'Free'
  }
  properties: {
    repositoryUrl: ''
    branch: ''
    buildProperties: {
      appLocation: 'agrisense_app/frontend/farm-fortune-frontend-main'
      apiLocation: ''
      outputLocation: 'dist'
    }
    stagingEnvironmentPolicy: 'Enabled'
    allowConfigFileUpdates: true
    enterpriseGradeCdnStatus: 'Disabled'
  }
}

// Configure Static Web App to proxy API calls to backend
resource frontendAppSettings 'Microsoft.Web/staticSites/config@2023-01-01' = {
  parent: frontendStaticWebApp
  name: 'appsettings'
  properties: {
    VITE_API_URL: 'https://${backendApp.properties.defaultHostName}'
  }
}

// ===================================================================
// RBAC - Grant backend app access to Key Vault
// ===================================================================

resource keyVaultSecretsUserRole 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  scope: subscription()
  name: '4633458b-17de-408a-b874-0445c86b69e6' // Key Vault Secrets User
}

resource backendKeyVaultAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: keyVault
  name: guid(keyVault.id, backendApp.id, keyVaultSecretsUserRole.id)
  properties: {
    roleDefinitionId: keyVaultSecretsUserRole.id
    principalId: backendApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// ===================================================================
// Outputs
// ===================================================================

output resourceGroupName string = resourceGroup().name
output containerRegistryName string = containerRegistry.name
output containerRegistryLoginServer string = containerRegistry.properties.loginServer
output storageAccountName string = storageAccount.name
output cosmosDbEndpoint string = enableCosmosDb && cosmosDbAccount != null ? cosmosDbAccount!.properties.documentEndpoint : ''
output backendAppUrl string = 'https://${backendApp.properties.defaultHostName}'
output frontendAppUrl string = 'https://${frontendStaticWebApp.properties.defaultHostname}'
output keyVaultName string = keyVault.name
output appInsightsInstrumentationKey string = enableAppInsights && appInsights != null ? appInsights!.properties.InstrumentationKey : ''
output appInsightsConnectionString string = enableAppInsights && appInsights != null ? appInsights!.properties.ConnectionString : ''
