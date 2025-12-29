// Storage Account module for photo storage

@description('Name of the storage account')
param name string

@description('Location for the resource')
param location string

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: name
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: true
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}

resource blobServices 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    cors: {
      corsRules: [
        {
          allowedOrigins: ['*']  // Will be restricted to Front Door URL after deployment
          allowedMethods: ['GET', 'HEAD', 'OPTIONS']
          allowedHeaders: ['*']
          exposedHeaders: ['*']
          maxAgeInSeconds: 86400
        }
      ]
    }
  }
}

// Get connection string
var blobEndpoint = storageAccount.properties.primaryEndpoints.blob
var blobEndpointHostname = replace(replace(blobEndpoint, 'https://', ''), '/', '')

output id string = storageAccount.id
output name string = storageAccount.name
output blobEndpoint string = blobEndpoint
output blobEndpointHostname string = blobEndpointHostname
output connectionString string = 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
