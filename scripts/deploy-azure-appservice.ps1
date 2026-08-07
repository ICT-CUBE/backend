param(
    [string] $ResourceGroup = "hanium-rg",
    [string] $Location = "koreacentral",
    [string] $AppName = "hanium",
    [string] $AcrName = "haniumacr",
    [string] $MysqlServerName = "hanium-mysql",
    [string] $MysqlAdminUser = "haniumadmin",
    [Parameter(Mandatory = $true)]
    [string] $MysqlAdminPassword,
    [string] $MysqlDatabase = "hanium",
    [string] $PlanName = "hanium-plan",
    [string] $Sku = "B1",
    [string] $ImageName = "hanium-api",
    [string] $Tag = "latest"
)

$ErrorActionPreference = "Stop"

Write-Host "Creating resource group..."
az group create `
    --name $ResourceGroup `
    --location $Location `
    --output none

Write-Host "Creating Azure Container Registry..."
az acr create `
    --resource-group $ResourceGroup `
    --name $AcrName `
    --sku Basic `
    --admin-enabled true `
    --output none

Write-Host "Building Docker image locally..."
docker build --tag "$AcrName.azurecr.io/$ImageName`:$Tag" .

Write-Host "Logging in to Azure Container Registry..."
az acr login `
    --name $AcrName `
    --output none

Write-Host "Pushing image to Azure Container Registry..."
docker push "$AcrName.azurecr.io/$ImageName`:$Tag"

Write-Host "Creating Azure Database for MySQL Flexible Server..."
az mysql flexible-server create `
    --resource-group $ResourceGroup `
    --name $MysqlServerName `
    --location $Location `
    --admin-user $MysqlAdminUser `
    --admin-password $MysqlAdminPassword `
    --sku-name Standard_B1ms `
    --tier Burstable `
    --version 8.0.21 `
    --public-access 0.0.0.0 `
    --output none

Write-Host "Creating MySQL database..."
az mysql flexible-server db create `
    --resource-group $ResourceGroup `
    --server-name $MysqlServerName `
    --database-name $MysqlDatabase `
    --output none

$AcrLoginServer = az acr show `
    --resource-group $ResourceGroup `
    --name $AcrName `
    --query loginServer `
    --output tsv

$AcrUsername = az acr credential show `
    --name $AcrName `
    --query username `
    --output tsv

$AcrPassword = az acr credential show `
    --name $AcrName `
    --query "passwords[0].value" `
    --output tsv

Write-Host "Creating App Service plan..."
az appservice plan create `
    --resource-group $ResourceGroup `
    --name $PlanName `
    --is-linux `
    --sku $Sku `
    --output none

Write-Host "Creating Web App for container..."
az webapp create `
    --resource-group $ResourceGroup `
    --plan $PlanName `
    --name $AppName `
    --deployment-container-image-name "$AcrLoginServer/$ImageName`:$Tag" `
    --output none

Write-Host "Configuring container registry credentials..."
az webapp config container set `
    --resource-group $ResourceGroup `
    --name $AppName `
    --container-image-name "$AcrLoginServer/$ImageName`:$Tag" `
    --container-registry-url "https://$AcrLoginServer" `
    --container-registry-user $AcrUsername `
    --container-registry-password $AcrPassword `
    --output none

Write-Host "Configuring app settings..."
az webapp config appsettings set `
    --resource-group $ResourceGroup `
    --name $AppName `
    --settings `
        WEBSITES_PORT=8000 `
        APP_NAME=hanium-api `
        ENVIRONMENT=production `
        DEBUG=false `
        MYSQL_HOST="$MysqlServerName.mysql.database.azure.com" `
        MYSQL_PORT=3306 `
        MYSQL_DATABASE=$MysqlDatabase `
        MYSQL_USER=$MysqlAdminUser `
        MYSQL_PASSWORD=$MysqlAdminPassword `
        MYSQL_SSL_ENABLED=true `
    --output none

Write-Host "Restarting Web App..."
az webapp restart `
    --resource-group $ResourceGroup `
    --name $AppName `
    --output none

Write-Host "Done: https://$AppName.azurewebsites.net"
