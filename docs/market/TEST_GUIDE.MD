# 마켓 도메인 테스트 가이드

테스트 파일: `tests/test_market.py`
실행: `.venv\Scripts\python.exe -m pytest tests/test_market.py -q`
최종 실행 결과: 55 passed (2026-08-28)

DB는 `Mock(spec=Session)` 으로 대체하고 `app.dependency_overrides[get_db]` 로 주입합니다.
실제 MySQL에는 접속하지 않습니다.

마켓 조회는 `db.scalar` 2회, `db.execute` 2회를 순서대로 호출하므로 `set_market_results()`
헬퍼로 호출 순서에 맞춰 결과를 지정합니다.

```text
scalar  1) 큐브 소유권      2) 총 거래 수
execute 1) 큐브+마켓상품    2) 제품명별 체결 거래(제품군이 없으면 생략)
```

---

## 마켓 조회 — `GET /api/v1/users/me/market`

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_read_market_returns_profile_and_representative_products | 제품군 2개, 체결 1건, 거래 24건 | 200 + 응답 JSON 전체 일치 | PASS |
| 정상 변형 | test_read_market_groups_same_product_name_into_smallest_cube_id | 같은 제품명 큐브 3번·7번 | 1개 항목, 대표 큐브 3번 | PASS |
| 정상 변형 | test_read_market_treats_different_letter_case_as_different_products | `JENNIE RUBY CUBE` / `jennie ruby cube` | 서로 다른 제품군 2개 (정규화 미적용) | PASS |
| 정상 변형 | test_read_market_orders_products_by_representative_cube_id | 대표 큐브 2, 5, 9 | 대표 큐브 id 오름차순 | PASS |
| 정상 변형 | test_read_market_uses_most_recent_settled_trade_price | 같은 제품명 거래 2건 | 최신순 첫 행(12500) 채택 | PASS |
| 정상 변형 | test_read_market_returns_null_price_when_no_settled_trade | 체결 거래 0건 | `latestTradePrice=null` | PASS |
| 정상 변형 | test_read_market_returns_null_image_when_representative_product_has_none | 대표 상품 이미지 없음 | `productImageUrl=null`, 제품군은 유지 | PASS |
| 정상 변형 | test_read_market_returns_empty_products_when_no_product_group | 조회 가능한 제품군 0개 | `products=[]`, 시세 쿼리 미실행(execute 1회) | PASS |
| 정상 변형 | test_read_market_returns_null_profile_fields_when_not_set | 프로필 이미지·닉네임 없음 | 두 필드 모두 `null` | PASS |
| 경계값 | test_read_market_returns_zero_trade_count_when_count_is_none | count 결과 `None` | `totalTradeCount=0` | PASS |
| 오류 | test_read_market_returns_404_when_ownership_not_found | 소유권 조회 결과 없음 | 404 CUBE_OWNERSHIP_NOT_FOUND, 이후 쿼리 미실행 | PASS |
| 오류 | test_read_market_returns_404_when_affinity_not_found | 소유권은 있으나 친밀도 없음 | 404 CUBE_AFFINITY_NOT_FOUND, 이후 쿼리 미실행 | PASS |
| 소유권 | test_read_market_queries_only_own_active_last_accessed_ownership | 소유권 SQL 검증 | WHERE에 `user_id=1`, `ownership_status='ACTIVE'`, `is_last_accessed IS true` | PASS |
| 정책 | test_read_market_counts_only_completed_trades_of_buyer_or_seller | 거래 수 SQL 검증 | `count(trade.id)`, `status='COMPLETED'`, `buyer_user_id=1 OR sell_listing.user_id=1` | PASS |
| 정책 | test_read_market_excludes_deleted_and_disabled_cubes_from_products | 제품 SQL 검증 | `cube.deleted_at IS NULL`, `cube.status != 'DISABLED'`, `market_product.deleted_at IS NULL`, `ORDER BY cube.id ASC` | PASS |
| 정책 | test_read_market_orders_trade_price_query_by_paid_time_and_trade_id | 시세 SQL 검증 | `sell_listing.price` 사용, 체결 5개 상태 IN, `ORDER BY trade.paid_time DESC, trade.id DESC`, 판매글 삭제 필터 없음 | PASS |
| 문서 | test_read_market_swagger_contract | OpenAPI 스키마 | 응답 코드 `{200, 404}` | PASS |

