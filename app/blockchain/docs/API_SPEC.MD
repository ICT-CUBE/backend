## 블록체인 연동 개요

ARZONE Blockchain Server(별도 Node.js 서비스)와 연동해 큐브 NFT를 발행·이전한다.

- 계약 정본: 블록체인 저장소의 `openapi.yaml` (OpenAPI 3.1)
- 로컬 Base URL: `http://127.0.0.1:3100`
- 우리 백엔드는 **클라이언트(호출)** 와 **webhook 수신자(제공)** 두 역할을 모두 맡는다.
- 연동 범위는 **Mint(큐브 최초 인증)** 와 **Transfer(구매 확정)** 두 가지다.
  출금·재진입·외부 재판매는 연동하지 않는다.

---

## 1. 우리가 제공하는 API

### 완료 알림 수신 (webhook)
- http 메서드: post
- domain: blockchain
- endpoint: /api/v1/internal/blockchain/notifications

### API 설명

블록체인 서버가 온체인 확정 후 호출하는 완료 알림을 수신한다.

사용자 요청이 아니라 서버 간 호출이므로 Access Token 인증을 적용하지 않고, 별도의 outbound HMAC 서명으로 검증한다.

---

### 처리 정책

- 블록체인 서버의 `NOTIFICATION_CALLBACK_URL`에 이 경로를 등록한다.
- 요청 헤더의 HMAC 서명을 `BLOCKCHAIN_WEBHOOK_HMAC_KEY_SECRET`으로 검증한다.
- 서명 검증에 실패하면 401을 반환하고 어떤 데이터도 저장하지 않는다.
- 전달은 at-least-once이므로 같은 `notificationId`가 여러 번 올 수 있다.
- 이미 처리한 `notificationId`는 다시 처리하지 않고 `duplicate = true`로 200을 반환한다.
- 2xx가 아니면 블록체인 서버가 재시도하므로, 처리에 성공한 알림은 반드시 200으로 응답한다.

---

### 요청 헤더

| 헤더 | 설명 |
| --- | --- |
| `X-ARZONE-Key-Id` | 블록체인 서버의 outbound HMAC key id |
| `X-ARZONE-Timestamp` | Unix seconds. 현재 시각과 ±300초를 벗어나면 401 |
| `X-ARZONE-Nonce` | 요청마다 새 UUID |
| `X-ARZONE-Signature` | 소문자 hex HMAC-SHA-256 |

---

### 요청 Body

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `notificationId` | string(uuid) | 알림 식별자. 중복 제거 기준 |
| `operationId` | string(uuid) | 작업 식별자 |
| `idempotencyKey` | string(uuid) | 요청 시 우리가 보낸 멱등키 |
| `operationType` | string | MINT 또는 TRANSFER |
| `tokenId` | number | 토큰 id |
| `finalStatus` | string | 항상 `ONCHAIN_CONFIRMED` |
| `finalOwnerAddress` | string | 확정 시점 소유자 주소 |
| `txHash` | string | 트랜잭션 해시 |
| `blockNumber` | number | 블록 번호 |
| `blockHash` | string | 블록 해시 |
| `confirmations` | number | 확정 판정 시점 confirmation 수 |
| `serviceRightsState` | string \| null | MINT·TRANSFER는 `null` |
| `confirmedAt` | string(date-time) | UTC ISO-8601 |

---

### 정상 응답 데이터

Status Code : 200

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `notificationId` | string(uuid) | 수신한 알림 id |
| `accepted` | boolean | 항상 `true` |
| `duplicate` | boolean | 이미 처리한 알림이면 `true` |

```json
{
  "notificationId": "16e98c5d-e79d-46b5-92a5-5573d58d896e",
  "accepted": true,
  "duplicate": false
}
```

---

### 오류 응답 데이터

Status Code : 401

HMAC 헤더가 없거나, 시각이 허용 범위를 벗어났거나, 서명이 일치하지 않는 경우

```json
{
  "code": "INVALID_WEBHOOK_SIGNATURE",
  "message": "유효하지 않은 webhook 서명입니다."
}
```

