param location string
@maxLength(11)
param prefix string
param deployDatabricks bool = false
param githubOwner string = ''
param githubRepository string
var suffix = uniqueString(resourceGroup().id)
resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: '${prefix}${suffix}'
  location: location
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  properties: {
    isHnsEnabled: true
    isSftpEnabled: false
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    accessTier: 'Hot'
    publicNetworkAccess: 'Enabled'
    networkAcls: { defaultAction: 'Allow', bypass: 'AzureServices' }
  }
}
resource blob 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
  properties: {}
}
resource containers 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = [for layer in ['landing','bronze','silver','gold']: {
  parent: blob
  name: layer
  properties: { publicAccess: 'None' }
}]
resource factory 'Microsoft.DataFactory/factories@2018-06-01' = {
  name: 'adf-${prefix}-${suffix}'
  location: location
  identity: { type: 'SystemAssigned' }
  properties: union({ publicNetworkAccess: 'Enabled' }, empty(githubOwner) ? {} : {
    repoConfiguration: {
      type: 'FactoryGitHubConfiguration'
      accountName: githubOwner
      repositoryName: githubRepository
      collaborationBranch: 'main'
      rootFolder: '/adf'
      disablePublish: false
    }
  })
}
resource landingRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containers[0].id, factory.id, 'Storage Blob Data Contributor')
  scope: containers[0]
  properties: {
    principalId: factory.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions','ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  }
}
resource lakeService 'Microsoft.DataFactory/factories/linkedservices@2018-06-01' = {
  parent: factory
  name: 'ls_adls'
  properties: {
    type: 'AzureBlobFS'
    typeProperties: { url: 'https://${storage.name}.dfs.${environment().suffixes.storage}' }
  }
}
resource workspace 'Microsoft.Databricks/workspaces@2024-05-01' = if (deployDatabricks) {
  name: 'dbw-${prefix}-${suffix}'
  location: location
  sku: { name: 'standard' }
  properties: {
    managedResourceGroupId: subscriptionResourceId('Microsoft.Resources/resourceGroups','rg-dbw-${prefix}-${suffix}')
    publicNetworkAccess: 'Enabled'
    parameters: { enableNoPublicIp: { value: true } }
  }
}
output storageAccount string = storage.name
output factoryName string = factory.name
