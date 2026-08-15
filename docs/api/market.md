## 거래 진행 정보 생성
- http 메서드: POST
- 엔드포인트: `/api/v1/users/me/trades`
- 도메인: market

### API 설명

주문 확인 화면에서 사용자가 에스크로 결제 진행 버튼을 누른 뒤 결제가 완료되면 호출한다.

요청값을 기준으로 `trade` 테이블에 거래 진행 정보를 생성한다.

---

### 처리 정책

- `buyer_user_id`는 결제하기를 호출한 현재 사용자의 ID로 저장한다. (로그인 전에는 id=1)
- `sellListingId`에 해당하는 판매 상품이 존재하고, `status = ACTIVE`이며, `deleted_at IS NULL`인 경우에만 거래를 생성한다. 
- 판매 상품이 존재하지 않거나, `status = SOLD`, `status = DELETED`, 또는 `deleted_at IS NOT NULL`이면 404를 반환한다.
- `trade.status`는 `PAID`로 저장한다.
- `trade.paid_time`은 프론트에서 전달한 `paidTime` 값을 저장한다.
- `sent_time`, `shipped_time`, `delivered_time`, `completed_time`은 `null`로 저장한다.

---

### 요청 Query

없음

---

### 요청 Path

없음

---

### 요청 Body

```json
{
  "sellListingId": 1,
  "buyerAddress": "서울특별시 강남구 테헤란로 429,1934호",
  "buyerPhoneNumber": "010-4282-4533  ",
  "totalPrice": 12740,
  "paidTime": "2026-08-15T21:30:00"
}
```

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `sellListingId` | number | O | 결제를 진행한 판매글 ID |
| `buyerAddress` | string | O | 구매자 배송 주소 |
| `buyerPhoneNumber` | string | O | 구매자 전화번호 |
| `totalPrice` | number | O | 최종 결제 금액 |
| `paidTime` | string(date-time) | O | 결제 완료 시간 |

---

### 정상 응답 데이터
Status Code : 201

```json
{
  "trade": {
    "id": 1,
    "sellListingId": 1,
    "buyerUserId": 1,
    "buyerAddress": "서울특별시 강남구 테헤란로 123",
    "buyerPhoneNumber": "010-1234-5678",
    "totalPrice": 12740,
    "paidTime": "2026-08-15T21:30:00",
    "sentTime": null,
    "shippedTime": null,
    "deliveredTime": null,
    "completedTime": null,
    "status": "PAID"
  }
}
```

---

### 오류 응답 데이터
Status Code : 404

```json
{
  "code": "SELL_LISTING_INVALID",
  "message": "판매 상품이 유효하지 않습니다."
}
```
