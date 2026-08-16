## 거래 진행 정보 생성
- http 메서드: POST
- 엔드포인트: `/api/v1/users/me/trades`
- 도메인: market

### API 설명

주문 확인 화면에서 사용자가 에스크로 결제 진행 버튼을 누른 뒤 결제가 완료되면 호출한다.

요청값을 기준으로 `trade` 테이블에 거래 진행 정보를 생성한다.

---

### 처리 정책

- `buyer_user_id`는 결제하기를 호출한 현재 사용자의 ID로 저장한다. (로그인 구현 전에는 항상 id=1)
- `sellListingId`에 해당하는 판매 상품이 존재하고, 판매 상품의 `status = ACTIVE`이며, `deleted_at IS NULL`인 경우에만 거래를 생성한다. 
- 판매 상품이 존재하지 않거나, `status = SOLD`, `status = DELETED`, 또는 `deleted_at IS NOT NULL`이면 404: SELL_LISTING_INVALID를 반환한다.
- 이미 해당 판매 상품에 거래가 생성되어 있으면 409: TRADE_ALREADY_EXISTS를 반환한다.
- 현재 사용자가 등록한 판매 상품이면 자기 상품 구매를 막기 위해 409: SELF_TRADE_NOT_ALLOWED를 반환한다.
- `trade.status`는 `PAID`로 저장한다.
- `trade.paid_time`은 프론트에서 전달한 `paidTime` 값을 저장한다.
- `paidTime`은 offset 없는 ISO 8601 date-time만 허용한다. 예: `2026-08-15T21:30:00`
- `sent_time`, `shipped_time`, `delivered_time`, `completed_time`은 `null`로 저장한다.
- 거래 생성이 완료되면 `sell_listing.status`를 `SOLD`로 변경한다.

---

### 요청 Query

없음

---

### 요청 Path

없음

---

### 요청 Body

| 필드 | 타입 | 필수 | 설명 |
|---|---:|:---:|---|
| `sellListingId` | number | O | 거래를 생성할 판매 상품 id |
| `buyerAddress` | string | O | 구매자 배송 주소 |
| `buyerPhoneNumber` | string | O | 구매자 연락처 |
| `totalPrice` | number | O | 배송비 등을 포함한 최종 결제 금액 |
| `paidTime` | string(date-time) | O | 결제 완료 시각 |

```json
{
  "sellListingId": 1,
  "buyerAddress": "서울특별시 강남구 테헤란로 429,1934호",
  "buyerPhoneNumber": "010-4282-4533",
  "totalPrice": 12740,
  "paidTime": "2026-08-15T21:30:00"
}
```

---

### 정상 응답 데이터
Status Code : 204

응답 Body 없음


---

### 오류 응답 데이터
Status Code : 404

판매 상품이 존재하지 않거나 거래 생성 가능한 상태가 아닌 경우

```json
{
  "code": "SELL_LISTING_INVALID",
  "message": "판매 상품이 유효하지 않습니다."
}
```


Status Code : 409

이미 거래가 생성된 판매 상품인 경우

```json
{
  "code": "TRADE_ALREADY_EXISTS",
  "message": "이미 거래가 생성된 판매 상품입니다."
}
```

현재 사용자가 자신이 등록한 판매 상품을 구매하려는 경우

```json
{
  "code": "SELF_TRADE_NOT_ALLOWED",
  "message": "자신이 등록한 판매 상품은 구매할 수 없습니다."
}
```




## 주문 상세 조회
- http 메서드: GET
- 엔드포인트: `/api/v1/users/me/trades/{tradeId}`
- 도메인: market

### API 설명

거래 내역 화면에서 사용자가 특정 거래를 클릭했을 때 호출한다.

`tradeId`를 기준으로 거래 상세 정보와 거래 진행 상태 타임라인을 조회한다.

---

### 처리 정책

