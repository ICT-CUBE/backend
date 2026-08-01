# 신규 팀원 개발 환경 구축 및 로컬 실행 가이드

이 문서는 백엔드 저장소를 처음 받은 팀원이 로컬 개발 환경을 준비하고 FastAPI와 MySQL을
정상적으로 실행하기 위한 절차를 설명합니다. 기본 개발 환경은 **Docker Compose 실행 방식**을
권장합니다.

## 1. 현재 개발 환경 구성

로컬에서는 Docker Compose가 다음 두 컨테이너를 실행합니다.

| 서비스 | 역할 | 로컬 주소/포트 |
|---|---|---|
| `api` | FastAPI 백엔드 | `http://localhost:8000` |
| `mysql` | MySQL 8.4 데이터베이스 | `localhost:3306` |

API 컨테이너는 MySQL이 정상 상태가 된 이후 시작합니다. MySQL 데이터는 Docker Volume인
`mysql_data`에 저장되므로 일반적인 컨테이너 재시작으로는 사라지지 않습니다.

## 2. 필수 프로그램

### 반드시 설치

- Git
- Docker Desktop
  - Windows에서는 WSL 2 기반 엔진 사용을 권장합니다.
  - 설치 후 Docker Desktop이 실행 중이어야 합니다.

### Docker 없이 Python을 직접 실행할 때만 설치

- Python 3.12

프로젝트는 Python `3.12 이상, 3.14 미만`을 허용하지만, Docker 이미지와 CI가 Python 3.12를
사용하므로 로컬에서도 3.12 사용을 권장합니다.

### 설치 확인

PowerShell에서 다음 명령을 실행합니다.

```powershell
git --version
docker --version
docker compose version
```

Python을 직접 실행할 경우에만 확인합니다.

```powershell
python --version
```

`docker` 명령이 인식되지 않으면 Docker Desktop 설치 후 PowerShell을 새로 열어보세요.

## 3. 저장소 받기

처음 받는 경우:

```powershell
cd C:\Projects\hanium
git clone https://github.com/ICT-CUBE/backend.git
cd backend
```

이미 저장소가 있는 경우:

```powershell
cd C:\Projects\hanium\backend
git switch dev
git pull origin dev
```

실제 팀 작업은 `dev`에서 직접 수정하지 않고 `dev`를 기준으로 작업 브랜치를 만듭니다.

```powershell
git switch -c be/작업이름
```

예시:

```powershell
git switch -c be/db-schema
```

## 4. 환경변수 파일 준비

프로젝트에는 실제 비밀값이 없는 `.env.example`만 커밋합니다. 각 팀원은 이를 복사해 자신의
`.env`를 생성해야 합니다.

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

### macOS/Linux

```bash
cp .env.example .env
```

`.env`에서 최소한 다음 두 비밀번호를 변경합니다.

```dotenv
DB_PASSWORD=본인이_정한_로컬_DB_비밀번호
MYSQL_ROOT_PASSWORD=본인이_정한_로컬_ROOT_비밀번호
```

Docker Compose로 API와 MySQL을 모두 실행할 때는 다음 값들을 유지합니다.

```dotenv
DB_HOST=mysql
DB_PORT=3306
DB_NAME=hanium
DB_USER=hanium
DB_SSL=false
```

`DB_HOST=mysql`의 `mysql`은 인터넷 주소가 아니라 `compose.yaml`에 정의된 MySQL 서비스
이름입니다. Docker 내부 네트워크에서 API가 이 이름으로 DB 컨테이너를 찾습니다.

OpenAI 기능을 아직 사용하지 않는다면 다음 값은 비워두어도 서버가 실행됩니다.

```dotenv
OPENAI_API_KEY=
```

> `.env`에는 DB 비밀번호와 API 키가 들어갈 수 있으므로 Git에 커밋하면 안 됩니다.
> `.gitignore`에 등록되어 있지만 `git status`에서 한 번 더 확인하세요.

## 5. 권장 방식: Docker Compose로 전체 실행

프로젝트 루트에서 실행합니다.

```powershell
docker compose up --build -d
```

각 옵션의 의미:

