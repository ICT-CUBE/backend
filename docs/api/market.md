## 거래 진행 정보 생성
- http 메서드: post
- 엔드포인트: api/v1/users/me/trades

### API 설명

사용자가 판매 사진에서 안전 에스크로 결제를 완료하면 호출된다.

결제가 완료된 거래 진행 정보를 DB에 저장하고, 생성된 거래 id를 반환한다.

- 고정 사용자 ID 1을 구매자로 저장한다.
- 판매자는 `sell_listing.user_id`를 사용한다.
- `trade.status`는 `PAID`로 저장한다.
- `escrow_payment.escrow_status`는 `PAID`로 저장한다.
- `escrow_payment.paid_at`은 서버가 저장하는 현재 한국 시간 기준 시각으로 저장한다.
- `shipment.shipment_status`는 `READY`로 저장한다.
- `trade.total_price`와 `escrow_payment.paid_amount`는 요청의 `paidAmount` 값으로 저장한다.
- 결제 완료 후 판매글은 거래 진행 중인 상태로 보고 `sell_listing.status`를 `SOLD`로 변경한다.

---

### 요청 Query

---

### 요청 Path

---

### 요청 Body

```json
{
  "sellListingId": 1201,
  "paymentMethod": "EASY_PAY",
  "paidAmount": 12740
}
```

- `sellListingId`: 결제를 진행한 판매글 id
- `paymentMethod`: 결제 수단
    - `CARD`
    - `BANK_TRANSFER`
    - `EASY_PAY`
- `paidAmount`: 에스크로로 결제 완료된 최종 금액

---

### 정상 응답 데이터

Status Code : 201

```json
{
  "trade": {
    "id": 3001,
    "status": "PAID",
    "escrowStatus": "PAID",
    "shipmentStatus": "READY"
  }
}
```

---

### 오류 응답 데이터

Status Code : 404

```json
{
  "code": "SELL_LISTING_NOT_FOUND",
  "message": "판매글을 찾을 수 없습니다."
}
```

- 존재하지 않는 판매글 id이거나 삭제된 판매글인 경우 위 응답을 반환한다.

Status Code : 409

```json
{
  "code": "SELL_LISTING_NOT_AVAILABLE",
  "message": "거래할 수 없는 판매글입니다."
}
```

- 판매글이 `ACTIVE` 상태가 아니거나, 대표 사용자 본인이 등록한 판매글인 경우 위 응답을 반환한다.
