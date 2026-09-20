# 마켓 도메인 테스트 가이드

테스트 파일: `app/market/tests/test_market.py`
실행: `.venv\Scripts\python.exe -m pytest app/market/tests/test_market.py -q`
최종 실행 결과: 107 passed (2026-09-15)

DB는 `Mock(spec=Session)` 으로 대체하고 `app.dependency_overrides[get_db]` 로 주입합니다.
실제 MySQL에는 접속하지 않습니다.

마켓 조회는 `db.scalar` 2회, `db.scalars` 1회, `db.execute` 1회를 순서대로 호출하므로
`set_market_results()` 헬퍼로 호출 순서에 맞춰 결과를 지정합니다.

```text
scalar  1) 큐브 소유권      2) 총 거래 수
scalars 1) 제품군 구성 큐브
execute 1) 제품명별 체결 거래(제품군이 없으면 생략)
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
| 정상 변형 | test_read_market_returns_empty_products_when_no_product_group | 조회 가능한 제품군 0개 | `products=[]`, 시세 쿼리 미실행(execute 0회) | PASS |
| 정상 변형 | test_read_market_returns_null_profile_fields_when_not_set | 프로필 이미지·닉네임 없음 | 두 필드 모두 `null` | PASS |
| 경계값 | test_read_market_returns_zero_trade_count_when_count_is_none | count 결과 `None` | `totalTradeCount=0` | PASS |
| 오류 | test_read_market_returns_404_when_ownership_not_found | 소유권 조회 결과 없음 | 404 CUBE_OWNERSHIP_NOT_FOUND, 이후 쿼리 미실행 | PASS |
| 오류 | test_read_market_returns_404_when_affinity_not_found | 소유권은 있으나 친밀도 없음 | 404 CUBE_AFFINITY_NOT_FOUND, 이후 쿼리 미실행 | PASS |
| 소유권 | test_read_market_queries_only_own_active_last_accessed_ownership | 소유권 SQL 검증 | WHERE에 `user_id=1`, `ownership_status='ACTIVE'`, `is_last_accessed IS true` | PASS |
| 정책 | test_read_market_counts_only_completed_trades_of_buyer_or_seller | 거래 수 SQL 검증 | `count(trade.id)`, `status='COMPLETED'`, `buyer_user_id=1 OR sell_listing.user_id=1` | PASS |
| 정책 | test_read_market_excludes_deleted_and_disabled_cubes_from_products | 제품 SQL 검증 | `cube.deleted_at IS NULL`, `cube.status != 'DISABLED'`, `ORDER BY cube.id ASC` | PASS |
| 정책 | test_read_market_orders_trade_price_query_by_paid_time_and_trade_id | 시세 SQL 검증 | 판매글→큐브 조인, `sell_listing.price` 사용, 체결 5개 상태 IN, `ORDER BY trade.paid_time DESC, trade.id DESC`, 판매글 삭제 필터 없음 | PASS |
| 문서 | test_read_market_swagger_contract | OpenAPI 스키마 | 응답 코드 `{200, 404}` | PASS |

### 목데이터 대조 검증 (일회성)

`scripts/sql/02-data-mock.sql` 의 마켓 데이터(큐브 10개, 마켓 상품 10개, 판매글 4개, 거래 1개)를
SQLite에 적재하고 `get_market()` 을 그대로 실행해 결과를 확인했습니다.
(`market_product` 테이블 제거 전 실행 결과입니다. 목데이터의 마켓 상품 id가 큐브 id와 같았으므로
`mp` 값은 제거 후의 `marketProductId = cube.id` 와 같습니다. 제거 후에는 다시 실행하지 않았습니다.)

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
- 거래 1건(판매글 1 → 큐브 2, `DELIVERED`)이 체결 거래로 인정되어
  `BIGBANG MADE CUBE` 만 판매글 가격 35000이 붙습니다. 거래 총액 36250이 아닙니다.
- 그 거래는 `COMPLETED`가 아니므로 `totalTradeCount`는 0입니다.
- 판매글 3·4번은 아직 거래가 없어 시세에 영향을 주지 않습니다.

### 검증하지 않은 항목

- **"다른 사용자의 소유권" 과 "존재하지 않는 소유권"** 은 Mock DB에서 결과가 같아 개별 테스트로
  나누지 않고 SQL 검증으로 대신했습니다. `ownership_status != ACTIVE`,
  `is_last_accessed = false` 도 같은 이유입니다.
- **삭제·비활성 큐브 제외, 최근 거래 정렬**은 Mock DB가 WHERE·ORDER BY를
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
| 정책 | test_read_market_sell_listings_requires_active_representative_cube | 대표 큐브 SQL 검증 | `cube.id`, `cube.deleted_at IS NULL`, `cube.status != 'DISABLED'` | PASS |
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

- **삭제·비활성 큐브 제외, `ACTIVE` 판매글만 조회, id 내림차순 정렬**은
  Mock DB가 WHERE·ORDER BY를 실제로 실행하지 않으므로 생성된 SQL로 검증했습니다.
- **판매자 본인 판매글도 포함**하는 규칙은 서비스가 `current_user_id` 를 받되 조회 조건으로
  쓰지 않으므로(명세상 별도 필터 없음) 별도 테스트를 만들지 않았습니다.
  `current_user_id` 는 `/users/me` 경로의 인증 의존성으로만 주입됩니다.
- **좋아요 취소가 `is_liked=false` 로 저장되는 규칙**은 좋아요 변경 API의 책임이라 이 조회
  테스트에서는 다루지 않고, 집계에서 제외되는지만 확인했습니다.

---

## 마켓 검색 결과 조회 — `GET /api/v1/users/me/market/search`

`db.execute` 1회로 판매글을 조회하므로 `set_search_results()` 헬퍼로 결과 행만 지정합니다.
`keyword` 는 라우터에서 `min_length=1` 로 검증하고, 앞뒤 공백을 제거한 뒤 빈 문자열이면
서비스에서 공통 400을 냅니다.

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_search_market_returns_sell_listings_matching_keyword | `keyword=ROSE`, 판매글 2건 | 200 + 응답 JSON 전체 일치, id 내림차순 | PASS |
| 정상 변형 | test_search_market_returns_listing_matching_artist_name_only | 제품명은 불일치, 아티스트명만 일치 | 200 + 해당 판매글 반환 | PASS |
| 정상 변형 | test_search_market_returns_listing_once_when_both_names_match | 제품명·아티스트명 모두 일치 | 판매글 1건만 반환 | PASS |
| 정상 변형 | test_search_market_returns_empty_list_when_no_listing_matches | 일치하는 판매글 0건 | 200 + `sellListings=[]` | PASS |
| 정상 변형 | test_search_market_returns_null_seller_nickname_and_zero_like_count | 닉네임 미설정·좋아요 0건 | `sellerNickname=null`, `likeCount=0` | PASS |
| 소유권 | test_search_market_includes_own_sell_listing | 판매자가 현재 사용자인 판매글 | 결과에 포함, SQL에 `sell_listing.user_id = 1` 없음 | PASS |
| 경계값 | test_search_market_allows_single_character_keyword | `keyword=R` (1글자) | 200 + `LIKE '%R%'` | PASS |
| 요청 검증 | test_search_market_returns_400_when_keyword_is_missing | `keyword` 파라미터 누락 | 400 INVALID_REQUEST, 쿼리 미실행 | PASS |
| 요청 검증 | test_search_market_returns_400_when_keyword_is_empty | `keyword=` (빈 문자열) | 400 INVALID_REQUEST, 쿼리 미실행 | PASS |
| 요청 검증 | test_search_market_returns_400_when_keyword_is_only_whitespace | `keyword=(공백 3칸)` | 400 INVALID_REQUEST, 쿼리 미실행 | PASS |
| 정책 | test_search_market_strips_keyword_before_matching | `keyword=(공백)ROSE(공백)` | `LIKE '%ROSE%'` 로 앞뒤 공백 제거 후 검색 | PASS |
| 정책 | test_search_market_matches_product_name_or_artist_name | 검색 조건 SQL 검증 | `product_name LIKE ... OR artist_name LIKE ...` | PASS |
| 정책 | test_search_market_escapes_like_wildcards_in_keyword | `keyword=50%_` | `LIKE '%50\%\_%' ESCAPE '\'` 로 와일드카드를 일반 문자로 검색 | PASS |
| 정책 | test_search_market_escapes_escape_character_in_keyword | `keyword=A\B` | `LIKE '%A\\B%' ESCAPE '\'` 로 이스케이프 문자 자체도 이스케이프 | PASS |
| 정책 | test_search_market_returns_only_active_listings_ordered_by_id_desc | 판매글 SQL 검증 | `status='ACTIVE'`, `deleted_at IS NULL`, 큐브 조건·판매글→큐브 조인, `ORDER BY sell_listing.id DESC` | PASS |
| 정책 | test_search_market_counts_only_liked_rows | 좋아요 서브쿼리 검증 | `count(selling_list_like.id)`, `is_liked IS true`, 판매글 id 상관 조건 | PASS |
| 문서 | test_search_market_swagger_contract | OpenAPI 스키마 | 응답 코드 `{200, 400}` | PASS |