- `up`: Compose 서비스를 생성하고 실행합니다.
- `--build`: 변경된 소스와 Dockerfile을 기준으로 API 이미지를 다시 만듭니다.
- `-d`: 터미널을 점유하지 않고 백그라운드에서 실행합니다.

최초 실행은 Python/MySQL 이미지와 패키지를 내려받기 때문에 몇 분 정도 걸릴 수 있습니다.

### 실행 상태 확인

```powershell
docker compose ps
```

정상적인 경우:

- `mysql`이 `healthy`
- `api`가 `Up` 또는 `running`

MySQL이 준비될 때까지 API 시작이 잠시 대기할 수 있습니다.

### 로그 확인

전체 로그:

```powershell
docker compose logs -f
```

API 로그만 확인:

```powershell
docker compose logs -f api
```

MySQL 로그만 확인:

```powershell
docker compose logs -f mysql
```

로그 보기를 종료할 때는 `Ctrl + C`를 누릅니다. 백그라운드 컨테이너는 계속 실행됩니다.

## 6. 정상 실행 확인

컨테이너가 실행된 후 다음 주소를 확인합니다.

| 확인 항목 | 주소 | 정상 결과 |
|---|---|---|
| 기본 API | `http://localhost:8000/` | `status: ok` |
| Swagger | `http://localhost:8000/docs` | API 문서 화면 |
| Liveness | `http://localhost:8000/api/v1/health/live` | `{"status":"ok"}` |
| Readiness | `http://localhost:8000/api/v1/health/ready` | DB 연결 성공 응답 |

PowerShell에서도 확인할 수 있습니다.

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/health/live
Invoke-RestMethod http://localhost:8000/api/v1/health/ready
```

Liveness는 FastAPI 프로세스만 확인합니다. Readiness는 MySQL에 `SELECT 1`까지 실행하므로 두
주소가 모두 성공해야 API와 DB 연결이 정상입니다.

## 7. 서버 종료와 재실행

### 데이터는 유지하고 종료

```powershell
docker compose down
```

### 다시 실행

```powershell
docker compose up -d
```

### 코드 또는 의존성이 변경됐을 때

```powershell
docker compose up --build -d
```

### DB 데이터까지 완전히 초기화

```powershell
docker compose down -v
docker compose up --build -d
```

> `docker compose down -v`는 `mysql_data` 볼륨과 로컬 DB 데이터를 삭제합니다. 팀원이 만든
> 테스트 데이터가 필요한지 확인하고, 정말 초기화할 때만 사용하세요.

## 8. 선택 방식: Python API를 호스트에서 직접 실행

코드 변경 시 빠른 reload가 필요하면 MySQL만 Docker로 실행하고 FastAPI는 로컬 Python으로
실행할 수 있습니다.

### 1단계: MySQL만 실행

```powershell
docker compose up -d mysql
```

### 2단계: `.env` 변경

Docker 밖에서 실행하는 Python은 `mysql`이라는 Docker 서비스 이름을 찾을 수 없습니다.

```dotenv
DB_HOST=localhost
DB_PORT=3306
```

### 3단계: Python 가상환경 생성

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

PowerShell 실행 정책 오류가 발생하면 현재 터미널에서만 다음을 실행한 뒤 다시 활성화합니다.

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 4단계: 패키지 설치

```powershell
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

`pyproject.toml`이 실행 의존성과 개발 의존성을 관리하므로 현재 프로젝트에는 별도
`requirements.txt`가 필요하지 않습니다.

### 5단계: Migration 적용 및 API 실행