- `tradeId`에 해당하는 거래가 존재하면 거래 상태와 상품 정보를 반환한다.
- 현재 사용자가 구매자인 거래만 조회할 수 있다. 로그인 구현 전에는 `trade.buyer_user_id = 1`인 거래만 조회한다.
- 거래 상태가 `PAID`, `SENT`, `SHIPPING`, `DELIVERED`, `COMPLETED` 중 어떤 상태이든 조회할 수 있다.
- 거래가 완료된 이후에도 주문 상세 조회는 가능하다.
- `tradeId`에 해당하는 거래가 존재하지 않거나, 현재 사용자가 구매자인 거래가 아니면 404: TRADE_NOT_FOUND를 반환한다.
- 로그인 구현 전에는 현재 사용자를 항상 id=1로 간주한다.
- 날짜/시간 값은 한국시간 기준 offset 없는 ISO 8601 형식으로 반환한다.
- 각 진행 단계의 시각은 `trade` 테이블의 시간 컬럼을 그대로 사용한다.
  - 결제 완료: `paid_time`
  - 판매자 발송: `sent_time`
  - 배송 중: `shipped_time`
  - 배송 완료: `delivered_time`
  - 구매 확정: `completed_time`
- 아직 도달하지 않은 거래 단계의 시각은 `null`로 반환한다.

---

### 요청 Query

없음

---

### 요청 Path

| 필드 | 타입 | 필수 | 설명 |
|---|---:|:---:|---|
| `tradeId` | number | O | 조회할 거래 id |

요청 예시: /api/v1/users/me/trades/23

---

### 요청 Body

없음

---

### 정상 응답 데이터
Status Code : 200
| 필드 | 타입 | 설명 |
|---|---:|---|
| `trade.id` | number | 거래 id |
| `trade.paidTime` | string(date-time) | 결제 완료 시각 |
| `trade.price` | number | 판매글에 등록된 상품 가격 |
| `trade.productImageUrl` | string \| null | 마켓 상품 이미지 URL |
| `trade.cube.id` | number | 큐브 id |
| `trade.cube.serialNumber` | string | 큐브 시리얼 번호 |
| `trade.cube.productName` | string | 큐브 상품명 |
| `trade.cube.artistName` | string | 아티스트 이름 |
| `trade.timeline[].status` | string | 거래 단계 상태 코드 |
| `trade.timeline[].label` | string | 화면 표시용 거래 단계 이름 |
| `trade.timeline[].time` | string(date-time) \| null | 해당 단계가 기록된 시각 |
| `trade.timeline[].completed` | boolean | 해당 단계 완료 여부 |

```json
{
  "trade": {
    "id": 1,
    "paidTime": "2026-08-05T14:30:00",
    "price": 12500,
    "productImageUrl": "https://example.com/mock/market-product-001.jpg",
    "cube": {
      "id": 1,
      "serialNumber": "#012",
      "productName": "RUBY CUBE",
      "artistName": "JENNIE"
    },
    "timeline": [
      {
        "status": "PAID",
        "label": "결제 완료",
        "time": "2026-08-05T14:30:00",
        "completed": true
      },
      {
        "status": "SENT",
        "label": "판매자 발송",
        "time": "2026-08-05T15:09:00",
        "completed": true
      },
      {
        "status": "SHIPPING",
        "label": "배송 중",
        "time": "2026-08-07T09:45:00",
        "completed": true
      },
      {
        "status": "DELIVERED",
        "label": "배송 완료",
        "time": null,
        "completed": false
      },
      {
        "status": "COMPLETED",
        "label": "구매 확정",
        "time": null,
        "completed": false
      }
    ]
  }
}
```


### 오류 응답 데이터
Status Code : 404

```json
{
  "code": "TRADE_NOT_FOUND",
  "message": "거래 정보를 찾을 수 없습니다."
}
```



