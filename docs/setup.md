# 세팅 가이드

이 문서는 Hanium 백엔드 서버를 로컬에서 실행하고 Azure 개발 서버로 배포하는 방법을 설명합니다.

## 준비물

```text
Docker Desktop
Azure CLI
GitHub CLI
Python 3.12
```

로그인:

```powershell
az login
gh auth login
```

## 로컬 실행

```powershell
Copy-Item .env.example .env
docker compose -f docker-compose.dev.yml up --build
```

확인:

```text
http://localhost:8000/health
http://localhost:8000/health/db
http://localhost:8000/docs
```

## 로컬 환경변수

```env
APP_NAME=hanium-api
ENVIRONMENT=development
DEBUG=true

MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_DATABASE=hanium
MYSQL_USER=hanium
MYSQL_PASSWORD=hanium_password
MYSQL_SSL_ENABLED=false
```

`.env`는 Git에 올리지 않습니다.

## Azure 개발 서버

```text
https://hanium.azurewebsites.net
```

확인:

```text
https://hanium.azurewebsites.net/health
https://hanium.azurewebsites.net/health/db
https://hanium.azurewebsites.net/docs
```

## 수동 배포

GitHub Actions를 쓰지 않고 직접 배포해야 할 때만 사용합니다.

```powershell
docker build --tag haniumacr.azurecr.io/hanium-api:latest .
docker push haniumacr.azurecr.io/hanium-api:latest
az webapp restart --resource-group hanium-rg --name hanium
```

## 자동 배포

자동 배포는 `dev-v2` 브랜치 기준입니다.

```text
dev-v2 push
-> GitHub Actions
-> Docker build
-> ACR push
-> Azure App Service deploy
```

필요한 GitHub Secrets:

```text
ACR_USERNAME
ACR_PASSWORD
AZURE_CREDENTIALS
```

## Azure 환경변수

Azure Portal 위치:

```text
App Service > hanium > Environment variables
```

필수 설정:

```env
WEBSITES_PORT=8000
APP_NAME=hanium-api
ENVIRONMENT=production
DEBUG=false
MYSQL_HOST=hanium-mysql.mysql.database.azure.com
MYSQL_PORT=3306
MYSQL_DATABASE=hanium
MYSQL_USER=haniumadmin
MYSQL_PASSWORD=...
MYSQL_SSL_ENABLED=true
```

## MySQL 방화벽

Azure MySQL이 생성된 뒤 `/health/db`가 timeout이면 MySQL 방화벽에서 App Service 접근을 허용해야 합니다.

개발 서버 초기 검증 단계에서는 Azure Portal에서 다음 규칙을 추가할 수 있습니다.

```text
Start IP: 0.0.0.0
End IP: 255.255.255.255
```

운영 환경에서는 App Service outbound IP만 허용하는 방식으로 좁히는 것이 좋습니다.
