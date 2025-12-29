// Static Web App module

@description('Name of the Static Web App')
param name string

@description('Location for the resource')
param location string

@description('SKU for the Static Web App')
@allowed(['Free', 'Standard'])
param sku string = 'Free'

@description('API backend URL for configuration')
param apiUrl string = ''

resource staticWebApp 'Microsoft.Web/staticSites@2023-01-01' = {
  name: name
  location: location
  sku: {
    name: sku
    tier: sku
  }
  properties: {
    stagingEnvironmentPolicy: 'Enabled'
    allowConfigFileUpdates: true
    buildProperties: {
      skipGithubActionWorkflowGeneration: true
    }
  }
}

// Configure app settings if API URL is provided
resource staticWebAppSettings 'Microsoft.Web/staticSites/config@2023-01-01' = if (!empty(apiUrl)) {
  parent: staticWebApp
  name: 'appsettings'
  properties: {
    VITE_API_URL: apiUrl
  }
}

output id string = staticWebApp.id
output name string = staticWebApp.name
output defaultHostname string = staticWebApp.properties.defaultHostname
output url string = 'https://${staticWebApp.properties.defaultHostname}'
#disable-next-line outputs-should-not-contain-secrets
output apiKey string = staticWebApp.listSecrets().properties.apiKey