### 목데이터 대조 (수기 확인)

`scripts/sql/02-data-mock.sql` 에 `keyword=ROSE` 조건을 손으로 적용한 예상 결과이며,
MySQL에 실제로 질의해 얻은 값은 아닙니다.

- 큐브 3(`ROSE ROISE CUBE`/`ROSE`), 6(`ROSE ROSIE CUBE`/`ROSE`), 9(`ROSE ROISE CUBE`/`ROSE`)가 검색됩니다.
- 큐브 6에는 판매글이 없어 결과에서 빠지고, 큐브 3의 판매글 2번과 큐브 9의 판매글 3번이 남습니다.
- 판매글 3번의 좋아요는 `(3,1,TRUE)`, `(4,2,FALSE)` 두 건이지만 `is_liked=true`인 1건만 집계됩니다.
- id 내림차순이므로 3번이 먼저 나오며, API_SPEC의 예시 응답과 같은 형태입니다.

```json
{"sellListings": [
  {"sellListingId": 3, "productName": "ROSE ROISE CUBE", "serialNumber": "NO.0099",
   "sellerNickname": "로제짱", "price": 42000, "likeCount": 1},
  {"sellListingId": 2, "productName": "ROSE ROISE CUBE", "serialNumber": "NO.0022",
   "sellerNickname": "로제짱", "price": 35000, "likeCount": 1}
]}
```

