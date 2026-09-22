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

## Azure 구매 확정 시연 준비

배송 완료 거래의 구매 확정과 NFT 소유권 이전을 반복해서 시연할 수 있도록 대상 거래만
구매 확정 직전 상태로 되돌립니다. 전체 Backend DB, Blockchain DB, Hardhat 체인은
초기화하지 않습니다. 먼저 Azure CLI 로그인이 되어 있어야 합니다.

```powershell
az login
cd C:\Projects\hanium\backend
.\.venv\Scripts\python.exe .\scripts\setup_database.py
```

기본 대상은 목데이터의 거래 1번(`NO.0031`, 판매자 2 → 구매자 1)입니다. 실행하면 대상
거래와 판매자·구매자를 보여준 뒤 거래 id `1`을 확인 입력으로 요구합니다. 다른 거래를
준비하려면 `--trade-id`를 지정하고, 확인 질문 없이 실행하려면 `--yes`를 사용합니다.

```powershell
.\.venv\Scripts\python.exe .\scripts\setup_database.py --yes
.\.venv\Scripts\python.exe .\scripts\setup_database.py --trade-id 1
```

스크립트는 다음 순서로 실행됩니다.

1. Azure Backend App Service 환경변수와 대상 거래 조회
2. 대상 NFT가 미발행이면 판매자에게 Mint
3. 이전 시연으로 구매자가 NFT를 보유 중이면 판매자에게 역이전
4. 대상 거래의 기존 디지털 인증서와 Transfer 작업 기록 삭제
5. 판매자 큐브 소유권, 큐브, 판매글을 거래 중 상태로 복원
6. 대상 거래를 `DELIVERED` 상태와 배송 타임라인으로 복원

Azure 환경변수의 DB 접속 정보와 블록체인 인증값은 실행 프로세스에만 주입하며 비밀값을
로컬 파일이나 콘솔에 출력하지 않습니다. 준비가 끝나면 구매자 계정으로 로그인해
`PATCH /api/v1/users/me/trades/{tradeId}/complete`를 호출하면 됩니다.

## 블록체인 연동 로컬 실행

큐브 NFT 발행·이전은 별도 저장소의 ARZONE Blockchain Server와 연동합니다.
연동 계약과 규칙은 `app/blockchain/docs/` 문서를 참고합니다.

아래 절차는 두 저장소가 같은 상위 디렉터리에 있고, Backend와 Blockchain Server
애플리케이션은 각각 Docker Compose로 실행하는 구성을 기준으로 합니다. 현재
Blockchain Server Compose에는 Hardhat 서비스가 없으므로 Hardhat 로컬 체인과 컨트랙트
배포 명령만 Windows 호스트에서 실행합니다.

```text
hanium/
├─ backend/
└─ blockchain-server/
```

Backend `.env`에서 Docker 컨테이너가 호스트의 Blockchain Server에 접근하도록 설정합니다.

```ini
BLOCKCHAIN_BASE_URL=http://host.docker.internal:3100
```

Blockchain Server `.env`는 다음 로컬 주소를 사용합니다.

```ini
CUBE_NFT_NETWORK=localhost
DATABASE_URL=mysql://cube_nft:cube_nft@mysql:3306/cube_nft
TRANSACTION_RPC_URL_PRIMARY=http://host.docker.internal:8545
NOTIFICATION_CALLBACK_URL=http://host.docker.internal:8000/api/v1/internal/blockchain/notifications
CONFIRMATION_BLOCKS_REQUIRED=1
```

`blockchain-server/.env`와 Backend `.env`의 인증값은 서로 일치해야 합니다.

- `HMAC_INBOUND_KEY_*` ↔ `BLOCKCHAIN_HMAC_KEY_*`
- `APPROVAL_JWT_SECRET` ↔ `BLOCKCHAIN_APPROVAL_JWT_SECRET`
- `HMAC_OUTBOUND_KEY_*` ↔ `BLOCKCHAIN_WEBHOOK_HMAC_KEY_*`

### 전체 로컬 환경 한 번에 초기화

Backend DB, Blockchain DB, Hardhat 체인을 함께 초기화하고 두 서버 실행, 컨트랙트 배포,
기존 큐브 백필 Mint까지 한 번에 처리하려면 Backend 저장소에서 실행합니다.

```powershell
cd C:\Projects\hanium\backend
.\scripts\reset-local-stack.ps1
```

확인 질문 없이 실행하려면 `-Force`, 두 Docker 이미지도 다시 빌드하려면 `-Rebuild`를
추가합니다.

```powershell
.\scripts\reset-local-stack.ps1 -Force
.\scripts\reset-local-stack.ps1 -Force -Rebuild
```

이 스크립트는 `backend_mysql-data`, `blockchain-server_mysql-data` 볼륨을 삭제합니다.
Hardhat은 숨김 프로세스로 실행되며 로그는 `blockchain-server/.local-logs/`에 저장됩니다.
일반적인 초기화에는 기존 이미지를 재사용하는 첫 번째 명령을 사용합니다.

