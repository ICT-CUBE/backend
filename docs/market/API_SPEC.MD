## 마켓 조회
- http 메서드: get
- domain: market
- endpoint: api/v1/users/me/market

### API 설명

사용자가 마켓 홈 화면에 진입하면 호출한다.

현재 사용자에게 표시할 프로필 정보와 제품 종류별 대표 큐브 및 최근 체결가를 반환한다.

---

### 처리 정책

- 현재 사용자의 `ownership_status = ACTIVE`이고 `is_last_accessed = true`인 큐브 소유권을 기준으로 상단 프로필 정보를 조회한다.
- 조건을 충족하는 큐브 소유권이 없으면 404: CUBE_OWNERSHIP_NOT_FOUND를 반환한다.
- 해당 큐브 소유권에 연결된 친밀도 정보가 없으면 404: CUBE_AFFINITY_NOT_FOUND를 반환한다.
- 프로필 이미지 URL은 현재 사용자의 `profile_character_img_url`, 아바타 닉네임은 현재 큐브 소유권의 `avatar_nickname`을 반환한다.
- 현재 친밀도 레벨은 `affinity.level_id`로 연결된 레벨의 숫자와 이름을 반환한다.
- `totalTradeCount`는 현재 사용자가 구매자 또는 판매자로 참여한 `COMPLETED` 거래 수로 계산한다.
- 마켓 상품은 큐브의 `product_name`이 완전히 같은 큐브끼리 하나의 제품군으로 묶는다.
- 제품명 비교 시 대소문자, 공백 또는 별도 문자열 정규화를 적용하지 않는다.
- 삭제된 큐브와 `status = DISABLED`인 큐브는 제품군 구성에서 제외한다.
- 삭제되지 않은 `market_product`가 연결된 큐브만 제품군 구성에 사용한다.
- 각 제품군에서 `cube.id`가 가장 작은 큐브를 대표 큐브로 선정한다.
- `representativeCubeId`, `marketProductId`, 제품명, 아티스트명과 이미지는 대표 큐브 및 대표 큐브의 마켓 상품에서 가져온다.
- 대표 마켓 상품의 `product_image_url`이 없으면 `productImageUrl`은 `null`로 반환한다.
- `latestTradePrice`는 같은 제품명에 속한 모든 시리얼 큐브의 거래 중 가장 최근에 체결된 거래를 기준으로 계산한다.
- `PAID`, `SENT`, `SHIPPING`, `DELIVERED`, `COMPLETED` 상태의 거래를 체결된 거래로 본다.
- 최근 거래는 `trade.paid_time DESC`, 동일한 결제 시각이면 `trade.id DESC` 순으로 결정한다.
- 체결가는 `trade.total_price`가 아닌 해당 거래에 연결된 `sell_listing.price`를 사용한다.
- 거래가 생성된 판매글은 이후 삭제되었더라도 과거 체결가 계산에 포함한다.
- 제품군에 체결된 거래가 없으면 `latestTradePrice`는 `null`로 반환한다.
- 제품 목록은 대표 큐브 id 오름차순으로 정렬하고 페이지네이션 없이 전체 반환한다.
- 조회 가능한 제품군이 없으면 `products`를 빈 배열로 반환한다.

---

### 요청 Query

없음

---

### 요청 Path

없음

---

### 요청 Body

없음

---

### 정상 응답 데이터

Status Code : 200

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `profile.profileCharacterImgUrl` | string | null | 현재 사용자의 프로필 캐릭터 이미지 URL |
| `profile.avatarNickname` | string | null | 현재 마지막 접근 활성 큐브의 아바타 닉네임 |
| `profile.level` | number | 현재 친밀도 레벨 숫자 |
| `profile.levelName` | string | 현재 친밀도 레벨명 |
| `profile.totalTradeCount` | number | 현재 사용자가 구매자 또는 판매자로 참여한 완료 거래 수 |
| `products` | array | 제품명별 대표 마켓 상품 목록 |
| `products[].representativeCubeId` | number | 제품군에서 id가 가장 작은 대표 큐브 id |
| `products[].marketProductId` | number | 대표 큐브에 연결된 마켓 상품 id |
| `products[].productName` | string | 대표 큐브 제품명 |
| `products[].artistName` | string | 대표 큐브 아티스트명 |
| `products[].productImageUrl` | string | null | 대표 마켓 상품 이미지 URL |
| `products[].latestTradePrice` | number | null | 같은 제품명의 모든 시리얼 큐브 중 가장 최근 체결된 판매글 가격 |