### 검증하지 않은 항목

- **삭제·비활성 큐브 제외, `ACTIVE` 판매글만 조회, id 내림차순 정렬**은
  Mock DB가 WHERE·ORDER BY를 실제로 실행하지 않으므로 생성된 SQL로 검증했습니다.
- **영문 대소문자를 구분하지 않는 부분 일치**는 DB 콜레이션(`utf8mb4_unicode_ci`)이 결정하므로
  Mock DB로는 확인할 수 없어 `LIKE '%keyword%'` 조건이 생성되는지까지만 검증했습니다.
- **오류 응답**은 이 API가 정의하는 도메인 오류가 없어 공통 400 외에는 해당 없음입니다.
- **예외(rollback)**는 조회 전용이라 `db.commit` 을 호출하지 않으므로 해당 없음이며,
  정상 케이스에서 `db.commit.assert_not_called()` 로 확인했습니다.

---

## 거래 진행 정보 생성 — `POST /api/v1/users/me/trades`

`db.scalar` 를 판매글 잠금 조회 → 기존 거래 확인 → 큐브 잠금 조회 순서로 3회 호출하므로
`db.scalar.side_effect` 에 세 결과를 순서대로 지정합니다.

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_create_trade_saves_trade_and_marks_sell_listing_sold | ACTIVE 판매글, 연결된 큐브 존재 | 204, 거래 `PAID` 저장, 판매글 `SOLD`, 큐브 `TRADE_PENDING`, commit 1회 | PASS |
| 정상 | test_create_trade_locks_and_marks_cube_of_the_sold_listing | 큐브 조회 SQL 검증 | 판매글의 `cube_id` 로 조회한 큐브를 `FOR UPDATE` 로 잠그고 `TRADE_PENDING` 으로 변경 | PASS |
| 오류 | test_create_trade_returns_404_when_cube_not_found | 판매글에 연결된 큐브 조회 결과 없음 | 404 SELL_LISTING_INVALID, 판매글 상태 유지, 저장 없음 | PASS |
| 오류 | test_create_trade_returns_404_for_missing_sell_listing | 판매글 조회 결과 없음 | 404 SELL_LISTING_INVALID, 저장 없음 | PASS |
| 오류 | test_create_trade_returns_404_for_inactive_sell_listing_without_existing_trade | 판매글 `status=DELETED` | 404 SELL_LISTING_INVALID, 저장 없음 | PASS |
| 상태 전이 | test_create_trade_returns_409_when_trade_already_exists | 같은 판매글의 거래 존재 | 409 TRADE_ALREADY_EXISTS, rollback 1회 | PASS |
| 소유권 | test_create_trade_returns_409_for_self_trade | 판매자가 현재 사용자 | 409 SELF_TRADE_NOT_ALLOWED, rollback 1회 | PASS |
| 문서 | test_create_trade_swagger_responses | OpenAPI 스키마 | 응답 코드 `{204, 404, 409}` | PASS |

