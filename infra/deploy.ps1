<#
.SYNOPSIS
  Azure 기반 리소스 생성 → ACR 원격 빌드 → Container App 배포를 순서대로 수행합니다.

.ENVIRONMENT VARIABLES (CHANGE_ME)
  MYSQL_ADMIN_PASSWORD : 필수. Azure MySQL 관리자 비밀번호
  OPENAI_API_KEY       : 선택. OpenAI 기능을 사용할 때만 지정

.EXAMPLE
  $env:MYSQL_ADMIN_PASSWORD = '<강력한-비밀번호>'
  ./infra/deploy.ps1 -SubscriptionId '<구독-ID>' -NamePrefix 'hanium' -Location 'koreacentral'
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [string] $SubscriptionId,
    [Parameter(Mandatory = $true)] [ValidatePattern('^[a-z][a-z0-9-]{2,17}$')] [string] $NamePrefix,
    [string] $Location = 'koreacentral',
    [string] $ResourceGroup = "$NamePrefix-rg",
    [string] $MysqlAdminLogin = 'haniumadmin',
    [string] $ImageName = 'backend',
    [string] $ImageTag = '',
    [string[]] $CorsOrigins = @('http://localhost:3000')
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw 'Azure CLI(az)가 필요합니다: https://learn.microsoft.com/cli/azure/install-azure-cli'
}
if ([string]::IsNullOrWhiteSpace($env:MYSQL_ADMIN_PASSWORD)) {
    throw '필수 환경 변수 MYSQL_ADMIN_PASSWORD를 먼저 설정하세요.'
}
if ([string]::IsNullOrWhiteSpace($ImageTag)) {
    $gitSha = (git rev-parse --short HEAD 2>$null)
    $ImageTag = if ($LASTEXITCODE -eq 0) { $gitSha } else { (Get-Date -Format 'yyyyMMddHHmmss') }
}

az account set --subscription $SubscriptionId
az group create --name $ResourceGroup --location $Location --output none

Write-Host '1/3 Azure 기반 리소스를 배포합니다...'
$foundationJson = az deployment group create `
    --resource-group $ResourceGroup `
    --template-file "$PSScriptRoot/foundation.bicep" `
    --parameters namePrefix=$NamePrefix mysqlAdminLogin=$MysqlAdminLogin mysqlAdminPassword=$env:MYSQL_ADMIN_PASSWORD `
    --query properties.outputs `
    --output json
if ($LASTEXITCODE -ne 0) { throw '기반 리소스 배포에 실패했습니다.' }
$outputs = $foundationJson | ConvertFrom-Json

Write-Host '2/3 ACR에서 컨테이너 이미지를 빌드합니다...'
$repositoryRoot = (Resolve-Path "$PSScriptRoot/..").Path
az acr build `
    --registry $outputs.acrName.value `
    --image "${ImageName}:${ImageTag}" `
    $repositoryRoot `
    --output none
if ($LASTEXITCODE -ne 0) { throw '컨테이너 이미지 빌드에 실패했습니다.' }

Write-Host '3/3 Container App을 배포합니다...'
$corsJson = $CorsOrigins | ConvertTo-Json -Compress
$appArgs = @(
    'deployment', 'group', 'create',
    '--resource-group', $ResourceGroup,
    '--template-file', "$PSScriptRoot/app.bicep",
    '--parameters',
    "namePrefix=$NamePrefix",
    "acrName=$($outputs.acrName.value)",
    "containerEnvironmentId=$($outputs.containerEnvironmentId.value)",
    "pullIdentityId=$($outputs.pullIdentityId.value)",
    "mysqlHost=$($outputs.mysqlHost.value)",
    "mysqlDatabaseName=$($outputs.mysqlDatabaseName.value)",
    "mysqlAdminLogin=$MysqlAdminLogin",
    "mysqlAdminPassword=$env:MYSQL_ADMIN_PASSWORD",
    "imageName=$ImageName",
    "imageTag=$ImageTag",
    "corsOrigins=$corsJson"
)
if (-not [string]::IsNullOrWhiteSpace($env:OPENAI_API_KEY)) {
    $appArgs += "openAiApiKey=$env:OPENAI_API_KEY"
}
$appJson = az @appArgs --query properties.outputs --output json
if ($LASTEXITCODE -ne 0) { throw 'Container App 배포에 실패했습니다.' }
$appOutputs = $appJson | ConvertFrom-Json

Write-Host "배포 완료: $($appOutputs.appUrl.value)"
Write-Host "Swagger 문서는 운영에서 비활성화됩니다. 상태 확인: $($appOutputs.appUrl.value)/api/v1/health/ready"

