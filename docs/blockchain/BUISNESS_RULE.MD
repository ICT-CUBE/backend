# 블록체인 연동 비즈니스 룰

## 연동 범위

- 큐브 최초 인증 성공 시 NFT를 발행(Mint)한다.
- 마켓 구매 확정 시 NFT를 구매자에게 이전(Transfer)한다.
- 출금, 재진입, 외부 재판매는 이번 범위에서 구현하지 않는다.
- 운영자 감사 API(`/internal/v1/audit/*`)는 호출하지 않으며 operator key도 사용하지 않는다.

## 요청 서명 (HMAC)

- `/health`, `/ready`를 제외한 모든 호출에 `X-ARZONE-Key-Id`, `X-ARZONE-Timestamp`, `X-ARZONE-Nonce`, `X-ARZONE-Signature` 헤더를 붙인다.
- `X-ARZONE-Timestamp`는 Unix seconds이며 서버 허용 범위는 ±300초다.
- `X-ARZONE-Nonce`는 요청마다 새 UUID를 생성하고 재사용하지 않는다.
- 서명 대상 문자열은 다음 5줄을 개행으로 이은 값이다.

```text
UPPERCASE_METHOD
normalized_path?sorted_query
timestamp
nonce
lowercase_hex_sha256(raw_body)
```

- `normalized_path?sorted_query`는 쿼리 키를 정렬하고 같은 키의 값도 정렬한 뒤 각 키·값을 URL 인코딩해 조합한다. 쿼리가 없으면 경로만 사용한다.
- 본문 해시는 실제로 전송하는 raw bytes를 기준으로 계산하며, 직렬화를 다시 수행하지 않는다.
- 서명은 base64url로 저장된 secret을 디코딩한 바이트로 HMAC-SHA-256을 계산하고 소문자 hex로 표기한다.
- 재시도할 때는 timestamp와 nonce를 새로 만들어 다시 서명한다.

## 승인 JWT

- 소유권을 바꾸는 `POST /mints`, `POST /transfers`에만 `Authorization: Bearer` 헤더로 승인 JWT를 함께 보낸다.
- 서명은 HS256이며 HMAC secret과 다른 `BLOCKCHAIN_APPROVAL_JWT_SECRET`을 사용한다.
- 공통 claim은 `jti`(요청마다 새 UUID), `iss`, `aud`, `iat`, `exp`, `purpose`, `tokenId`다.
- 유효기간은 30분을 넘길 수 없으며, 요청 직전에 발급한다.
- `purpose = MINT`는 `userId`, `cubeId`, `to`를 추가로 담는다.
- `purpose = TRANSFER`는 `tradeId`, `sellerUserId`, `buyerUserId`, `from`, `to`를 추가로 담는다.
- `to`와 `from`은 `POST /internal/v1/wallets` 응답의 주소를 그대로 사용한다.
- 같은 `jti`를 재사용하면 409 `APPROVAL_JTI_REPLAY`가 되므로, 재시도 시에도 JWT를 새로 발급한다.

## 식별자 규칙

- `userId`, `cubeId`, `tradeId`는 접두사 없이 Backend의 BIGINT를 문자열로 변환해 보낸다. 예: `"1"`.
- `tokenId`는 큐브 시리얼 번호의 숫자 부분을 사용한다. `NO.0026` → `26`, `NO.0100` → `100`.
- 시리얼 번호가 `NO.` + 숫자 형식이 아니거나, 변환값이 1~10000 범위를 벗어나면 Mint를 시도하지 않고 실패로 기록한다.
- `tokenId`는 큐브와 1:1이므로 다른 큐브가 같은 `tokenId`를 사용할 수 없다.
- 멱등키(`idempotencyKey`)는 작업마다 새 UUID를 생성해 저장하고, 재시도할 때는 저장한 값을 그대로 다시 사용한다.

## 수탁 지갑

- 지갑 주소는 우리 DB에 저장하지 않는다.
- Mint·Transfer 직전에 `POST /internal/v1/wallets`를 호출해 주소를 확보한다. 이 API는 기존 지갑이 있으면 그대로, 없으면 새로 만들어 항상 200으로 응답한다.
- Transfer는 판매자와 구매자 각각에 대해 호출해 `from`, `to`를 채운다.

## NFT 메타데이터