### 검증하지 않은 항목

- **하나의 트랜잭션 처리**는 서비스가 거래 저장·판매글 상태·큐브 상태를 모두 세션에 반영한 뒤
  `db.commit()` 을 한 번만 호출하는 것으로 확인했습니다. 실제 트랜잭션 격리 동작은 Mock DB로
  검증할 수 없습니다.
- **행 잠금(`with_for_update`)** 의 실제 동시성 동작도 확인 대상이 아니며, 생성된 SQL에
  `FOR UPDATE` 가 포함되는지만 검증했습니다.
- **`buyer_user_id = 1` 고정**은 로그인 구현 전 임시 정책이라 `get_current_user_id` 의존성이
  반환하는 값을 그대로 저장하는지만 확인했습니다.
- **요청 검증·경계값·예외(commit 실패)** 케이스는 이번 작업 범위가 아니어서 추가하지 않았습니다.

---

## 판매글 상세 조회 — `GET /api/v1/users/me/sell-listings/{sellListingId}`

`db.execute` 로 (판매글, 판매자, 큐브) 행을 조회한 뒤 `db.scalars` 로 이미지 URL을 조회하므로
`set_sell_listing_detail_results()` 헬퍼로 두 결과를 지정합니다.

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_read_sell_listing_detail_returns_listing_seller_and_cube | ACTIVE 판매글 + 이미지 2건 | 200 + 응답 JSON 전체 일치 | PASS |
| 정상 변형 | test_read_sell_listing_detail_returns_is_mine_true_for_own_listing | 작성자가 현재 사용자 | `isMine=true` | PASS |
| 정상 변형 | test_read_sell_listing_detail_returns_sold_listing | 판매글 `status=SOLD` | 200 + `status="SOLD"` | PASS |
| 정상 변형 | test_read_sell_listing_detail_returns_empty_image_urls | 등록된 이미지 0건 | `imageUrls=[]` | PASS |
| 정상 변형 | test_read_sell_listing_detail_returns_null_seller_profile_image_url | 판매자 프로필 이미지 없음 | `sellerProfileImageUrl=null` | PASS |
| 오류 | test_read_sell_listing_detail_returns_404_when_listing_is_unavailable | 판매글 조회 결과 없음 | 404 SELL_LISTING_NOT_FOUND, 이미지 쿼리 미실행 | PASS |
| 경계값 | test_read_sell_listing_detail_allows_minimum_sell_listing_id | `sellListingId=1` | 200 | PASS |
| 경계값 | test_read_sell_listing_detail_returns_400_when_id_is_zero | `sellListingId=0` | 400 INVALID_REQUEST, 쿼리 미실행 | PASS |
| 요청 검증 | test_read_sell_listing_detail_returns_400_when_id_is_not_a_number | `sellListingId=abc` | 400 INVALID_REQUEST, 쿼리 미실행 | PASS |
| 정책 | test_read_sell_listing_detail_excludes_deleted_listing | 판매글 SQL 검증 | `status != 'DELETED'`, `deleted_at IS NULL`, 판매자·큐브 조인 | PASS |
| 정책 | test_read_sell_listing_detail_orders_images_by_id_asc | 이미지 SQL 검증 | `listing_media.deleted_at IS NULL`, `ORDER BY listing_media.id ASC` | PASS |
| 문서 | test_read_sell_listing_detail_swagger_contract | OpenAPI 스키마 | 응답 코드 `{200, 404}` | PASS |

### 검증하지 않은 항목

