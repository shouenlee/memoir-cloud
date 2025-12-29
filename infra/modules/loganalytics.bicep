// Log Analytics Workspace module

@description('Name of the Log Analytics workspace')
param name string

@description('Location for the resource')
param location string

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: name
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

output id string = logAnalytics.id
output name string = logAnalytics.name
output customerId string = logAnalytics.properties.customerId
#disable-next-line outputs-should-not-contain-secrets
output sharedKey string = logAnalytics.listKeys().primarySharedKey
