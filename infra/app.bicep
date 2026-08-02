// ACR에 이미지가 올라간 뒤 Container App을 생성/업데이트합니다.
targetScope = 'resourceGroup'

@description('foundation.bicep과 동일한 프로젝트 접두사')
param namePrefix string

param location string = resourceGroup().location

@description('foundation.bicep 출력값: ACR 이름')
param acrName string

@description('foundation.bicep 출력값: Container Apps Environment 리소스 ID')
param containerEnvironmentId string

@description('foundation.bicep 출력값: ACR Pull 관리 ID 리소스 ID')
param pullIdentityId string

@description('foundation.bicep 출력값: MySQL FQDN')
param mysqlHost string

param mysqlDatabaseName string = 'hanium'
param mysqlAdminLogin string = 'haniumadmin'

@secure()
param mysqlAdminPassword string

@description('ACR 저장소 이름')
param imageName string = 'backend'

@description('CHANGE_ME: 배포할 불변 이미지 태그. latest 대신 Git SHA 사용을 권장합니다.')
param imageTag string

@secure()
@description('선택 사항: OpenAI API를 사용할 때만 전달합니다.')
param openAiApiKey string = ''

@description('CHANGE_ME: 실제 프론트엔드 Origin 목록')
param corsOrigins array = [
  'http://localhost:3000'
]

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: acrName
}

resource containerEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' existing = {
  name: last(split(containerEnvironmentId, '/'))
}

var appName = '${namePrefix}-api'
var appSecrets = concat(
  [
    {
      name: 'db-password'
      value: mysqlAdminPassword
    }
  ],
  empty(openAiApiKey)
    ? []
    : [
        {
          name: 'openai-api-key'
          value: openAiApiKey
        }
      ]
)
var appEnvironmentVariables = concat(
  [
    { name: 'APP_NAME', value: appName }
    { name: 'ENVIRONMENT', value: 'production' }
    { name: 'DEBUG', value: 'false' }
    { name: 'LOG_LEVEL', value: 'INFO' }
    { name: 'DB_HOST', value: mysqlHost }
    { name: 'DB_PORT', value: '3306' }
    { name: 'DB_NAME', value: mysqlDatabaseName }
    { name: 'DB_USER', value: mysqlAdminLogin }
    { name: 'DB_PASSWORD', secretRef: 'db-password' }
    { name: 'DB_SSL', value: 'true' }
    { name: 'CORS_ORIGINS', value: string(corsOrigins) }
  ],
  empty(openAiApiKey)
    ? []
    : [
        { name: 'OPENAI_API_KEY', secretRef: 'openai-api-key' }
      ]
)

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${pullIdentityId}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        allowInsecure: false
        targetPort: 8000
        transport: 'auto'
      }
      registries: [
        {
          server: registry.properties.loginServer
          identity: pullIdentityId
        }
      ]
      secrets: appSecrets
    }
    template: {
      containers: [
        {
          name: 'api'
          image: '${registry.properties.loginServer}/${imageName}:${imageTag}'
          env: appEnvironmentVariables
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/api/v1/health/live'
                port: 8000
                scheme: 'HTTP'
              }
              initialDelaySeconds: 10
              periodSeconds: 10
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/api/v1/health/ready'
                port: 8000
                scheme: 'HTTP'
              }
              initialDelaySeconds: 10
              periodSeconds: 10
            }
          ]
        }
      ]
      scale: {
        // 미사용 시 0으로 축소해 비용을 줄입니다. 첫 요청에는 콜드 스타트가 발생할 수 있습니다.
        minReplicas: 0
        maxReplicas: 2
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}

output appName string = containerApp.name
output appUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'