### 목데이터 대조 검증 (일회성)

`scripts/sql/02-data-mock.sql` 의 마켓 데이터(큐브 10개, 마켓 상품 10개, 판매글 4개, 거래 1개)를
SQLite에 적재하고 `get_market()` 을 그대로 실행해 결과를 확인했습니다.

```text
profile: level 3 Close, avatarNickname '젠득이', totalTradeCount 0
  cube=1  mp=1  'JENNIE RUBY CUBE'        price=None    <- 큐브 7과 같은 제품군
  cube=2  mp=2  'BIGBANG MADE CUBE'       price=35000
  cube=3  mp=3  'ROSE ROISE CUBE'         price=None    <- 큐브 9와 같은 제품군
  cube=4  mp=4  'JENNIE SOLO CUBE'        price=None
  cube=5  mp=5  'BIGBANG STILL LIFE CUBE' price=None
  cube=6  mp=6  'ROSE ROSIE CUBE'         price=None
  cube=8  mp=8  'AESPA ARMAGEDDON CUBE'   price=None
  cube=10 mp=10 'IU THE WINNING CUBE'     price=None
```

- 큐브 10개 중 `JENNIE RUBY CUBE`(1, 7)와 `ROSE ROISE CUBE`(3, 9)가 각각 묶여 제품군은 8개이고,
  각 제품군의 대표는 id가 작은 큐브(1번, 3번)입니다. 대표 큐브 id 오름차순으로 나옵니다.
- 거래 1건(판매글 1 → 마켓 상품 2 → 큐브 2, `DELIVERED`)이 체결 거래로 인정되어
  `BIGBANG MADE CUBE` 만 판매글 가격 35000이 붙습니다. 거래 총액 36250이 아닙니다.
- 그 거래는 `COMPLETED`가 아니므로 `totalTradeCount`는 0입니다.
- 판매글 3·4번은 아직 거래가 없어 시세에 영향을 주지 않습니다.

### 검증하지 않은 항목

- **"다른 사용자의 소유권" 과 "존재하지 않는 소유권"** 은 Mock DB에서 결과가 같아 개별 테스트로
  나누지 않고 SQL 검증으로 대신했습니다. `ownership_status != ACTIVE`,
  `is_last_accessed = false` 도 같은 이유입니다.
- **삭제·비활성 큐브 제외, 삭제된 마켓 상품 제외, 최근 거래 정렬**은 Mock DB가 WHERE·ORDER BY를
  실제로 실행하지 않으므로 생성된 SQL에 조건이 포함되는지로 검증했습니다.
  `..._uses_most_recent_settled_trade_price` 는 정렬된 결과를 받았을 때 첫 행을 채택하는
  Python 쪽 로직만 검증합니다.
- **조회 시 부수효과 없음**은 대표 케이스에서 `db.commit.assert_not_called()` 로만 확인했습니다.

---

## 마켓 세부 상품 조회 — `GET /api/v1/users/me/market/products/{representativeCubeId}/sell-listings`

