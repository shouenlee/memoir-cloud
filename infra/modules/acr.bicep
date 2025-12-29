// Azure Container Registry module

@description('Name of the container registry')
param name string

@description('Location for the resource')
param location string

@description('SKU for the container registry')
@allowed(['Basic', 'Standard', 'Premium'])
param sku string = 'Basic'

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: name
  location: location
  sku: {
    name: sku
  }
  properties: {
    adminUserEnabled: true
    publicNetworkAccess: 'Enabled'
  }
}

output id string = acr.id
output name string = acr.name
output loginServer string = acr.properties.loginServer
output adminUsername string = acr.listCredentials().username
#disable-next-line outputs-should-not-contain-secrets
output adminPassword string = acr.listCredentials().passwords[0].value
