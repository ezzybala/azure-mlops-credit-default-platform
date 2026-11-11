targetScope = 'resourceGroup'

@description('Location for resources')
param location string = resourceGroup().location

@description('ACR name')
param acrName string

@description('AKS cluster name')
param aksName string

@description('Node count')
param nodeCount int = 1

@description('VM Size')
param vmSize string = 'Standard_B2s'

module acr './acr.bicep' = {
  name: 'acrDeployment'
  params: {
    acrName: acrName
    location: location
  }
}

module aks './aks.bicep' = {
  name: 'aksDeployment'

  params: {
    aksName: aksName
    location: location
    nodeCount: nodeCount
    vmSize: vmSize
    acrId: acr.outputs.acrId
  }
}
output aksClusterName string = aks.outputs.clusterName

output acrLoginServer string = acr.outputs.loginServer