```powershell
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

종료는 `Ctrl + C`입니다.

Docker Compose 전체 실행 방식으로 돌아갈 때는 `.env`를 다시 변경합니다.

```dotenv
DB_HOST=mysql
DB_PORT=3306
```

## 9. 테스트와 코드 검사

가상환경이 활성화된 상태에서 실행합니다.

```powershell
ruff check .
pytest
```

자동 수정 가능한 Ruff 오류를 수정하려면:

```powershell
ruff check . --fix
```

Docker 이미지가 정상적으로 생성되는지도 확인할 수 있습니다.

```powershell
docker build -t hanium-backend:local .
```

Compose 설정의 문법과 최종 적용값 확인:

```powershell
docker compose config
```

`docker compose config` 출력에는 `.env` 값이 포함될 수 있으므로 외부에 그대로 공유하지
마세요.

## 10. DB 모델 변경과 Migration

SQLAlchemy 모델을 변경한 뒤 migration 파일을 생성합니다.

```powershell
alembic revision --autogenerate -m "변경_내용"
```

예시:

```powershell
alembic revision --autogenerate -m "create_user_table"
```

생성된 `migrations/versions/` 파일을 검토한 다음 적용합니다.

```powershell
alembic upgrade head
```

자동 생성 결과가 항상 의도와 일치하는 것은 아니므로 migration 파일을 검토하지 않고 바로
커밋하지 마세요.

## 11. 자주 발생하는 문제

### `http://localhost:8000/docs`에 접속할 수 없음

먼저 컨테이너 상태를 확인합니다.

```powershell
docker compose ps -a
docker compose logs api --tail 100
docker compose logs mysql --tail 100
```

`api`가 실행 중이 아니면 Swagger도 열리지 않습니다. Docker Desktop이 실행 중인지도
확인하세요.

### `port is already allocated` 또는 3306 포트 충돌

PC에 설치된 다른 MySQL이 3306을 사용 중일 수 있습니다.

```powershell
Get-NetTCPConnection -LocalPort 3306 -State Listen
```

기존 MySQL을 사용하지 않는다면 해당 서비스를 종료합니다. 기존 MySQL을 유지해야 한다면
`compose.yaml`에서 MySQL의 **왼쪽 호스트 포트만** 3307로 바꿉니다.

```yaml
ports:
  - "3307:3306"
```

- API도 Docker에서 실행: `.env`의 `DB_PORT=3306` 유지
- Python API를 호스트에서 실행: `.env`의 `DB_PORT=3307` 사용

Docker 내부에서는 계속 MySQL 컨테이너의 3306 포트로 연결하기 때문입니다.

### Readiness만 503 반환

FastAPI는 실행 중이지만 MySQL 연결에 실패한 상태입니다.

확인할 항목:

1. `docker compose ps`에서 MySQL이 healthy인지
2. `.env`의 `DB_HOST=mysql`인지
3. `DB_NAME`, `DB_USER`, `DB_PASSWORD`가 MySQL 생성 값과 일치하는지
4. 기존 Volume을 만든 뒤 비밀번호만 변경하지 않았는지

MySQL Volume이 이미 생성된 뒤 `.env` 비밀번호를 바꾸면 기존 DB 계정 비밀번호는 자동으로
변경되지 않습니다. 데이터가 필요 없다면 Volume을 초기화할 수 있지만, 데이터 삭제 전에 반드시
확인하세요.

### MySQL 로그에 InnoDB 손상 오류 발생

최초 초기화 중 Docker가 강제 종료되면 로컬 볼륨이 불완전할 수 있습니다. 필요한 데이터가 없는
새 개발 DB임을 확인한 경우에만 다음으로 초기화합니다.

```powershell
docker compose down -v
docker compose up --build -d
```

### `.env`를 변경했지만 반영되지 않음

컨테이너를 다시 생성합니다.

```powershell
docker compose up -d --force-recreate
```

### 운영 환경에서 `/docs`가 열리지 않음

정상 동작입니다. `app/main.py`는 `ENVIRONMENT=production`일 때 Swagger와 ReDoc을
비활성화합니다. 로컬에서는 `ENVIRONMENT=local`을 사용하세요.

## 12. 작업 시작 전 체크리스트

- [ ] 올바른 저장소와 작업 브랜치인지 확인했다.
- [ ] Docker Desktop이 실행 중이다.
- [ ] `.env.example`을 복사해 `.env`를 만들었다.
- [ ] `.env`의 로컬 DB 비밀번호를 변경했다.
- [ ] `docker compose ps`에서 API와 MySQL 상태를 확인했다.
- [ ] Liveness와 Readiness가 모두 성공한다.
- [ ] `ruff check .`와 `pytest`가 통과한다.
- [ ] `git status`에 `.env`가 포함되지 않는다.
