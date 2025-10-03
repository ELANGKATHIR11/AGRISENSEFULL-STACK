targetScope = 'resourceGroup'

@description('Azure region for resources')
param location string

@description('Name of the Container Apps environment')
param environmentName string

@description('Name of the Container App')
param containerAppName string

@description('Container port the app listens on')
param containerPort int = 8004

@description('Allowed CORS origins for the API')
param allowedOrigins string = '*'

@description('Allow insecure ingress (HTTP) alongside HTTPS')
param ingressAllowInsecure bool = true

@description('SKU for Azure Container Registry')
param containerRegistrySku string = 'Basic'

@description('Tag for azd env name')
param azdEnvName string = ''

var nameSuffix = uniqueString(resourceGroup().id)

// Log Analytics for Container Apps
resource law 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'log-${nameSuffix}'
  location: location
  properties: {
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
  tags: {
    'azd-env-name': azdEnvName
  }
}

// Container Apps Environment
resource cae 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: environmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: law.properties.customerId
        sharedKey: law.listKeys().primarySharedKey
      }
    }
  }
  tags: {
    'azd-env-name': azdEnvName
  }
}

// Azure Container Registry for image storage
resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: 'acr${nameSuffix}'
  location: location
  sku: {
    name: containerRegistrySku
  }
  properties: {
    adminUserEnabled: true
    dataEndpointEnabled: false
  }
  tags: {
    'azd-env-name': azdEnvName
  }
}

// Registry credentials output for deployment (azd will use these)
var acrServer = acr.properties.loginServer

// User-assigned managed identity for pull from ACR (recommended pattern)
resource uami 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'uami-${nameSuffix}'
  location: location
  tags: {
    'azd-env-name': azdEnvName
  }
}

// Grant AcrPull to the identity
resource acrAcrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, 'acrpull', uami.id)
  scope: acr
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '7f951dda-4ed3-4680-a7ca-43fe172d538d'
    )
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// The Container App definition
resource app 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  properties: {
    managedEnvironmentId: cae.id
    configuration: {
      ingress: {
        external: true
        allowInsecure: ingressAllowInsecure
        targetPort: containerPort
      }
      registries: [
        {
          server: acrServer
          identity: uami.id
        }
      ]
      secrets: []
    }
    template: {
      containers: [
        {
          name: 'api'
          image: '${acrServer}/${containerAppName}:latest'
          env: [
            // Key runtime settings
            {
              name: 'ALLOWED_ORIGINS'
              value: allowedOrigins
            }
            {
              name: 'AGRISENSE_DISABLE_ML'
              value: '1'
            }
            {
              name: 'AGRISENSE_DATA_DIR'
              value: '/data'
            }
            {
              name: 'PORT'
              value: string(containerPort)
            }
          ]
          probes: [
            {
              type: 'liveness'
              httpGet: {
                path: '/live'
                port: containerPort
              }
              initialDelaySeconds: 5
              periodSeconds: 10
            }
            {
              type: 'readiness'
              httpGet: {
                path: '/ready'
                port: containerPort
              }
              initialDelaySeconds: 5
              periodSeconds: 10
            }
          ]
          volumeMounts: [
            {
              volumeName: 'data'
              mountPath: '/data'
            }
          ]
        }
      ]
      volumes: [
        // Ephemeral emptyDir for SQLite; swap to Azure Files later if persistence beyond revisions is required
        {
          name: 'data'
          storageType: 'EmptyDir'
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 2
      }
    }
  }
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${uami.id}': {}
    }
  }
  tags: {
    'azd-env-name': azdEnvName
  }
}

output containerAppUrl string = app.properties.configuration.ingress.fqdn
output containerAppName string = app.name
output containerAppResourceId string = app.id
output containerRegistryServer string = acr.properties.loginServer
