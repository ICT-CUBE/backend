# 아키텍처 문서

이 문서는 Hanium 백엔드 개발 서버의 인프라 구조를 설명합니다.

## 전체 구조

```text
Frontend / Client
        |
        | HTTPS API 요청
        v
Azure App Service
  hanium
        |
        | Docker 이미지 실행
        v
Azure Container Registry
  haniumacr.azurecr.io/hanium-api
        |
        | TLS로 MySQL 연결
        v
Azure Database for MySQL Flexible Server
  hanium-mysql
```

## 주요 리소스

```text
Resource Group: hanium-rg
App Service: hanium
App Service Plan: hanium-plan
Container Registry: haniumacr
MySQL Server: hanium-mysql
Database: hanium
```

## FastAPI

진입점:

```text
app/main.py
```

주요 엔드포인트:

```text
GET /
GET /health
GET /health/db
GET /docs
```

## Docker

배포용 컨테이너는 `Dockerfile`로 빌드합니다. 컨테이너 내부에서 FastAPI는 `8000` 포트로 실행됩니다.

```text
haniumacr.azurecr.io/hanium-api
```

GitHub Actions는 다음 태그를 push합니다.

```text
hanium-api:${GITHUB_SHA}
hanium-api:latest
```

## 데이터베이스

Azure MySQL은 secure transport를 요구하므로 배포 환경에서는 TLS 연결을 사용합니다.

```env
MYSQL_SSL_ENABLED=true
```

로컬 Docker Compose에서는 MySQL 컨테이너를 직접 띄우므로 TLS를 사용하지 않습니다.

```env
MYSQL_SSL_ENABLED=false
```

## OpenAI GPT

OpenAI GPT 기능은 환경변수로 분리합니다.

```env
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini
```

`OPENAI_API_KEY`는 비밀값이므로 Git에 커밋하지 않습니다. 로컬에서는 `.env`, Azure에서는 App Service 환경변수에만 설정합니다.

## CI/CD

워크플로 파일:

```text
.github/workflows/deploy-dev.yml
```

브랜치 전략:

```text
infra-init-v2 -> 인프라 초기화 작업 브랜치
dev-v2        -> 개발 서버 자동 배포 브랜치
main          -> 건드리지 않음
```

`dev-v2` 브랜치에 push되면 GitHub Actions가 Docker 이미지를 빌드하고 Azure App Service에 배포합니다.