## 구매 확정
- http 메서드: PATCH
- 엔드포인트: `/api/v1/users/me/trades/{tradeId}/complete`
- 도메인: market

### API 설명

주문 상세 조회 화면에서 사용자가 구매 확정 버튼을 눌렀을 때 호출한다.

`tradeId`를 기준으로 거래를 구매 확정 상태로 변경하고, 디지털 소유권 인증서 데이터를 생성한 뒤 인증서 화면에 필요한 정보를 반환한다.

---

### 처리 정책

- 현재 사용자가 구매자인 거래만 구매 확정할 수 있다. 로그인 구현 그전에는 `trade.buyer_user_id = 1`인 거래만 처리한다.
- `tradeId`에 해당하는 거래가 존재하지 않거나, 현재 사용자가 구매자인 거래가 아니면 404: TRADE_NOT_FOUND를 반환한다.
- 구매 확정은 `trade.status = DELIVERED`인 거래에서만 가능하다.
- `trade.status`가 `DELIVERED`가 아니면 409: TRADE_NOT_DELIVERED를 반환한다.
- API 호출이 성공하면 `trade.status`를 `COMPLETED`로 변경한다.
- API 호출이 성공하면 `trade.completed_time`을 서버의 현재 한국시간 기준 offset 없는 datetime으로 저장한다.
- 구매 확정과 동시에 `digital_certificate` 데이터를 생성한다.
- `digital_certificate.trade_id`는 구매 확정된 거래 id로 저장한다.
- 인증서의 블록체인 관련 값은 현재 실제 블록체인 연동 전이므로 서버에서 생성한 개발용 값을 저장하고 반환한다.
- 이미 해당 거래의 디지털 인증서가 존재하는 경우는 정상 흐름에서는 발생하지 않는다고 가정한다.

---

### 요청 Query

없음

---

### 요청 Path

| 필드 | 타입 | 필수 | 설명 |
|---|---:|:---:|---|
| `tradeId` | number | O | 구매 확정할 거래 id |

요청 예시: /api/v1/users/me/trades/23/complete

---

### 요청 Body

없음

---

### 정상 응답 데이터
Status Code : 200

| 필드 | 타입 | 설명 |
|---|---:|---|
| `certificate.id` | number | 디지털 인증서 id |
| `certificate.tradeId` | number | 인증서가 연결된 거래 id |
| `certificate.ownerNickname` | string \| null | 구매 확정을 진행한 사용자 닉네임 |
| `certificate.completedTime` | string(date-time) | 구매 확정 완료 시각 |
| `certificate.network` | string | 블록체인 네트워크 |
| `certificate.tokenStandard` | string | 토큰 표준 |
| `certificate.tokenId` | string | 토큰 id |
| `certificate.contractAddress` | string | 컨트랙트 주소 |
| `certificate.txHash` | string | 트랜잭션 해시 |
| `certificate.metadataUrl` | string | 메타데이터 URL |

```json
{
  "certificate": {
    "id": 1,
    "tradeId": 23,
    "ownerNickname": "홍길동",
    "completedTime": "2026-08-10T18:43:00",
    "network": "Polygon Mainnet",
    "tokenStandard": "ERC-721",
    "tokenId": "31",
    "contractAddress": "0s3a82f9c41",
    "txHash": "0s3a82f6f8b12",
    "metadataUrl": "IPFS Encrypted"
  }
}
```

### 오류 응답 데이터
Status Code : 404

거래가 존재하지 않거나 현재 사용자가 구매자인 거래가 아닌 경우

```json
{
  "code": "TRADE_NOT_FOUND",
  "message": "거래 정보를 찾을 수 없습니다."
}
```

Status Code : 409

거래가 배송 완료 상태가 아니라 구매 확정을 진행할 수 없는 경우

```json
{
  "code": "TRADE_NOT_DELIVERED",
  "message": "배송 완료 상태인 거래만 구매 확정할 수 있습니다."
}
```
