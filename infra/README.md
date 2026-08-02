# Azure 인프라

이 디렉터리는 다음 리소스를 Bicep으로 관리합니다.

- Azure Container Registry(ACR): FastAPI 이미지 저장, 관리자 계정 비활성화
- User-assigned Managed Identity: Container App의 ACR pull 전용 권한
- Azure Container Apps: 외부 HTTPS API, 자동 확장 0~2 replicas
- Azure Database for MySQL Flexible Server: Burstable, 공개 접속 차단
- VNet / 전용 서브넷 / Private DNS: API에서 DB로만 비공개 통신
- Log Analytics: Container Apps 로그 수집

## 최초 배포

Azure CLI 로그인 후 저장소 루트에서 PowerShell 7로 실행합니다.

```powershell
az login
$env:MYSQL_ADMIN_PASSWORD = 'CHANGE_ME_STRONG_PASSWORD'
$env:OPENAI_API_KEY = 'CHANGE_ME_OPTIONAL_OPENAI_KEY' # OpenAI를 아직 안 쓰면 생략

./infra/deploy.ps1 `
  -SubscriptionId 'CHANGE_ME_AZURE_SUBSCRIPTION_ID' `
  -NamePrefix 'CHANGE_ME_UNIQUE_PROJECT_NAME' `
  -Location 'koreacentral' `
  -CorsOrigins @('https://CHANGE_ME_FRONTEND_DOMAIN')
```

`NamePrefix`는 3~18자의 영문 소문자/숫자/하이픈을 사용합니다. ACR과 MySQL 이름에는 자동으로
고유 접미사가 붙습니다. 같은 명령을 다시 실행하면 기존 리소스를 갱신하므로 별도의 수동 생성은
필요하지 않습니다.

## 변경할 가능성이 높은 값

| 목적 | 위치 | 기본값 / 변경 시점 |
|---|---|---|
| Azure 구독 | `deploy.ps1 -SubscriptionId` | 본인 구독 ID를 입력 |
| 리소스 접두사 | `deploy.ps1 -NamePrefix` | 팀/프로젝트 고유 이름 입력 |
| DB 비밀번호 | `MYSQL_ADMIN_PASSWORD` | 최초 배포 전에 강력한 값 입력 |
| OpenAI 키 | `OPENAI_API_KEY` | OpenAI 기능 연결 시 입력 |
| 프론트 주소 | `deploy.ps1 -CorsOrigins` | 프론트 배포 주소 확정 시 교체 |
| 서버 사양 | `foundation.bicep`의 MySQL `sku` | 부하 테스트 후 상향 |
| 최소 인스턴스 | `app.bicep`의 `minReplicas` | 콜드 스타트 제거가 필요하면 1 |

## 운영 전 체크

현재 구성은 공모전 초기 비용에 맞춰 단일 DB와 7일 로컬 중복 백업을 사용합니다. 실제 사용자
서비스로 전환할 때는 MySQL Zone Redundant HA, 장기 백업, 별도 migration job, Azure Key Vault,
WAF/API Management 도입을 트래픽과 예산에 맞춰 검토하세요.

