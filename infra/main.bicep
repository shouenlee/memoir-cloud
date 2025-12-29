// Main deployment template for Memoir Cloud
// Photo gallery application using Container Apps + Static Web Apps

targetScope = 'resourceGroup'

@description('Environment name (dev, staging, prod)')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Location for all resources')
param location string = resourceGroup().location

@description('Base name for resources')
param baseName string = 'memoir-cloud'

@description('Container image tag')
param imageTag string = 'latest'

// Generate unique names
var suffix = uniqueString(resourceGroup().id)
var storageAccountName = 'st${replace(baseName, '-', '')}${take(suffix, 4)}'
var acrName = 'acr${replace(baseName, '-', '')}${take(suffix, 4)}'
var logAnalyticsName = 'log-${baseName}-${environment}'
var appInsightsName = '${baseName}-insights'
var containerAppEnvName = '${baseName}-env'
var containerAppName = '${baseName}-api'
var staticWebAppName = '${baseName}-web'

// Log Analytics Workspace
module logAnalytics 'modules/loganalytics.bicep' = {
  name: 'logAnalytics'
  params: {
    name: logAnalyticsName
    location: location
  }
}

// Application Insights
module appInsights 'modules/insights.bicep' = {
  name: 'appInsights'
  params: {
    name: appInsightsName
    location: location
    logAnalyticsWorkspaceId: logAnalytics.outputs.id
  }
}

// Storage Account for photos
module storage 'modules/storage.bicep' = {
  name: 'storage'
  params: {
    name: storageAccountName
    location: location
  }
}

// Container Registry
module acr 'modules/acr.bicep' = {
  name: 'acr'
  params: {
    name: acrName
    location: location
    sku: environment == 'prod' ? 'Standard' : 'Basic'
  }
}

// Container Apps Environment
module containerAppEnv 'modules/containerapp-env.bicep' = {
  name: 'containerAppEnv'
  params: {
    name: containerAppEnvName
    location: location
    logAnalyticsCustomerId: logAnalytics.outputs.customerId
    logAnalyticsSharedKey: logAnalytics.outputs.sharedKey
  }
}

// Container App (Backend API)
module containerApp 'modules/containerapp.bicep' = {
  name: 'containerApp'
  params: {
    name: containerAppName
    location: location
    environmentId: containerAppEnv.outputs.id
    containerImage: '${acr.outputs.loginServer}/${baseName}-api:${imageTag}'
    registryLoginServer: acr.outputs.loginServer
    registryUsername: acr.outputs.adminUsername
    registryPassword: acr.outputs.adminPassword
    minReplicas: environment == 'prod' ? 1 : 0
    maxReplicas: environment == 'prod' ? 10 : 3
    envVars: [
      {
        name: 'AZURE_STORAGE_CONNECTION_STRING'
        value: storage.outputs.connectionString
      }
      {
        name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
        value: appInsights.outputs.connectionString
      }
      {
        name: 'ENVIRONMENT'
        value: environment
      }
    ]
  }
}

// Static Web App (Frontend)
// Note: Static Web Apps have limited region availability
// Using 'eastus2' which supports Static Web Apps
module staticWebApp 'modules/staticwebapp.bicep' = {
  name: 'staticWebApp'
  params: {
    name: staticWebAppName
    // Static Web Apps only available in certain regions
    location: 'eastus2'
    sku: environment == 'prod' ? 'Standard' : 'Free'
    apiUrl: containerApp.outputs.url
  }
}

// Outputs
output resourceGroupName string = resourceGroup().name
output storageAccountName string = storage.outputs.name
output storageBlobEndpoint string = storage.outputs.blobEndpoint
output acrName string = acr.outputs.name
output acrLoginServer string = acr.outputs.loginServer
output containerAppUrl string = containerApp.outputs.url
output staticWebAppUrl string = staticWebApp.outputs.url
output appInsightsName string = appInsights.outputs.name
output appInsightsConnectionString string = appInsights.outputs.connectionString