요청 Body 형식 오류는 공통 `400 INVALID_REQUEST`를 따른다.

---

## 2. 우리가 호출하는 블록체인 서버 API

모든 호출에 HMAC 헤더 4종이 필요하고, 소유권 변경 API는 승인 JWT(`Authorization: Bearer`)를 추가로 보낸다.

| 메서드 | 경로 | 승인 JWT | 사용 시점 |
| --- | --- | --- | --- |
| POST | `/internal/v1/wallets` | 불필요 | Mint·Transfer 직전, 사용자 수탁 지갑 주소 확보 |
| POST | `/internal/v1/metadata` | 불필요 | Mint 직전, NFT 메타데이터 준비 |
| GET | `/internal/v1/metadata/{tokenId}` | 불필요 | 메타데이터 `ready` 확인 |
| POST | `/internal/v1/mints` | `MINT` | 큐브 최초 인증 성공 시 |
| POST | `/internal/v1/transfers` | `TRANSFER` | 구매 확정 시 |
| GET | `/internal/v1/operations/{operationId}` | 불필요 | 작업 상태 폴링·재조회 |
| GET | `/internal/v1/nfts/{tokenId}` | 불필요 | 확정 후 컨트랙트 주소·tokenURI 조회 |

### 요청 Body

```text
POST /internal/v1/wallets    { "userId": "1" }
POST /internal/v1/metadata   { "tokenId": 26, "cubeNumber": "NO.0026",
                               "publicGrade": "UNSPECIFIED",
                               "imageBase64": "...", "imageMimeType": "image/png",
                               "benefitReferenceId": "NONE" }
POST /internal/v1/mints      { "idempotencyKey": "<uuid>", "userId": "1",
                               "cubeId": "2", "tokenId": 26 }
POST /internal/v1/transfers  { "idempotencyKey": "<uuid>", "tradeId": "3",
                               "sellerUserId": "2", "buyerUserId": "1", "tokenId": 26 }
```

### 응답

- `POST /wallets` → `200` `{ userId, address, provider, providerAdapter, integrationReady, status, createdAt }`
- `POST /metadata` → `200` `{ tokenId, metadataCid, tokenUri, ready }`
- `POST /mints`, `POST /transfers` → **`202`** `{ operationId, status, type, tokenId }`
  - 202는 접수 성공일 뿐 온체인 성공이 아니다.
- `GET /operations/{operationId}` → `200` 작업 상태와 트랜잭션 시도·알림 상태
- `GET /nfts/{tokenId}` → `200` `{ tokenId, minted, ownerAddress, contractAddress, metadataUri, checkedAt, blockNumber }`

### 오류

블록체인 서버 오류는 `{ code, message, requestId }` 형식이며, 우리 서비스는 이를 그대로 노출하지 않고 비즈니스 룰에 정의한 정책으로 변환한다.

| HTTP | 주요 code | 우리 처리 |
| --- | --- | --- |
| 400 | `VALIDATION_FAILED` | 요청 조립 오류. 공통 500 |
| 401 | `HMAC_*` | 서명·시각 문제. 공통 500 |
| 403 | `APPROVAL_*` | 승인 JWT 문제. 공통 500 |
| 404 | `WALLET_NOT_FOUND` | 지갑 미준비. 공통 500 |
| 409 | `METADATA_NOT_READY`, `IDEMPOTENCY_CONFLICT`, `TRANSFER_OWNER_MISMATCH` 등 | 업무 충돌. 도메인 정책에 따라 처리 |
| 429·5xx | — | 같은 멱등키로 제한적 재시도 |

---

## 3. 영향받는 기존 API

| API | 변화 |
| --- | --- |
| `POST /api/v1/cubes/verification` | 요청·응답 형식 변화 없음. 내부적으로 Mint를 수행하고 확정까지 대기한다 |
| `PATCH /api/v1/users/me/trades/{tradeId}/complete` | 요청·응답 형식 변화 없음. 인증서 값이 예시값이 아니라 실제 온체인 값으로 채워진다 |