- **소유권**은 이 API에서 접근 제한 조건이 아니므로(본인·타인 판매글 모두 조회 가능) 별도
  404 케이스 없이 `isMine` 값 분기만 확인했습니다.
- **상태 전이**는 조회 전용이라 해당 없음입니다.
- **예외(rollback)**는 `db.commit` 을 호출하지 않으므로 해당 없음이며, 정상 케이스에서
  `db.commit.assert_not_called()` 로 확인했습니다.
- **거래 진행 버튼 활성화 조건(`ACTIVE` + `isMine=false`)** 은 프론트 표시 규칙이라 서버는
  두 값을 그대로 내려주는지만 확인했습니다.

---

## 내 거래 내역 조회 — `GET /api/v1/users/me/trades`

`db.execute` 1회로 (거래, 판매가, 큐브) 행을 조회하므로
`set_trade_history_results()` 헬퍼로 결과 행만 지정합니다.

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_read_trade_history_returns_buyer_trades | 구매 거래 2건 | 200 + 응답 JSON 전체 일치 | PASS |
| 정상 변형 | test_read_trade_history_returns_completed_status | `trade.status=COMPLETED` | `status="COMPLETED"` | PASS |
| 정상 변형 | test_read_trade_history_maps_ongoing_statuses_to_in_progress | `PAID`/`SENT`/`SHIPPING`/`DELIVERED` | 모두 `status="IN_PROGRESS"` | PASS |
| 정상 변형 | test_read_trade_history_returns_null_product_image_url | 큐브 제품 이미지 없음 | `productImageUrl=null` | PASS |
| 정상 변형 | test_read_trade_history_returns_date_without_time | `paid_time=2025-04-08T23:59:59` | `paidDate="2025-04-08"` | PASS |
| 정상 변형 | test_read_trade_history_returns_empty_list_when_no_trade | 거래 0건 | 200 + `trades=[]` | PASS |
| 소유권 | test_read_trade_history_queries_only_current_user_trades | 조회 SQL 검증 | `trade.buyer_user_id = 1`, 판매자 조건 없음 | PASS |
| 정책 | test_read_trade_history_excludes_deleted_sell_listing_and_cube | 조회 SQL 검증 | 판매글·큐브 `deleted_at IS NULL`, 판매글→큐브 조인, 가격은 `sell_listing.price` | PASS |
| 정책 | test_read_trade_history_orders_by_paid_time_and_trade_id_desc | 정렬 SQL 검증 | `ORDER BY trade.paid_time DESC, trade.id DESC` | PASS |
| 정책 | test_read_trade_history_uses_cube_product_image | 이미지 컬럼 검증 | `cube.product_image_url` 사용, `listing_media` 미조회 | PASS |
| 문서 | test_read_trade_history_swagger_contract | OpenAPI 스키마 | 응답 코드 `{200}` | PASS |

### 검증하지 않은 항목

- **오류 응답**은 이 API가 정의하는 도메인 오류가 없어 해당 없음입니다. 요청 Query·Path가
  없으므로 요청 검증·경계값 케이스도 해당 없음입니다.
- **상태 전이·예외(rollback)**는 조회 전용이라 해당 없음이며, 정상 케이스에서
  `db.commit.assert_not_called()` 로 확인했습니다.
- **정렬 결과**는 Mock DB가 ORDER BY를 실제로 실행하지 않으므로 생성된 SQL로 검증했습니다.
- **`paid_time` 이 항상 존재한다는 전제**는 명세를 그대로 따랐고, `NULL` 인 거래에 대한
  방어 코드는 두지 않았습니다.

---

## 판매 가능 큐브 조회 — `GET /api/v1/users/me/sellable-cubes`

`db.scalars` 한 번으로 큐브 목록을 조회하므로 `db.scalars.return_value` 에
결과를 지정합니다.

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_read_sellable_cubes_returns_active_unlisted_cubes | 판매 가능 큐브 2건(이미지 있음/없음) | 200 + 응답 JSON 전체 일치, 조회 SQL에 소유권·삭제·중복 판매글(NOT EXISTS, `sell_listing.cube_id = cube.id`) 조건과 `ORDER BY cube.id ASC` 포함 | PASS |
| 정상 변형 | test_read_sellable_cubes_returns_empty_list | 조회 결과 0건 | 200 + `cubes=[]` | PASS |
| 문서 | test_read_sellable_cubes_swagger_responses | OpenAPI 스키마 | 응답 코드 `{200}`, tag `market` | PASS |