`db.scalar` 로 대표 큐브의 제품명을 얻은 뒤 `db.execute` 로 판매글을 조회합니다.
테스트는 `set_sell_listing_results()` 헬퍼로 두 결과를 지정합니다.

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_read_market_sell_listings_returns_listings_of_same_product_name | 같은 제품명 큐브 2개의 판매글 | 200 + 응답 JSON 전체 일치, id 내림차순 | PASS |
| 정상 변형 | test_read_market_sell_listings_returns_empty_list_when_nothing_on_sale | 판매 중인 판매글 0건 | `sellListings=[]` | PASS |
| 정상 변형 | test_read_market_sell_listings_returns_zero_like_count | 좋아요 0건 | `likeCount=0` | PASS |
| 정상 변형 | test_read_market_sell_listings_returns_null_seller_nickname | 판매자 닉네임 미설정 | `sellerNickname=null` | PASS |
| 정상 변형 | test_read_market_sell_listings_excludes_product_name_with_different_letter_case | `ROSE ROISE CUBE` / `rose roise cube` | 대소문자가 정확히 같은 판매글만 반환 | PASS |
| 경계값 | test_read_market_sell_listings_allows_minimum_representative_cube_id | `representativeCubeId=1` | 200 | PASS |
| 경계값 | test_read_market_sell_listings_returns_400_when_cube_id_is_zero | `representativeCubeId=0` | 400 INVALID_REQUEST, 쿼리 미실행 | PASS |
| 요청 검증 | test_read_market_sell_listings_returns_400_when_cube_id_is_not_a_number | `representativeCubeId=abc` | 400 INVALID_REQUEST | PASS |
| 오류 | test_read_market_sell_listings_returns_404_when_representative_cube_not_found | 대표 큐브 조회 결과 없음 | 404 MARKET_PRODUCT_NOT_FOUND, 판매글 쿼리 미실행 | PASS |
| 정책 | test_read_market_sell_listings_requires_active_representative_cube_and_product | 대표 큐브 SQL 검증 | `cube.id`, `cube.deleted_at IS NULL`, `cube.status != 'DISABLED'`, `market_product.deleted_at IS NULL` | PASS |
| 정책 | test_read_market_sell_listings_returns_only_active_listings_ordered_by_id_desc | 판매글 SQL 검증 | `status='ACTIVE'`, `deleted_at IS NULL`, 제품명·큐브 조건, `ORDER BY sell_listing.id DESC` | PASS |
| 정책 | test_read_market_sell_listings_counts_only_liked_rows | 좋아요 서브쿼리 검증 | `count(selling_list_like.id)`, `is_liked IS true`, 판매글 id 상관 조건 | PASS |
| 문서 | test_read_market_sell_listings_swagger_contract | OpenAPI 스키마 | 응답 코드 `{200, 404}` | PASS |

### 목데이터 대조 검증 (일회성)

`representativeCubeId=3`(`ROSE ROISE CUBE`)으로 `get_market_product_sell_listings()` 를 실행한 결과가
API_SPEC의 예시 응답과 **완전히 일치**함을 확인했습니다.

```json
{"sellListings": [
  {"sellListingId": 3, "productName": "ROSE ROISE CUBE", "serialNumber": "NO.0099",
   "sellerNickname": "로제짱", "price": 42000, "likeCount": 1},
  {"sellListingId": 2, "productName": "ROSE ROISE CUBE", "serialNumber": "NO.0022",
   "sellerNickname": "로제짱", "price": 35000, "likeCount": 1}
]}
```

- 큐브 3번과 9번이 같은 제품군이라 판매글 2·3번이 함께 나오고, id 내림차순으로 3번이 먼저입니다.
- 판매글 3번의 좋아요는 `(3,1,TRUE)`, `(4,2,FALSE)` 두 건이지만 `is_liked=true`인 1건만 집계됩니다.

### 검증하지 않은 항목

- **삭제·비활성 큐브 제외, 삭제된 마켓 상품 제외, `ACTIVE` 판매글만 조회, id 내림차순 정렬**은
  Mock DB가 WHERE·ORDER BY를 실제로 실행하지 않으므로 생성된 SQL로 검증했습니다.
- **판매자 본인 판매글도 포함**하는 규칙은 서비스가 `current_user_id` 를 받되 조회 조건으로
  쓰지 않으므로(명세상 별도 필터 없음) 별도 테스트를 만들지 않았습니다.
  `current_user_id` 는 `/users/me` 경로의 인증 의존성으로만 주입됩니다.
- **좋아요 취소가 `is_liked=false` 로 저장되는 규칙**은 좋아요 변경 API의 책임이라 이 조회
  테스트에서는 다루지 않고, 집계에서 제외되는지만 확인했습니다.
