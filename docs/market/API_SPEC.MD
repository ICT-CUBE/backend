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



## 마켓 검색 결과 조회
- http 메서드: get
- domain: market
- endpoint: api/v1/users/me/market/search

### API 설명

사용자가 마켓에서 키워드로 판매 상품을 검색할 때 호출한다.

큐브의 제품명 또는 아티스트명에 키워드가 포함된 마켓 상품을 찾고, 해당 상품을 판매 중인 판매글 전체를 반환한다.

---

### 처리 정책

- 프론트는 검색어를 `keyword` Query로 전달한다.
- `keyword`는 필수이며, 누락되거나 공백으로만 구성된 경우 공통 400: INVALID_REQUEST를 반환한다.
- 검색 전 키워드의 앞뒤 공백은 제거한다.
- `cube.product_name` 또는 `cube.artist_name`에 키워드가 포함된 큐브를 검색한다.
- 검색은 MySQL의 현재 문자열 비교 규칙에 따라 부분 일치로 처리한다.
- 키워드에 포함된 `%`, `_`, `\`는 와일드카드가 아닌 일반 문자로 검색한다.
- 검색된 큐브에는 삭제되지 않은 `market_product`가 연결되어 있어야 한다.
- 삭제되었거나 `status = DISABLED`인 큐브와 삭제된 마켓 상품은 제외한다.
- 판매글은 `status = ACTIVE`이고 `deleted_at IS NULL`인 판매 중인 항목만 반환한다.
- 하나의 판매글은 제품명과 아티스트명 조건을 모두 만족하더라도 한 번만 반환한다.
- `sellerNickname`은 판매글 작성자의 `user.nickname`을 반환한다.
- `likeCount`는 해당 판매글의 `selling_list_like.is_liked = true`인 행의 수로 계산하며 좋아요가 없으면 0을 반환한다.
- 판매글은 id 내림차순으로 정렬하고 페이지네이션 없이 전체 반환한다.
- 검색 결과가 없으면 오류를 반환하지 않고 `sellListings`를 빈 배열로 반환한다.

---

### 요청 Query

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `keyword` | string | O | 큐브 제품명 또는 아티스트명에서 검색할 키워드 |

```
GET /api/v1/users/me/market/search?keyword=ROSE
```

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
| `sellListings` | array | 검색된 제품을 판매 중인 판매글 목록 |
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

검색 결과가 없는 경우

```json
{
  "sellListings": []
}
```

---

### 오류 응답 데이터

이 API에서 별도로 정의하는 도메인 오류는 없음.

필수 Query 누락·공백 입력에 대한 400과 서버 내부 오류에 대한 500은 공통 오류 정책을 따른다.



## 거래 진행정보 생성
- http 메서드: post
- domain: market
- endpoint: api/v1/users/me/trades

### API 설명

주문 확인 화면에서 사용자가 결제하기 버튼을 눌러 결제가 완료되면 호출한다.

구매자 배송 정보와 판매글의 가격을 기준으로 거래 정보를 생성하고 판매 대상 큐브를 거래 대기 상태로 변경한다.

---

### 처리 정책

- `buyer_user_id`는 API를 호출한 현재 사용자의 id로 저장한다. 로그인 구현 전에는 항상 id=1을 사용한다.
- `sellListingId`에 해당하는 판매글이 존재하고, `status = ACTIVE`이며, `deleted_at IS NULL`인 경우에만 거래를 생성한다.
- 판매글에 연결된 마켓 상품과 큐브가 존재하고 삭제되지 않았으며, 큐브가 비활성화되지 않은 경우에만 거래를 생성한다.
- 판매글 또는 연결된 마켓 상품·큐브가 거래 가능한 상태가 아니면 404: SELL_LISTING_INVALID를 반환한다.
- 이미 해당 판매글에 거래가 생성되어 있으면 409: TRADE_ALREADY_EXISTS를 반환한다.
- 현재 사용자가 등록한 판매글이면 자기 상품 구매를 막기 위해 409: SELF_TRADE_NOT_ALLOWED를 반환한다.
- 구매자는 `buyerPhoneNumber`와 `buyerAddress`만 전달하며, 결제 금액과 결제 시각은 서버에서 결정한다.
- `trade.buyer_phone_number`와 `trade.buyer_address`에는 요청으로 받은 값을 저장한다.
- `trade.total_price`는 `sell_listing.price × 1.05`로 계산한다.
- 계산 결과 원 단위 미만의 소수점이 발생하면 버림 처리한다.
- 결제 금액은 프론트에서 전달받지 않으며 DB에 저장된 판매글 가격만 신뢰한다.
- `trade.paid_time`은 거래 생성 시점의 한국 표준시(KST)를 offset 없는 date-time으로 저장한다.
- `trade.sent_time`, `shipped_time`, `delivered_time`, `completed_time`은 `null`로 저장한다.
- `trade.status`는 `PAID`로 저장한다.
- 거래 생성이 완료되면 `sell_listing.status`를 `SOLD`로 변경한다.
- 판매글과 연결된 `cube.status`를 `TRADE_PENDING`으로 변경한다.
- 거래 생성, 판매글 상태 변경, 큐브 상태 변경은 하나의 DB 트랜잭션으로 처리한다.
- 정상 처리되면 서버가 계산한 최종 결제 금액만 반환한다.

---

### 요청 Query

없음

---

### 요청 Path

없음

---

### 요청 Body

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `sellListingId` | number | O | 구매할 판매글 id |
| `buyerPhoneNumber` | string | O | 구매자 연락처 |
| `buyerAddress` | string | O | 구매자 배송 주소 |

```json
{
  "sellListingId": 1,
  "buyerPhoneNumber": "010-4282-4533",
  "buyerAddress": "서울특별시 강남구 테헤란로 429, 1934호"
}
```

---

### 정상 응답 데이터

Status Code : 201

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `totalPrice` | number | 판매글 가격에 5%를 더해 서버가 계산한 최종 결제 금액 |

```json
{
  "totalPrice": 36750
}
```

---

### 오류 응답 데이터

Status Code : 404

판매글 또는 연결된 마켓 상품·큐브가 존재하지 않거나 거래 가능한 상태가 아닌 경우

```json
{
  "code": "SELL_LISTING_INVALID",
  "message": "판매 상품이 유효하지 않습니다."
}
```

Status Code : 409

이미 거래가 생성된 판매글인 경우

```json
{
  "code": "TRADE_ALREADY_EXISTS",
  "message": "이미 거래가 생성된 판매 상품입니다."
}
```

현재 사용자가 자신이 등록한 판매글을 구매하려는 경우

```json
{
  "code": "SELF_TRADE_NOT_ALLOWED",
  "message": "자신이 등록한 판매 상품은 구매할 수 없습니다."
}
```


## 판매글 상세 조회
- http 메서드: get
- domain: market
- endpoint: api/v1/users/me/sell-listings/{sellListingId}

### API 설명

사용자가 마켓 판매 목록 또는 검색 결과에서 판매글을 선택해 상세 화면에 진입할 때 호출한다.

판매글 정보, 판매자 닉네임, 판매 대상 큐브 정보와 판매글에 등록된 이미지 전체를 반환한다.

---

### 처리 정책

- 프론트는 판매 목록 또는 검색 결과에서 받은 `sellListingId`를 Path로 전달한다.
- 현재 사용자가 작성한 판매글인지 여부와 관계없이 조회할 수 있다.
- `sellListingId`에 해당하는 판매글이 존재하지 않으면 404: SELL_LISTING_NOT_FOUND를 반환한다.
- 판매글의 `status = DELETED`이거나 `deleted_at IS NOT NULL`이면 삭제된 판매글로 판단하고 404: SELL_LISTING_NOT_FOUND를 반환한다.
- 삭제되지 않은 판매글은 `ACTIVE` 또는 `SOLD` 상태와 관계없이 조회할 수 있다.
- `sellerNickname`은 판매글 작성자의 `user.nickname`을 반환한다.
- `sellerProfileImageUrl`은 판매글 작성자의 `user.profile_character_img_url`을 반환하며, 값이 없으면 `null`을 반환한다.
- `status`는 판매글의 현재 상태인 `ACTIVE` 또는 `SOLD`를 반환한다.
- `isMine`은 판매글 작성자의 사용자 id와 현재 사용자 id가 같으면 `true`, 다르면 `false`를 반환한다.
- 프론트는 `status = ACTIVE`이고 `isMine = false`인 경우에만 거래 진행 버튼을 활성화한다.
- `productName`과 `serialNumber`는 판매글의 마켓 상품과 연결된 큐브에서 조회한다.
- `imageUrls`에는 판매글과 연결된 모든 `listing_media.image_url`을 담는다.
- 판매글 이미지는 `listing_media.id` 오름차순으로 반환한다.
- 연결된 판매글 이미지가 없으면 `imageUrls`를 빈 배열로 반환한다.
- `createdAt`은 판매글의 `created_at`을 offset 없는 ISO 8601 date-time으로 반환한다.

---

### 요청 Query

없음

---

### 요청 Path

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `sellListingId` | number | O | 조회할 판매글 id |

```json
{
  "sellListingId": 1
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
| `sellListing` | object | 판매글 상세 정보 |
| `sellListing.sellListingId` | number | 판매글 id |
| `sellListing.imageUrls` | array&lt;string&gt; | 판매글에 등록된 이미지 URL 목록 |
| `sellListing.sellerNickname` | string | 판매자 닉네임 |
| `sellListing.sellerProfileImageUrl` | string | null | 판매자 프로필 이미지 URL. 등록된 이미지가 없으면 null |
| `sellListing.status` | string | 판매글 상태. ACTIVE 또는 SOLD |
| `sellListing.isMine` | boolean | 현재 사용자가 작성한 판매글인지 여부 |
| `sellListing.title` | string | 판매글 제목 |
| `sellListing.description` | string | 판매글 설명 |
| `sellListing.price` | number | 판매 가격 |
| `sellListing.createdAt` | string(date-time) | 판매글 등록 시각 |
| `sellListing.productName` | string | 판매 대상 큐브 제품명 |
| `sellListing.serialNumber` | string | 판매 대상 물리 큐브 시리얼 번호 |

```json
{
  "sellListing": {
    "sellListingId": 1,
    "imageUrls": [
      "https://haniumstorage.blob.core.windows.net/hanium/listing_media/1/1.jpg",
      "https://haniumstorage.blob.core.windows.net/hanium/listing_media/1/2.jpg"
    ],
    "sellerNickname": "uddystar_142",
    "sellerProfileImageUrl": "https://haniumstorage.blob.core.windows.net/hanium/profile/profile_1.png",
    "status": "ACTIVE",
    "isMine": false,
    "title": "제니 루비 큐브 1번 팝니다.",
    "description": "작년 팝업스토어에서 구매한 제니 솔로 큐브 양도합니다.",
    "price": 12500,
    "createdAt": "2026-08-28T20:30:00",
    "productName": "JENNIE RUBY CUBE",
    "serialNumber": "NO.0012"
  }
}
```

---

### 오류 응답 데이터

Status Code : 404

판매글이 존재하지 않거나 삭제된 경우

```json
{
  "code": "SELL_LISTING_NOT_FOUND",
  "message": "판매 상품을 찾을 수 없습니다."
}
```

## 내 거래 내역 조회
- http 메서드: get
- domain: market
- endpoint: /api/v1/users/me/trades

### API 설명

현재 사용자가 구매자로 참여한 모든 거래 내역을 조회한다.

거래 내역 화면에 필요한 큐브 정보, 결제 정보와 거래 진행 여부를 배열로 반환한다.

---

### 처리 정책

- 현재 사용자가 구매자인 거래만 조회한다. 로그인 구현 전에는 `trade.buyer_user_id = 1`인 거래를 조회한다.
- 거래 상태와 관계없이 현재 사용자가 구매자로 참여한 모든 거래를 반환한다.
- 거래 내역은 최근 결제한 거래부터 표시할 수 있도록 `trade.paid_time` 내림차순으로 정렬한다.
- `paid_time`이 같은 거래는 `trade.id` 내림차순으로 정렬한다.
- 각 거래에는 상세 조회 화면으로 이동할 때 사용할 거래 id를 포함한다.
- 판매글이 삭제되었거나 판매글과 연결된 마켓 상품이 삭제된 거래는 조회 결과에서 제외한다.
- 상품 이미지는 판매글에 연결된 삭제되지 않은 `listing_media` 중 id가 가장 작은 데이터의 `image_url`을 사용하며, 이미지가 없으면 `null`을 반환한다.
- 큐브 이름과 시리얼 번호는 판매글의 마켓 상품과 연결된 큐브 정보를 사용한다.
- 가격은 배송비 등이 포함된 `trade.total_price`가 아니라 판매글에 등록된 `sell_listing.price`를 반환한다.
- 모든 거래에는 `paid_time`이 반드시 존재한다고 가정한다.
- 결제 날짜는 `trade.paid_time`의 날짜를 한국시간 기준 `YYYY-MM-DD` 형식으로 반환한다.
- `trade.status = COMPLETED`이면 응답의 `status`를 `COMPLETED`로 반환한다.
- `trade.status`가 `PAID`, `SENT`, `SHIPPING`, `DELIVERED` 중 하나이면 응답의 `status`를 `IN_PROGRESS`로 반환한다.
- 조회 결과가 없으면 오류를 반환하지 않고 `trades`를 빈 배열로 반환한다.
- 페이지네이션 없이 조건에 맞는 거래 전체를 반환한다.

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
| `trades` | array | 현재 사용자가 구매자로 참여한 거래 내역 목록 |
| `trades[].id` | number | 거래 id |
| `trades[].productImageUrl` | string | null | 판매글의 첫 번째 판매 이미지 URL |
| `trades[].productName` | string | 큐브 제품명 |
| `trades[].serialNumber` | string | 큐브 시리얼 번호 |
| `trades[].price` | number | 판매글에 등록된 상품 가격 |
| `trades[].paidDate` | string(date) | 결제 날짜, YYYY-MM-DD 형식 |
| `trades[].status` | string | 화면 표시용 거래 진행 상태: IN_PROGRESS | COMPLETED |

```json
{
  "trades": [
    {
      "id": 1,
      "productImageUrl": "https://haniumstorage.blob.core.windows.net/hanium/cube_images/cube%20card.png",
      "productName": "BIGBANG MADE CUBE",
      "serialNumber": "NO.0031",
      "price": 35000,
      "paidDate": "2025-04-08",
      "status": "IN_PROGRESS"
    }
  ]
}
```

조회 결과가 없는 경우

```json
{
  "trades": []
}
```

---

### 오류 응답 데이터

없음