### 검증하지 않은 항목

- **오류·경계값**은 이 API가 정의하는 도메인 오류와 요청 파라미터가 없어 해당 없음입니다.
- **소유권 조건**은 Mock DB로 결과를 구분할 수 없어 생성된 SQL의 WHERE 절로 검증했습니다.

---

## 판매글 등록 — `POST /api/v1/users/me/sell-listings`

`db.scalar` 를 큐브 조회(`marketProductId` = `cube.id`) → 기존 `ACTIVE` 판매글 확인 순서로 2회 호출하므로
`db.scalar.side_effect` 에 두 결과를 지정하고, `db.flush.side_effect` 로 생성된 id를 채웁니다.

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_create_sell_listing_saves_listing_from_json_body | 소유 중인 큐브, 판매 중 판매글 없음 | 201 + `{"sellListingId": 7}`, 판매글 `ACTIVE`·`cube_id=1` 저장, flush·commit 각 1회, 큐브 조회 SQL(`cube.id = 1`, `FOR UPDATE`) 조건 검증 | PASS |
| 정상 변형 | test_create_sell_listing_saves_null_when_product_status_is_omitted | `productStatus` 생략 | 201, `product_status=None` 저장 | PASS |
| 요청 검증 | test_create_sell_listing_returns_400_when_required_json_field_is_missing | `title` 누락 | 400 INVALID_REQUEST, 쿼리 미실행 | PASS |
| 오류 | test_create_sell_listing_returns_404_for_unavailable_market_product | 큐브 조회 결과 없음 | 404 MARKET_PRODUCT_NOT_FOUND, 저장 없음 | PASS |
| 상태 전이 | test_create_sell_listing_returns_409_for_existing_active_listing | 같은 큐브의 `ACTIVE` 판매글 존재 | 409 SELL_LISTING_ALREADY_ACTIVE, rollback 1회 | PASS |
| 문서 | test_create_sell_listing_swagger_contract | OpenAPI 스키마 | 응답 코드 `{201, 404, 409}`, 요청 Body 5개 필드, `productStatus` 는 선택 | PASS |

### 검증하지 않은 항목

- **소유권**은 큐브 조회 SQL에 `cube_ownership.user_id` 조건이 포함되는지로 확인했습니다.
- **예외(commit 실패)** 케이스는 추가하지 않았습니다.

---

## 판매글 삭제 — `DELETE /api/v1/users/me/sell-listings/{sellListingId}`

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_delete_sell_listing_soft_deletes_current_user_listing | 현재 사용자의 삭제되지 않은 판매글 | 204, `status=DELETED` + `deleted_at` KST naive(마이크로초 0) 저장, commit 1회 | PASS |
| 소유권 | test_delete_sell_listing_returns_404_when_listing_is_unavailable | 없는 판매글 또는 남의 판매글 | 404 SELL_LISTING_NOT_FOUND, commit 없음 | PASS |
| 문서 | test_delete_sell_listing_swagger_contract | OpenAPI 스키마 | 응답 코드 `{204, 404}` | PASS |

### 검증하지 않은 항목

- **"없는 판매글" 과 "남의 판매글"** 은 Mock DB로 구분할 수 없어 조회 SQL의 `user_id` 조건으로
  함께 검증했습니다.
- **이미 삭제된 판매글 재요청**도 같은 404 경로라 별도 케이스를 만들지 않았습니다.

---

## 거래 상세 조회 — `GET /api/v1/users/me/trades/{tradeId}`

`db.execute` 로 (거래, 판매글, 큐브) 행을 조회하므로
`db.execute.return_value.first` 에 `trade_detail_row()` 를 지정합니다.

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_read_trade_detail_returns_trade_product_and_timeline | `SHIPPING` 거래 | 200 + 응답 JSON 전체 일치, 타임라인 5단계의 `completed` 플래그 | PASS |
| 소유권 | test_read_trade_detail_returns_404_for_unknown_or_other_user_trade | 없는 거래 또는 남의 거래 | 404 TRADE_NOT_FOUND | PASS |
| 문서 | test_read_trade_detail_swagger_responses | OpenAPI 스키마 | 응답 코드 `{200, 404}` | PASS |