```json
{
  "profile": {
    "profileCharacterImgUrl": "https://haniumstorage.blob.core.windows.net/hanium/profile_image/profile_002.png",
    "avatarNickname": "젠득이",
    "level": 3,
    "levelName": "Close",
    "totalTradeCount": 24
  },
  "products": [
    {
      "representativeCubeId": 1,
      "marketProductId": 1,
      "productName": "JENNIE RUBY CUBE",
      "artistName": "JENNIE",
      "productImageUrl": "https://haniumstorage.blob.core.windows.net/hanium/cube_images/Icon%20Background.png",
      "latestTradePrice": 12500
    },
    {
      "representativeCubeId": 2,
      "marketProductId": 2,
      "productName": "BIGBANG MADE CUBE",
      "artistName": "BIGBANG",
      "productImageUrl": "https://haniumstorage.blob.core.windows.net/hanium/cube_images/cube%20card.png",
      "latestTradePrice": null
    }
  ]
}
```

---

### 오류 응답 데이터

Status Code : 404

현재 사용자의 활성 마지막 접근 큐브 소유권을 찾을 수 없는 경우

```json
{
  "code": "CUBE_OWNERSHIP_NOT_FOUND",
  "message": "큐브 소유권 정보를 찾을 수 없습니다."
}
```

큐브 소유권에 연결된 친밀도 정보를 찾을 수 없는 경우

```json
{
  "code": "CUBE_AFFINITY_NOT_FOUND",
  "message": "큐브 친밀도 정보를 찾을 수 없습니다."
}
```


## 마켓 세부 상품 조회
- http 메서드: get
- domain: market
- endpoint: api/v1/users/me/market/products/{representativeCubeId}/sell-listings

### API 설명

사용자가 마켓 홈에서 제품군을 선택하면 호출한다.

대표 큐브와 같은 제품명의 시리얼 큐브를 판매하는 판매글 전체를 반환한다.

---

### 처리 정책

- 프론트는 마켓 조회 API에서 받은 `representativeCubeId`를 Path로 전달한다.
- `representativeCubeId`에 해당하는 큐브의 `product_name`을 제품군 조회 기준으로 사용한다.
- 대표 큐브가 존재하지 않거나 삭제되었거나 `status = DISABLED`이면 404: MARKET_PRODUCT_NOT_FOUND를 반환한다.
- 대표 큐브에는 삭제되지 않은 `market_product`가 연결되어 있어야 한다.
- 큐브의 `product_name`이 대표 큐브의 제품명과 완전히 같은 모든 시리얼 큐브를 조회한다.
- 제품명에는 대소문자, 공백 또는 별도 문자열 정규화를 적용하지 않는다.
- 아티스트명은 제품군을 구분하는 조건으로 사용하지 않는다.
- 삭제되었거나 `status = DISABLED`인 큐브와 삭제된 마켓 상품은 제외한다.
- 판매글은 `status = ACTIVE`이고 `deleted_at IS NULL`인 판매 중인 항목만 반환한다.
- 제품 상태, 가격 또는 판매자 등에 대한 별도 Query 필터는 제공하지 않는다.
- `sellerNickname`은 판매글 작성자의 `user.nickname`을 반환한다.
- `likeCount`는 해당 판매글의 `selling_list_like.is_liked = true`인 행의 수로 계산하며 좋아요가 없으면 0을 반환한다.
- 판매글은 id 내림차순으로 정렬하고 페이지네이션 없이 전체 반환한다.
- 판매 중인 판매글이 없으면 `sellListings`를 빈 배열로 반환한다.

---

### 요청 Query

없음

---

### 요청 Path

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `representativeCubeId` | number | O | 마켓 조회 API에서 반환된 제품군 대표 큐브 id |

```json
{
  "representativeCubeId": 3
}
```

---

### 요청 Body

없음

---

### 정상 응답 데이터

Status Code : 200

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `sellListings` | array | 같은 제품명의 시리얼 큐브를 판매 중인 판매글 목록 |
| `sellListings[].sellListingId` | number | 판매글 id |
| `sellListings[].productName` | string | 판매 중인 큐브 제품명 |
| `sellListings[].serialNumber` | string | 판매 중인 물리 큐브 시리얼 번호 |
| `sellListings[].sellerNickname` | string | 판매자 닉네임 |
| `sellListings[].price` | number | 판매글에 등록된 판매 가격 |
| `sellListings[].likeCount` | number | 현재 좋아요 상태인 판매글 좋아요 수 |

```json
{
  "sellListings": [
    {
      "sellListingId": 3,
      "productName": "ROSE ROISE CUBE",
      "serialNumber": "NO.0099",
      "sellerNickname": "로제짱",
      "price": 42000,
      "likeCount": 1
    },
    {
      "sellListingId": 2,
      "productName": "ROSE ROISE CUBE",
      "serialNumber": "NO.0022",
      "sellerNickname": "로제짱",
      "price": 35000,
      "likeCount": 1
    }
  ]
}
```

---

### 오류 응답 데이터

Status Code : 404

대표 큐브 또는 조회 기준이 되는 마켓 상품을 찾을 수 없는 경우

```json
{
  "code": "MARKET_PRODUCT_NOT_FOUND",
  "message": "마켓 제품 정보를 찾을 수 없습니다."
}
```