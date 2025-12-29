// Container Apps Environment module

@description('Name of the Container Apps Environment')
param name string

@description('Location for the resource')
param location string

@description('Log Analytics Workspace Customer ID')
param logAnalyticsCustomerId string

@description('Log Analytics Workspace Shared Key')
@secure()
param logAnalyticsSharedKey string

resource environment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: name
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsCustomerId
        sharedKey: logAnalyticsSharedKey
      }
    }
    zoneRedundant: false
  }
}

output id string = environment.id
output name string = environment.name
output defaultDomain string = environment.properties.defaultDomain