- 메타데이터는 Mint 직전에 `POST /internal/v1/metadata`로 준비한다.
- 허용 필드만 보낸다: `tokenId`, `cubeNumber`, `publicGrade`, `imageBase64`, `imageMimeType`, `benefitReferenceId`. 그 외 키를 넣으면 400이 된다.
- `cubeNumber`에는 원본 시리얼 번호(`NO.0026`)를 그대로 넣는다.
- `publicGrade`는 고정값 `UNSPECIFIED`, `benefitReferenceId`는 고정값 `NONE`을 사용한다.
- 이미지는 판매자가 올린 `listing_media`가 아니라 `market_product.product_image_url`의 공식 제품 이미지를 사용한다.
- 이미지는 URL에서 내려받아 base64로 변환해 보내며, 디코딩 크기가 2 MiB를 넘거나 PNG·JPEG·WebP·GIF가 아니면 Mint를 시도하지 않고 실패로 기록한다.
- 응답의 `ready`가 `true`일 때만 Mint를 요청한다. `false`면 `GET /internal/v1/metadata/{tokenId}`로 다시 확인한다.

## 큐브 최초 인증 시 Mint

- 큐브 인증번호 검증에 성공하고 큐브 소유권·친밀도·1레벨 보상 저장을 커밋한 뒤에 Mint를 진행한다.
- DB 트랜잭션을 연 상태로 외부 API를 호출하지 않는다.
- 순서는 지갑 확보 → 메타데이터 준비 → 승인 JWT 발급 → `POST /internal/v1/mints`다.
- `202` 응답의 `operationId`와 멱등키를 저장한 뒤 확정될 때까지 대기한다.
- Mint가 실패하거나 대기 시간을 초과해도 인증 API는 기존과 같이 `201`과 `cubeOwnershipId`를 반환한다.
- 큐브 인증 자체는 이미 완료된 것으로 보고, 실패한 Mint는 작업 기록에 남겨 나중에 재시도한다.

## 구매 확정 시 Transfer

- 기존 구매 확정 API의 거래 검증을 모두 통과한 뒤에 Transfer를 진행한다.
- 순서는 판매자·구매자 지갑 확보 → 승인 JWT 발급 → `POST /internal/v1/transfers`다.
- `202` 응답의 `operationId`와 멱등키를 저장한 뒤 확정될 때까지 대기한다.
- 확정되면 `GET /internal/v1/nfts/{tokenId}`를 한 번 호출해 컨트랙트 주소와 tokenURI를 확보한다.
- 확보한 값으로 `digital_certificate`를 생성한다.
  - `network`: 설정값 `BLOCKCHAIN_NETWORK`
  - `token_standard`: `ERC-721`
  - `token_id`: 시리얼 숫자 부분을 문자열로 변환한 값
  - `tx_hash`: 완료 알림의 `txHash`
  - `contract_address`: NFT 조회 API의 `contractAddress`
  - `metadata_url`: NFT 조회 API의 `metadataUri`
- 구매 확정 API의 요청·응답 형식은 바꾸지 않으며, 인증서 값만 실제 온체인 값으로 채운다.
- NFT 이전을 요청하기 전에 같은 거래의 확정된 이전 작업이 있는지 먼저 조회한다.
- 확정된 작업이 있으면 다시 이전을 요청하지 않고 그 결과로 인증서를 만든다.
- 확정 대기가 시간을 넘겨 오류로 응답한 뒤 사용자가 다시 요청해도 중복 이전이 일어나지 않는다.
- 거래 조회·검증을 마치면 거래 행 잠금을 풀고 외부 호출을 시작한다.
- 외부 호출을 마친 뒤 거래 상태를 다시 확인하고, 그 사이 확정됐으면 오류로 응답한다.
- NFT 이전 접수가 거절되면 `409 TRADE_TRANSFER_REJECTED`를 반환한다.
- 확정 대기 시간을 넘기면 `409 TRADE_CONFIRMATION_TIMEOUT`을 반환한다.
- 블록체인 서버에 연결하지 못하면 공통 `500 INTERNAL_SERVER_ERROR`를 반환한다.

## 확정 대기