### 1. Blockchain MySQL 준비

Blockchain Server 저장소의 MySQL 호스트 포트는 Backend MySQL과 충돌하지 않도록
`3307:3306`으로 설정되어 있어야 합니다.

```powershell
cd C:\Projects\hanium\blockchain-server
docker compose up -d mysql
npm ci
$env:DATABASE_URL="mysql://cube_nft:cube_nft@127.0.0.1:3307/cube_nft"
npm run migration:run --workspace=server
Remove-Item Env:DATABASE_URL
```

`npm ci`는 의존성이 이미 설치되어 있으면 매번 실행할 필요가 없습니다. 마이그레이션
명령은 Windows 호스트에서 실행되므로 해당 명령을 실행하는 동안에만 공개 포트
`127.0.0.1:3307`을 사용합니다. Blockchain Server 컨테이너는 `.env`에 설정한
`mysql:3306`으로 같은 Compose의 MySQL 서비스에 연결합니다.

### 2. Hardhat 로컬 체인 실행 — 터미널 1

```powershell
cd C:\Projects\hanium\blockchain-server
npm run node --workspace=contracts/cube-nft
```

이 프로세스는 종료하지 않고 계속 실행합니다. 로컬 Hardhat 노드는 트랜잭션이 있을
때만 블록을 만들기 때문에 `CONFIRMATION_BLOCKS_REQUIRED=1`로 설정해야 합니다.

### 3. 컨트랙트 배포와 Blockchain Server 실행 — 터미널 2

Hardhat 노드가 실행된 다음 Windows 호스트에서 컨트랙트를 배포합니다. 배포 결과가
`contracts/deployments/localhost.json`에 생성됩니다. 로컬 Compose는 이 디렉터리를
Blockchain Server 컨테이너에 읽기 전용으로 마운트하므로 체인 초기화 후에도 최신
배포 주소를 사용합니다.

```powershell
cd C:\Projects\hanium\blockchain-server
npm run deploy:localhost --workspace=contracts/cube-nft
docker compose up --build server
```

Blockchain Server 컨테이너는 종료하지 않고 계속 실행합니다. 호스트에 공개된
`http://127.0.0.1:3100`에서 요청을 받습니다.

### 4. Backend 실행 — 터미널 3

```powershell
cd C:\Projects\hanium\backend
docker compose -f docker-compose.dev.yml up --build
```

정상적으로 실행되면 로컬 서비스는 다음 포트를 사용합니다.

```text
Backend API       localhost:8000
Backend MySQL     localhost:3306
Blockchain API    localhost:3100
Blockchain MySQL  localhost:3307
Hardhat RPC       localhost:8545
```

### 5. 기존 목데이터 백필 Mint — 터미널 4

기존 목데이터 큐브를 거래 시나리오에 쓰려면 백필 발행을 한 번 실행합니다.

```powershell
cd C:\Projects\hanium\backend
docker compose -f docker-compose.dev.yml exec api python scripts/backfill_mint.py
```

Backend를 Docker가 아니라 Windows 호스트에서 직접 실행하는 경우에는 다음 명령을
사용할 수 있습니다.

```powershell
cd C:\Projects\hanium\backend
$env:MYSQL_HOST="localhost"
.venv\Scripts\python.exe scripts/backfill_mint.py
```

### Hardhat 노드 재시작 시 주의사항

Hardhat 노드를 종료하면 로컬 체인 상태와 서명 계정의 nonce가 초기화됩니다. 반면
Blockchain Server DB에는 이전 체인의 nonce 예약과 Operation이 남으므로, Hardhat
노드만 새로 실행하면 Mint가 `REQUESTED` 상태에서 멈추고 확정 대기시간을 초과할 수
있습니다.

따라서 Hardhat 노드를 새로 실행할 때는 Blockchain Server DB 볼륨도 함께 초기화한
뒤 마이그레이션을 다시 실행해야 합니다.

> 아래 `docker compose down -v`는 **Blockchain Server 전용 MySQL 데이터와 볼륨을
> 삭제합니다.** Backend MySQL에는 영향을 주지 않지만, 보존해야 할 Blockchain Server
> 로컬 데이터가 없는지 확인한 후 실행합니다.

```powershell
cd C:\Projects\hanium\blockchain-server
docker compose down -v
docker compose up -d mysql
$env:DATABASE_URL="mysql://cube_nft:cube_nft@127.0.0.1:3307/cube_nft"
npm run migration:run --workspace=server
Remove-Item Env:DATABASE_URL
```

초기화 후 다음 순서로 다시 실행합니다.

1. Hardhat 로컬 체인 실행
2. `npm run deploy:localhost --workspace=contracts/cube-nft`로 컨트랙트 재배포
3. `docker compose up --build server`로 Blockchain Server 컨테이너 재빌드·실행
4. Backend의 `scripts/backfill_mint.py` 재실행
