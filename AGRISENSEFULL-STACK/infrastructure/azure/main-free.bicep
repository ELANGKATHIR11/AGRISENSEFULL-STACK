// ===================================================================
// AgriSense Azure Free Tier Deployment
// Simplified template for dynamic web app deployment
// ===================================================================

@description('Azure region for resources')
param location string = resourceGroup().location

@description('Project name prefix')
param projectName string = 'agrisense'

@description('Unique suffix for globally unique names')
param uniqueSuffix string = uniqueString(resourceGroup().id)

// ===================================================================
// Variables
// ===================================================================

var resourcePrefix = '${projectName}-free'
var appServicePlanName = '${resourcePrefix}-plan'
var webAppName = '${resourcePrefix}-app-${uniqueSuffix}'
var cosmosDbAccountName = '${resourcePrefix}-cosmos-${uniqueSuffix}'
var storageAccountName = replace('${projectName}free${uniqueSuffix}', '-', '')
var appInsightsName = '${resourcePrefix}-insights'

var tags = {
  Environment: 'free'
  Project: 'AgriSense'
  ManagedBy: 'Bicep'
  DeployedBy: 'Copilot'
}

// ===================================================================
// App Service Plan - F1 Free Tier
// ===================================================================

resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanName
  location: location
  tags: tags
  sku: {
    name: 'F1'
    tier: 'Free'
    size: 'F1'
    capacity: 1
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

// ===================================================================
// Web App - Python Backend + React Frontend Served Together
// ===================================================================

resource webApp 'Microsoft.Web/sites@2023-01-01' = {
  name: webAppName
  location: location
  tags: tags
  kind: 'app,linux'
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.12'
      alwaysOn: false // F1 tier doesn't support always on
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      http20Enabled: true
      appSettings: [
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'AGRISENSE_DISABLE_ML'
          value: '1'
        }
        {
          name: 'WORKERS'
          value: '1'
        }
        {
          name: 'LOG_LEVEL'
          value: 'WARNING'
        }
        {
          name: 'ENABLE_CACHE'
          value: 'true'
        }
        {
          name: 'CACHE_TTL'
          value: '3600'
        }
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'false'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
      ]
      cors: {
        allowedOrigins: [
          '*'
        ]
        supportCredentials: false
      }
    }
  }
}

// ===================================================================
// Cosmos DB - Free Tier (1000 RU/s, 25GB)
// ===================================================================

resource cosmosDbAccount 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' = {
  name: cosmosDbAccountName
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    enableFreeTier: true
    enableAutomaticFailover: false
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
  }
}

// Cosmos DB Database
resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-11-15' = {
  parent: cosmosDbAccount
  name: 'AgriSense'
  properties: {
    resource: {
      id: 'AgriSense'
    }
  }
}

// Container: SensorData
resource sensorDataContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: cosmosDatabase
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
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
      }
    }
  }
}

// Container: Recommendations
resource recommendationsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: cosmosDatabase
  name: 'Recommendations'
  properties: {
    resource: {
      id: 'Recommendations'
      partitionKey: {
        paths: ['/fieldId']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
      }
    }
  }
}

// Container: ChatHistory
resource chatHistoryContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: cosmosDatabase
  name: 'ChatHistory'
  properties: {
    resource: {
      id: 'ChatHistory'
      partitionKey: {
        paths: ['/userId']
        kind: 'Hash'
      }
      defaultTtl: 2592000 // 30 days
      indexingPolicy: {
        indexingMode: 'consistent'
      }
    }
  }
}

// ===================================================================
// Storage Account - For ML models and logs
// ===================================================================

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

// Blob containers
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

// ===================================================================
// Application Insights
// ===================================================================

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    RetentionInDays: 30
    IngestionMode: 'ApplicationInsights'
  }
}

// ===================================================================
// Outputs
// ===================================================================

output webAppUrl string = 'https://${webApp.properties.defaultHostName}'
output webAppName string = webApp.name
output cosmosDbEndpoint string = cosmosDbAccount.properties.documentEndpoint
output cosmosDbName string = cosmosDatabase.name
output storageAccountName string = storageAccount.name
output appInsightsConnectionString string = appInsights.properties.ConnectionString
output resourceGroupName string = resourceGroup().name