- 확정 대기는 `GET /internal/v1/operations/{operationId}` 폴링으로 수행한다.
- 상태가 `ONCHAIN_CONFIRMED` 또는 `COMPLETED`가 되면 확정으로 본다.
- 대기 제한 시간은 120초이며, 초과하면 폴링을 멈추고 작업 기록을 대기 상태로 남긴다.
- `REQUESTED`, `SUBMITTED`, `PENDING`, `UNKNOWN`은 실패로 단정하지 않고 계속 대기하거나 대기 상태로 남긴다.
- `FAILED`, `REVIEW_REQUIRED`, `CANCELLED`는 즉시 대기를 끝내고 실패로 기록한다.
- 확정된 작업의 `finalOwnerAddress`가 기대한 소유자 주소와 다르면 성공으로 처리하지 않고 실패로 기록한다.

## 완료 알림 처리

- 완료 알림은 확정 대기와 무관하게 중복 수신될 수 있다.
- 이미 저장한 `notificationId`가 다시 오면 저장하지 않고 `duplicate = true`로 200을 반환한다.
- 알림으로 받은 `operationId`가 우리 작업 기록에 없으면 저장하지 않고 200으로 수락한다.
- 이미 확정 처리한 작업에 알림이 뒤늦게 도착해도 인증서를 다시 만들지 않는다.
- 대기 시간 초과로 확정하지 못한 작업은 알림을 받은 시점에 확정 처리한다.
- 작업 기록은 `REQUESTED`, `CONFIRMED`, `FAILED` 세 가지 상태로만 관리한다.
- 확정 전 상태는 모두 `REQUESTED`로 두고, 접수 실패와 온체인 실패는 실패 사유와 함께 `FAILED`로 남긴다.

## 실패 처리

- 블록체인 서버 호출이 실패하거나 응답이 오류이면 작업 기록에 실패 사유를 남긴다.
- 구매 확정 중 Transfer 접수 자체가 실패하면 구매 확정 API를 오류로 응답한다.
- 큐브 인증 중 Mint가 실패하면 인증 API는 성공으로 응답하고 실패만 기록한다.
- 확정 대기 시간을 초과하면 저장한 `operationId`로 나중에 상태를 재조회한다.
- 롤백이 필요한 온체인 보상 처리는 하지 않는다.

## 개발용 백필 Mint

- 목데이터로 이미 `OWNED` 상태인 큐브도 거래를 시험할 수 있도록 백필 Mint 스크립트를 제공한다.
- 대상은 `ownership_status = ACTIVE`인 큐브 소유권이다.
- 각 큐브마다 `GET /internal/v1/nfts/{tokenId}`로 발행 여부와 현재 소유자를 먼저 확인한다.
- 이미 같은 소유자가 보유하고 있으면 건너뛴다.
- 발행되지 않았으면 현재 소유자 앞으로 Mint한다.
- 다른 소유자가 보유하고 있으면 그 큐브 처리를 중단하고 기록만 남긴다.
- 서버 기동 시 자동 실행하지 않고, 로컬·데모 환경에서 수동으로 실행하는 명령으로 제공한다.
- 처리 결과는 큐브마다 `MINTED`, `ALREADY_MINTED`, `OWNED_BY_OTHER`, `SKIPPED`, `FAILED` 중 하나로 남긴다.
- 한 큐브가 실패해도 나머지 큐브 처리를 계속한다.

## 설정값

| 환경변수 | 설명 |
| --- | --- |
| `BLOCKCHAIN_BASE_URL` | 블록체인 서버 주소 |
| `BLOCKCHAIN_NETWORK` | `digital_certificate.network`에 저장할 네트워크 이름 |
| `BLOCKCHAIN_HMAC_KEY_ID` / `BLOCKCHAIN_HMAC_KEY_SECRET` | 요청 서명용 inbound key |
| `BLOCKCHAIN_APPROVAL_JWT_SECRET` / `_ISSUER` / `_AUDIENCE` | 승인 JWT 설정 |
| `BLOCKCHAIN_WEBHOOK_HMAC_KEY_ID` / `_SECRET` | webhook 서명 검증용 outbound key |

- secret은 `.env`로만 주입하고 저장소에 커밋하지 않는다.
- `BLOCKCHAIN_BASE_URL`은 Backend가 Docker로 실행될 때 `127.0.0.1`이 컨테이너 자신을 가리키므로 `host.docker.internal`을 사용한다.
- 환경변수 값에는 URL만 넣고 Markdown 링크 형식을 쓰지 않는다.
