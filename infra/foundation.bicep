// Azure 공통 기반 리소스: 네트워크, ACR, Container Apps 환경, MySQL을 생성합니다.
// 앱 이미지는 ACR 생성 후 빌드해야 하므로 app.bicep과 의도적으로 분리했습니다.
targetScope = 'resourceGroup'

@description('CHANGE_ME: 리소스 이름 앞에 붙을 짧은 영문 소문자 프로젝트명 (예: hanium)')
@minLength(3)
@maxLength(18)
param namePrefix string

@description('리소스를 배치할 Azure 리전. 기본값은 리소스 그룹 위치입니다.')
param location string = resourceGroup().location

@description('MySQL 관리자 ID. admin, root 등 예약어는 사용하지 마세요.')
param mysqlAdminLogin string = 'haniumadmin'

@secure()
@description('CHANGE_ME: 대/소문자, 숫자, 특수문자를 조합한 MySQL 관리자 비밀번호')
param mysqlAdminPassword string

@description('애플리케이션이 사용할 초기 데이터베이스 이름')
param mysqlDatabaseName string = 'hanium'

// 전역에서 이름이 겹치지 않도록 구독/리소스 그룹 기반 접미사를 붙입니다.
var uniqueSuffix = uniqueString(subscription().subscriptionId, resourceGroup().id)
var normalizedPrefix = toLower(replace(namePrefix, '-', ''))
var acrName = take('${normalizedPrefix}${uniqueSuffix}acr', 50)
var mysqlServerName = take('${normalizedPrefix}-${uniqueSuffix}-mysql', 63)
var containerEnvironmentName = '${namePrefix}-env'
var identityName = '${namePrefix}-container-pull-id'

resource vnet 'Microsoft.Network/virtualNetworks@2024-05-01' = {
  name: '${namePrefix}-vnet'
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: [
        '10.20.0.0/16'
      ]
    }
    subnets: [
      {
        // Consumption Container Apps 환경에는 /23 이상의 전용 서브넷이 필요합니다.
        name: 'container-apps-subnet'
        properties: {
          addressPrefix: '10.20.0.0/23'
          delegations: []
        }
      }
      {
        // MySQL Flexible Server만 사용할 수 있는 위임 서브넷입니다.
        name: 'mysql-subnet'
        properties: {
          addressPrefix: '10.20.2.0/24'
          delegations: [
            {
              name: 'mysql-flexible-server-delegation'
              properties: {
                serviceName: 'Microsoft.DBforMySQL/flexibleServers'
              }
            }
          ]
        }
      }
    ]
  }
}

resource containerAppsSubnet 'Microsoft.Network/virtualNetworks/subnets@2024-05-01' existing = {
  parent: vnet
  name: 'container-apps-subnet'
}

resource mysqlSubnet 'Microsoft.Network/virtualNetworks/subnets@2024-05-01' existing = {
  parent: vnet
  name: 'mysql-subnet'
}

resource privateDnsZone 'Microsoft.Network/privateDnsZones@2024-06-01' = {
  // Flexible Server private access용 DNS 영역은 mysql.database.azure.com으로 끝나야 합니다.
  name: '${normalizedPrefix}.mysql.database.azure.com'
  location: 'global'
}

resource privateDnsLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = {
  parent: privateDnsZone
  name: '${namePrefix}-vnet-link'
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: vnet.id
    }
  }
}

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${namePrefix}-logs'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource containerEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: containerEnvironmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
    vnetConfiguration: {
      infrastructureSubnetId: containerAppsSubnet.id
      internal: false
    }
  }
}

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: acrName
  location: location
  sku: {
    // 공모전 초기 단계에는 Basic이면 충분합니다. 트래픽 증가 시 Standard로 변경하세요.
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
  }
}

resource pullIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
}

// 비밀번호 없이 ACR 이미지를 가져올 수 있도록 관리 ID에 AcrPull 역할만 부여합니다.
resource acrPullRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registry.id, pullIdentity.id, 'AcrPull')
  scope: registry
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '7f951dda-4ed3-4680-a7ca-43fe172d538d'
    )
    principalId: pullIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource mysqlServer 'Microsoft.DBforMySQL/flexibleServers@2023-12-30' = {
  name: mysqlServerName
  location: location
  sku: {
    // 저비용 시작점입니다. 부하 테스트 후 Standard_D2ds_v4 이상을 검토하세요.
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    administratorLogin: mysqlAdminLogin
    administratorLoginPassword: mysqlAdminPassword
    version: '8.0.21'
    storage: {
      storageSizeGB: 20
      autoGrow: 'Enabled'
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      // 공모전 비용 절감용. 실제 서비스 전환 시 ZoneRedundant를 검토하세요.
      mode: 'Disabled'
    }
    network: {
      delegatedSubnetResourceId: mysqlSubnet.id
      privateDnsZoneResourceId: privateDnsZone.id
      publicNetworkAccess: 'Disabled'
    }
  }
  dependsOn: [
    privateDnsLink
  ]
}

resource applicationDatabase 'Microsoft.DBforMySQL/flexibleServers/databases@2023-12-30' = {
  parent: mysqlServer
  name: mysqlDatabaseName
  properties: {
    charset: 'utf8mb4'
    collation: 'utf8mb4_0900_ai_ci'
  }
}

output acrName string = registry.name
output acrLoginServer string = registry.properties.loginServer
output containerEnvironmentId string = containerEnvironment.id
output pullIdentityId string = pullIdentity.id
output mysqlHost string = mysqlServer.properties.fullyQualifiedDomainName
output mysqlDatabaseName string = applicationDatabase.name

