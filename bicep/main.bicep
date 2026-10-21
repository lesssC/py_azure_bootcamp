
targetScope = 'subscription'

@description('Region de Azure para los recursos.')
param location string = 'westus'

param resourceGroupName string = 'rg-redsosten-student'
param sqlAdminLogin string = 'adminredsosten'

@secure()
param sqlAdminPassword string

param openAiDeployment string = 'gpt-4.1-mini'

param entraAdminObjectId string = ''
param entraAdminLogin string = ''

@description('Imagen inicial para la validacion de infraestructura.')
param containerImage string
param containerTargetPort int = 80
@description('Numero minimo de replicas para evitar pantallas de arranque en frio.')
param containerMinReplicas int = 1

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
}

module infrastructure 'modules/resources.bicep' = {
  name: 'redsosten-infrastructure'
  scope: rg
  params: {
    location: location
    sqlAdminLogin: sqlAdminLogin
    sqlAdminPassword: sqlAdminPassword
    openAiDeployment: openAiDeployment
    entraAdminObjectId: entraAdminObjectId
    entraAdminLogin: entraAdminLogin
    containerImage: containerImage
    containerTargetPort: containerTargetPort
    containerMinReplicas: containerMinReplicas
  }
}

output containerAppUrl string = infrastructure.outputs.containerAppUrl
output sqlServerName string = infrastructure.outputs.sqlServerName
output acrLoginServer string = infrastructure.outputs.acrLoginServer
output openAiEndpoint string = infrastructure.outputs.openAiEndpoint
output documentIntelligenceEndpoint string = infrastructure.outputs.documentIntelligenceEndpoint
output keyVaultName string = infrastructure.outputs.keyVaultName
output managedIdentityPrincipalId string = infrastructure.outputs.managedIdentityPrincipalId
