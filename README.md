# hanium-api

FastAPI, MySQL, Docker, Azure App Service 기반 Hanium 백엔드 API 서버입니다.

## 개발용 배포 서버

```text
https://hanium.azurewebsites.net
```

프론트엔드에서는 API base URL을 환경변수로 분리해서 사용합니다.

```env
NEXT_PUBLIC_API_BASE_URL=https://hanium.azurewebsites.net
```

서버 상태 확인:

- Health: https://hanium.azurewebsites.net/health
- DB Health: https://hanium.azurewebsites.net/health/db
- Swagger UI: https://hanium.azurewebsites.net/docs

OpenAI GPT 기능은 `OPENAI_API_KEY`, `OPENAI_MODEL` 환경변수로 설정합니다. 실제 API 키는 저장소에 올리지 않습니다.

## 로컬 개발 서버

```powershell
Copy-Item .env.example .env
docker compose -f docker-compose.dev.yml up --build
```

로컬 확인:

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Health: http://localhost:8000/health
- DB Health: http://localhost:8000/health/db

## 자동 배포

GitHub Actions CI/CD는 `be/dev-v2` 브랜치 push를 기준으로 실행됩니다.

```text
git push
-> GitHub Actions
-> Docker image build
-> Azure Container Registry push
-> Azure App Service deploy
```

배포 대상:

```text
ACR: haniumacr.azurecr.io/hanium-api
App Service: hanium
MySQL: hanium-mysql
```

자세한 내용은 [docs/architecture.md](docs/architecture.md), [docs/setup.md](docs/setup.md)를 참고합니다.
