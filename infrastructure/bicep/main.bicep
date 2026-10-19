targetScope = 'subscription'
param location string = 'northeurope'
param resourceGroupName string = 'rg-procureflow-dev'
param prefix string = 'procureflow'
param deployDatabricks bool = false
param githubOwner string = ''
param githubRepository string = 'procureflow-data-platform'
resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
  tags: { project: 'ProcureFlow', environment: 'dev', syntheticData: 'true' }
}
module platform './platform.bicep' = {
  name: 'platform'
  scope: rg
  params: {
    location: location
    prefix: prefix
    deployDatabricks: deployDatabricks
    githubOwner: githubOwner
    githubRepository: githubRepository
  }
}
output storageAccount string = platform.outputs.storageAccount
output factoryName string = platform.outputs.factoryName
output resourceGroup string = rg.name
