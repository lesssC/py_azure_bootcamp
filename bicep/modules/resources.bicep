param location string
param sqlAdminLogin string
@secure()
param sqlAdminPassword string
param openAiDeployment string
param entraAdminObjectId string
param entraAdminLogin string
param containerImage string
param containerTargetPort int
param containerMinReplicas int = 1

// Incluye la región para evitar colisiones con recursos de Cognitive Services
// eliminados recientemente (soft delete) de despliegues anteriores.
var suffix = toLower(uniqueString(resourceGroup().id, location))

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'log-redsosten-${suffix}'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource vnet 'Microsoft.Network/virtualNetworks@2024-01-01' = {
  name: 'vnet-redsosten'
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: ['10.0.0.0/16']
    }
  }
}

resource nsg 'Microsoft.Network/networkSecurityGroups@2024-01-01' = {
  name: 'nsg-redsosten-db'
  location: location
  properties: {
    securityRules: [
      {
        name: 'DenyInternetInbound'
        properties: {
          priority: 100
          protocol: '*'
          access: 'Deny'
          direction: 'Inbound'
          sourceAddressPrefix: 'Internet'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '*'
        }
      }
    ]
  }
}

resource appSubnet 'Microsoft.Network/virtualNetworks/subnets@2024-01-01' = {
  parent: vnet
  name: 'snet-app'
  properties: {
    addressPrefix: '10.0.0.0/23'
    delegations: [
      {
        name: 'container-apps'
        properties: {
          serviceName: 'Microsoft.App/environments'
        }
      }
    ]
  }
}

resource dbSubnet 'Microsoft.Network/virtualNetworks/subnets@2024-01-01' = {
  parent: vnet
  name: 'snet-db'
  properties: {
    addressPrefix: '10.0.2.0/24'
    privateEndpointNetworkPolicies: 'Disabled'
    networkSecurityGroup: {
      id: nsg.id
    }
  }
}

resource sqlServer 'Microsoft.Sql/servers@2023-08-01-preview' = {
  name: 'sql-redsosten-${suffix}'
  location: location
  properties: {
    administratorLogin: sqlAdminLogin
    administratorLoginPassword: sqlAdminPassword
    publicNetworkAccess: 'Disabled'
    minimalTlsVersion: '1.2'
  }
}

resource sqlEntraAdmin 'Microsoft.Sql/servers/administrators@2022-05-01-preview' = if (!empty(entraAdminObjectId)) {
  parent: sqlServer
  name: 'ActiveDirectory'
  properties: {
    administratorType: 'ActiveDirectory'
    login: entraAdminLogin
    sid: entraAdminObjectId
    tenantId: subscription().tenantId
  }
}

resource sqlDatabase 'Microsoft.Sql/servers/databases@2023-08-01-preview' = {
  parent: sqlServer
  name: 'sqldb-redsosten'
  location: location
  sku: {
    name: 'GP_S_Gen5_1'
    tier: 'GeneralPurpose'
    family: 'Gen5'
    capacity: 1
  }
  properties: {
    autoPauseDelay: 60
    minCapacity: json('0.5')
  }
}

resource sqlPrivateEndpoint 'Microsoft.Network/privateEndpoints@2024-01-01' = {
  name: 'pe-sql-redsosten'
  location: location
  properties: {
    subnet: {
      id: dbSubnet.id
    }
    privateLinkServiceConnections: [
      {
        name: 'sql-connection'
        properties: {
          privateLinkServiceId: sqlServer.id
          groupIds: ['sqlServer']
        }
      }
    ]
  }
}

resource privateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  // This zone is the documented Azure SQL Private Link DNS suffix.
  #disable-next-line no-hardcoded-env-urls
  name: 'privatelink.database.windows.net'
  location: 'global'
}

resource privateDnsLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: privateDnsZone
  name: 'vnet-redsosten-link'
  location: 'global'
  properties: {
    virtualNetwork: {
      id: vnet.id
    }
    registrationEnabled: false
  }
}

resource privateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-01-01' = {
  parent: sqlPrivateEndpoint
  name: 'sql-dns-zone-group'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'sql-dns-config'
        properties: {
            privateDnsZoneId: privateDnsZone.id
        }
      }
    ]
  }
}

resource openAi 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: 'aoai-redsosten-${suffix}'
  location: location
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: 'aoai-redsosten-${suffix}'
    publicNetworkAccess: 'Enabled'
  }
}

resource documentIntelligence 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: 'di-redsosten-${suffix}'
  location: location
  kind: 'FormRecognizer'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: 'di-redsosten-${suffix}'
    publicNetworkAccess: 'Enabled'
  }
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: 'kvredsosten${suffix}'
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    publicNetworkAccess: 'Enabled'
  }
}

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: 'acrredsosten${suffix}'
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
  }
}

resource managedEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'cae-redsosten-${suffix}'
  location: location
  properties: {
    vnetConfiguration: {
      infrastructureSubnetId: appSubnet.id
    }
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'ca-redsosten-kiosco'
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: managedEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      registries: [
        {
          server: acr.properties.loginServer
          identity: 'system'
        }
      ]
      ingress: {
        external: true
        targetPort: containerTargetPort
        transport: 'auto'
      }
    }
    template: {
      containers: [
        {
          name: 'kiosco'
          image: containerImage
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          env: [
            {
              name: 'AZURE_SQL_SERVER'
              value: sqlServer.properties.fullyQualifiedDomainName
            }
            {
              name: 'AZURE_SQL_DATABASE'
              value: sqlDatabase.name
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: openAi.properties.endpoint
            }
            {
              name: 'AZURE_OPENAI_DEPLOYMENT'
              value: openAiDeployment
            }
            {
              name: 'DOCUMENT_INTELLIGENCE_ENDPOINT'
              value: documentIntelligence.properties.endpoint
            }
            {
              name: 'AZURE_KEY_VAULT_URL'
              value: keyVault.properties.vaultUri
            }
          ]
        }
      ]
      scale: {
        minReplicas: containerMinReplicas
        maxReplicas: 1
      }
    }
  }
}

resource acrPullRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, containerApp.id, 'AcrPull')
  scope: acr
  properties: {
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '7f951dda-4ed3-4680-a7ca-43fe172d538d'
    )
  }
}

resource keyVaultSecretsRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, containerApp.id, 'KeyVaultSecretsUser')
  scope: keyVault
  properties: {
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '4633458b-17de-408a-b874-0445c86b69e6'
    )
  }
}

resource openAiUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openAi.id, containerApp.id, 'CognitiveServicesOpenAIUser')
  scope: openAi
  properties: {
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
    )
  }
}

resource documentIntelligenceUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(documentIntelligence.id, containerApp.id, 'CognitiveServicesUser')
  scope: documentIntelligence
  properties: {
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      'a97b65f3-24c7-4388-baec-2e7a223487b3'
    )
  }
}

output containerAppUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
output sqlServerName string = sqlServer.name
output acrLoginServer string = acr.properties.loginServer
output openAiEndpoint string = openAi.properties.endpoint
output documentIntelligenceEndpoint string = documentIntelligence.properties.endpoint
output keyVaultName string = keyVault.name
output managedIdentityPrincipalId string = containerApp.identity.principalId
