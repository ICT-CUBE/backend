# Hanium Backend

FastAPI + MySQL 기반 공모전 백엔드 초기 프로젝트입니다. 로컬 개발은 Docker Compose로 실행하고,
Azure에서는 Container Apps + ACR + Azure Database for MySQL Flexible Server를 사용합니다.

## 로컬 실행

1. 환경 변수 파일을 만들고 `CHANGE_ME` 값을 로컬 비밀번호로 바꿉니다.

   ```powershell
   Copy-Item .env.example .env
   ```

2. API와 MySQL을 실행합니다.

   ```powershell
   docker compose up --build
   ```


3. 아래 주소를 확인합니다.

   - API: `http://localhost:8000`
   - Swagger: `http://localhost:8000/docs`
   - Liveness: `http://localhost:8000/api/v1/health/live`
   - Readiness(DB 포함): `http://localhost:8000/api/v1/health/ready`

종료는 `docker compose down`을 사용합니다. DB 데이터까지 지우고 완전히 초기화할 때만
`docker compose down -v`를 사용하세요.

## Docker 없이 앱 개발

MySQL만 Docker로 실행하고 Python 앱은 호스트에서 실행할 수도 있습니다. 이 경우 `.env`의
`DB_HOST`를 `localhost`로 바꾸세요.

```powershell
python -m venv .venv
./.venv/Scripts/Activate.ps1
pip install -e '.[dev]'
docker compose up -d mysql
alembic upgrade head
uvicorn app.main:app --reload
```

## 새 API 추가 위치

- 라우터: `app/api/routes/`
- 라우터 등록: `app/api/router.py`
- DB 모델: `app/models/`를 만든 뒤 `app/db/base.py`의 `Base` 상속
- 비즈니스/외부 API 로직: `app/services/`
- 설정값: `app/core/config.py`와 `.env.example` 양쪽에 추가

DB 모델을 변경한 뒤에는 다음 명령으로 migration을 생성하고 생성 파일을 반드시 검토합니다.

```powershell
alembic revision --autogenerate -m "describe_change"
alembic upgrade head
```

## 테스트와 정적 검사

```powershell
ruff check .
pytest
```

## Azure 배포

Azure 리소스 구성과 교체할 값은 [`infra/README.md`](infra/README.md)에 정리되어 있습니다.
배포는 기반 리소스 생성, ACR 원격 이미지 빌드, Container App 갱신 순서로 자동 수행됩니다.

## 비밀값 관리 원칙

- `.env`, DB 비밀번호, OpenAI 키를 Git에 커밋하지 않습니다.
- Azure 배포 시 비밀값은 Container Apps secret으로 저장되고 앱에는 secret reference로 주입됩니다.
- ACR 관리자 ID/비밀번호 대신 Managed Identity와 최소 권한 `AcrPull`을 사용합니다.
- 로그에 요청 본문, 인증 헤더, DB URL, API 키를 출력하지 않습니다.