### 검증하지 않은 항목

- **타임라인 라벨**은 서비스 상단 `TRADE_TIMELINE_LABELS` 상수를 그대로 쓰므로 정상 케이스의
  응답 JSON 비교로만 확인했습니다.

---

## 구매 확정 — `PATCH /api/v1/users/me/trades/{tradeId}/complete`

`db.execute` 로 (거래, 구매자) → (판매자 id, 시리얼) 을 조회하고, `db.scalar` 로
확정된 이전 작업 → 대기 중 이전 작업 → 큐브를 순서대로 조회하므로
`set_complete_trade_results()` 헬퍼로 다섯 결과를 한 번에 지정합니다.
NFT 이전은 `app.market.service.transfer_cube_nft` 를 patch 해서 대체합니다.

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_complete_trade_updates_trade_and_creates_certificate | `DELIVERED` 거래 | 200 + 응답 JSON 전체 일치, 거래 `COMPLETED` + `completed_time` 저장, 인증서 생성, commit 1회 | PASS |
| 정상 | test_complete_trade_releases_cube_to_owned | 큐브가 `TRADE_PENDING` | 200, 큐브 `OWNED` 로 복귀, 조회 SQL이 거래의 판매글로 조인하며 `FOR UPDATE` 포함 | PASS |
| 정상 변형 | test_complete_trade_keeps_cube_status_when_cube_is_disabled | 큐브가 `DISABLED` | 200, 큐브 상태 유지 | PASS |
| 정상 | test_complete_trade_requests_transfer_with_seller_and_serial_number | 판매자 7, 시리얼 NO.0055 | 이전 요청에 거래 id·판매자·구매자·시리얼 전달 | PASS |
| 정책 | test_complete_trade_releases_trade_lock_before_transfer | 호출 순서 검증 | 외부 호출 전에 `rollback()` 으로 거래 행 잠금 해제 | PASS |
| 정상 변형 | test_complete_trade_reuses_confirmed_transfer_operation | 이미 `CONFIRMED` 인 이전 작업 존재 | 200, 이전 재요청 없이 기존 결과로 인증서 생성 | PASS |
| 상태 전이 | test_complete_trade_returns_409_when_transfer_is_in_progress | `REQUESTED` 이전 작업 존재 | 409 TRADE_CONFIRMATION_TIMEOUT, 이전 중복 접수 없음 | PASS |
| 정책 | test_complete_trade_queries_transfer_operation_by_status | 조회 SQL 검증 | 거래 id·`TRANSFER`·`CONFIRMED`/`REQUESTED` 조건 | PASS |
| 오류 | test_complete_trade_returns_409_when_transfer_is_rejected | 블록체인 서버가 이전 거절 | 409 TRADE_TRANSFER_REJECTED, 저장 없음 | PASS |
| 오류 | test_complete_trade_returns_409_when_confirmation_times_out | 확정 대기 초과 | 409 TRADE_CONFIRMATION_TIMEOUT | PASS |
| 예외 | test_complete_trade_returns_500_when_blockchain_is_unreachable | 블록체인 서버 연결 실패 | 500 INTERNAL_SERVER_ERROR | PASS |
| 소유권 | test_complete_trade_returns_404_for_unknown_or_other_user_trade | 없는 거래 또는 남의 거래 | 404 TRADE_NOT_FOUND, 저장 없음 | PASS |
| 상태 전이 | test_complete_trade_returns_409_when_trade_is_not_delivered | 거래가 이미 `COMPLETED` | 409 TRADE_NOT_DELIVERED, 저장 없음 | PASS |
| 문서 | test_complete_trade_swagger_responses | OpenAPI 스키마 | 라우터 선언과 응답 코드 집합 일치 | PASS |

### 검증하지 않은 항목

- **큐브 상태 복귀와 거래 확정의 단일 트랜잭션 처리**는 두 변경이 모두 세션에 반영된 뒤
  `db.commit()` 이 한 번만 호출되는 것으로 확인했습니다. 실제 격리 동작은 Mock DB로 검증할
  수 없습니다.
- **큐브 소유권(`cube_ownership`) 이전**은 구현되어 있지 않아 검증 대상이 아닙니다.
- **블록체인 서버 실환경 연동**은 `app/blockchain/docs/TEST_GUIDE.MD` 에서 다룹니다.
