# 마이페이지 도메인 테스트 가이드

테스트 파일: `app/mypage/tests/test_mypage.py`
실행: `.venv\Scripts\python.exe -m pytest app/mypage/tests/test_mypage.py -q`
최종 실행 결과: 56 passed (2026-09-22)

DB는 `Mock(spec=Session)` 으로 대체하고 `app.dependency_overrides[get_db]` 로 주입합니다.
실제 MySQL에는 접속하지 않습니다.

마이페이지 조회는 `db.scalar` 를 사용자 → 작성 게시글 수 → 댓글 단 게시글 수 순서로 3번
호출하므로 `set_my_page_results()` 헬퍼로 호출 순서에 맞춰 결과를 지정합니다.

---

## 마이페이지 조회 — `GET /api/v1/users/me`

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_read_my_page_returns_profile_and_activity_counts | 프로필 + 게시글 4건·댓글 게시글 2건 | 200 + 응답 JSON 전체 일치, `db.add`·`db.commit` 호출 없음 | PASS |
| 정상 변형 | test_read_my_page_returns_null_nickname_and_profile_image | 닉네임·프로필 이미지 `NULL` | 둘 다 `null` 반환(빈 문자열·기본 URL 치환 없음) | PASS |
| 정상 변형 | test_read_my_page_returns_zero_counts_when_no_activity | 활동 0건 | `writtenPostCount=0`, `commentedPostCount=0` | PASS |
| 정상 변형 | test_read_my_page_returns_zero_counts_when_count_is_none | 집계 결과가 `None` | 0으로 변환해 반환 | PASS |
| 소유권 | test_read_my_page_queries_only_current_user_profile | 사용자 조회 SQL 검증 | `"user".id = 1` | PASS |
| 정책 | test_read_my_page_counts_only_visible_posts_of_current_user | 작성 게시글 SQL 검증 | `count(post.id)`, `post.user_id = 1`, `status IN ('ACTIVE','REPORTED')`, `deleted_at IS NULL` | PASS |
| 정책 | test_read_my_page_counts_distinct_posts_of_current_user_comments | 댓글 게시글 SQL 검증 | `count(DISTINCT comment.post_id)`, `comment JOIN post`, 댓글·게시글 상태와 삭제 조건 | PASS |
| 예외 | test_read_my_page_returns_500_when_user_row_is_missing | 사용자 조회 결과 없음 | 공통 500 INTERNAL_SERVER_ERROR | PASS |
| 문서 | test_read_my_page_swagger_contract | OpenAPI 스키마 | 응답 코드 `{200}`, tag `mypage`, `HTTPBearer` 인증 선언 | PASS |

### 검증하지 않은 항목

- **오류 응답**은 이 API가 정의하는 도메인 오류가 없어 해당 없음입니다. 요청 Query·Path·Body가
  없으므로 요청 검증·경계값 케이스도 해당 없음입니다.
- **인증 실패(401)** 는 공통 인증 의존성이 처리하므로 `app/auth/tests/test_auth.py` 에서 검증하고,
  여기서는 Swagger에 `security` 가 선언되는지만 확인합니다.
- **같은 게시글에 댓글을 여러 개 단 경우 1건으로 집계**되는 동작은 Mock DB가 집계를 실제로
  수행하지 않으므로 생성된 SQL의 `COUNT(DISTINCT ...)` 로 검증했습니다.
- **상태 전이·예외(rollback)** 는 조회 전용이라 해당 없음입니다.

---

## 사용자 프로필 수정 — `PATCH /api/v1/users/me/profile`

서비스가 `db.scalar` 로 현재 사용자를 1번 조회하므로 `db.scalar.return_value` 에 사용자 객체를
지정하고, 응답 이후 그 객체의 `nickname`·`profile_character_img_url` 값을 확인합니다.

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_update_profile_saves_nickname_and_profile_image_url | `DORI` + `profile_001` | 204 + Body 없음, 닉네임·`.../profile_image/profile_001.png` 저장, `db.add` 없음, commit 1회 | PASS |
| 정상 변형 | test_update_profile_saves_profile_002_image_url | `profile_002` | `.../profile_002.png` 저장 | PASS |
| 정상 변형 | test_update_profile_saves_profile_003_image_url | `profile_003` | `.../profile_003.png` 저장 | PASS |
| 정상 변형 | test_update_profile_strips_nickname_before_saving | `"  도리 DORI!  "` | 앞뒤 공백만 제거한 `도리 DORI!` 저장(문자 종류 제한 없음) | PASS |
| 정상 변형 | test_update_profile_accepts_same_values_as_current_profile | 기존과 같은 값 | 204 + commit 1회 | PASS |
| 정상 변형 | test_update_profile_saves_values_when_profile_was_null | 기존 닉네임·이미지 `NULL` | 새 값 저장 | PASS |
| 소유권 | test_update_profile_queries_only_current_user | 사용자 조회 SQL 검증 | `"user".id = 1`, WHERE에 닉네임 조건 없음(중복 허용), 조회 1회 | PASS |
| 경계값 | test_update_profile_allows_minimum_nickname_length | 닉네임 1자 | 204 | PASS |
| 경계값 | test_update_profile_allows_maximum_nickname_length | 닉네임 20자 | 204 | PASS |
| 경계값 | test_update_profile_allows_nickname_that_fits_after_strip | 공백 포함 24자, 제거 후 20자 | 204 + 20자 저장 | PASS |
| 경계값 | test_update_profile_returns_400_when_nickname_is_too_long | 닉네임 21자 | 400 INVALID_REQUEST + 조회·commit 없음 | PASS |
| 요청 검증 | test_update_profile_returns_400_when_nickname_is_blank | 공백만 있는 닉네임 | 400 INVALID_REQUEST | PASS |
| 요청 검증 | test_update_profile_returns_400_when_nickname_is_empty | 빈 문자열 | 400 INVALID_REQUEST | PASS |
| 요청 검증 | test_update_profile_returns_400_when_nickname_is_missing | `nickname` 누락 | 400 INVALID_REQUEST | PASS |
| 요청 검증 | test_update_profile_returns_400_when_profile_character_code_is_missing | `profileCharacterCode` 누락 | 400 INVALID_REQUEST | PASS |
| 요청 검증 | test_update_profile_returns_400_for_unsupported_profile_character_code | `profile_004` | 400 INVALID_REQUEST | PASS |
| 요청 검증 | test_update_profile_returns_400_when_nickname_is_not_string | `nickname: 1234` | 400 INVALID_REQUEST | PASS |
| 예외 | test_update_profile_returns_500_when_user_row_is_missing | 사용자 조회 결과 없음 | 공통 500 INTERNAL_SERVER_ERROR JSON + commit 없음 | PASS |
| 예외 | test_update_profile_rolls_back_when_commit_fails | commit이 예외 발생 | 500 + rollback 1회 | PASS |
| 문서 | test_update_profile_swagger_contract | OpenAPI 스키마 | 응답 코드 `{204, 400}`, 요청 Body 있음, tag `mypage`, `HTTPBearer` | PASS |

### 검증하지 않은 항목

- **오류(도메인 오류 코드)** 는 명세에 공통 400/500 외 도메인 오류가 없어 해당 없음입니다.
- **상태 전이(409)** 는 같은 값으로 재요청해도 정상 처리하는 API라 해당 없음입니다.
- **인증 실패(401)** 는 공통 인증 의존성이 처리하므로 `app/auth/tests/test_auth.py` 에서 검증하고,
  여기서는 Swagger에 `security` 가 선언되는지만 확인합니다.
- **회원가입과 같은 규칙 사용**은 두 API가 `app/user/profile.py` 를 함께 쓰는 것으로 보장하고,
  회원가입 쪽 동작은 기존 `app/auth/tests/test_auth.py` 가 그대로 통과하는 것으로 확인했습니다.

---

## 내가 쓴 글 조회 — `GET /api/v1/users/me/posts`

서비스가 `db.execute` 1회로 (게시글, 작성자 닉네임, 좋아요 수, 댓글 수, 좋아요 여부) 행을
조회하므로 `set_my_posts_results()` 헬퍼로 결과 행만 지정합니다. 다음 페이지 존재 여부는
`size + 1` 건을 조회해 판단하므로, `hasNext` 검증 테스트는 요청한 `size` 보다 한 건 많은 행을
지정합니다. WHERE·집계·정렬 조건은 Mock DB가 실행하지 않으므로 생성된 SQL로 검증합니다.

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_read_my_posts_returns_posts_with_counts | FREE·CERTIFICATION 게시글 2건 | 200 + 응답 JSON 전체 일치, `db.add`·`db.commit` 호출 없음 | PASS |
| 정상 변형 | test_read_my_posts_returns_empty_list_when_no_post | 작성한 게시글 없음 | 200 + `posts: []`, `hasNext: false` | PASS |
| 정상 변형 | test_read_my_posts_returns_has_next_true_when_more_rows_exist | page=1, size=2, 3건 조회 | 앞 2건만 반환 + `hasNext: true`, 요청한 page·size 반환 | PASS |
| 정상 변형 | test_read_my_posts_returns_null_author_nickname | 닉네임 `NULL` | `authorNickname: null` | PASS |
| 정상 변형 | test_read_my_posts_includes_reported_post | `status=REPORTED` 게시글 | 목록에 포함 | PASS |
| 정상 변형 | test_read_my_posts_returns_full_content_without_truncation | 내용 3,000자 | 축약 없이 전체 반환 | PASS |
| 소유권 | test_read_my_posts_queries_only_visible_posts_of_current_user | 조회 SQL 검증 | `post.user_id = 1`, `status IN ('ACTIVE','REPORTED')`, `deleted_at IS NULL`, 게시판·검색 조건 없음 | PASS |
| 정책 | test_read_my_posts_counts_liked_rows_and_active_comments | 집계 SQL 검증 | `count(post_like.id)` + `is_liked IS true`, `post_like.user_id = 1`, `count(comment.id)` + `status = 'ACTIVE'` + `deleted_at IS NULL` | PASS |
| 정책 | test_read_my_posts_orders_by_created_at_and_id_desc | page=2, size=5 | `ORDER BY created_at DESC, id DESC`, `LIMIT 6`, `OFFSET 10` | PASS |
| 경계값 | test_read_my_posts_allows_minimum_page_and_size | page=0, size=1 | 200 | PASS |
| 경계값 | test_read_my_posts_returns_400_when_page_is_negative | page=-1 | 400 INVALID_REQUEST + 조회 안 함 | PASS |
| 경계값 | test_read_my_posts_returns_400_when_size_is_zero | size=0 | 400 INVALID_REQUEST + 조회 안 함 | PASS |
| 요청 검증 | test_read_my_posts_returns_400_when_page_is_not_number | page=abc | 400 INVALID_REQUEST + 조회 안 함 | PASS |
| 문서 | test_read_my_posts_swagger_contract | OpenAPI 스키마 | 응답 코드 `{200, 400}`, Query `page`·`size`, tag `mypage`, `HTTPBearer` | PASS |

### 검증하지 않은 항목

- **오류(도메인 오류 코드)** 는 명세에 공통 400/500 외 도메인 오류가 없어 해당 없음입니다.
- **다른 사용자의 게시글 제외 / 삭제된 게시글 제외 / REPORTED·DELETED 댓글 미집계**는 Mock DB로
  재현할 수 없어 생성된 SQL 조건으로 검증했습니다.
- **size 최댓값**은 명세에 상한이 없어 검증하지 않았습니다.
- **상태 전이·예외(rollback)** 는 조회 전용이라 해당 없음입니다.
- **인증 실패(401)** 는 공통 인증 의존성이 처리하므로 `app/auth/tests/test_auth.py` 에서 검증하고,
  여기서는 Swagger에 `security` 가 선언되는지만 확인합니다.

---

## 댓글 단 글 조회 — `GET /api/v1/users/me/commented-posts`

내가 쓴 글 조회와 같은 select·페이지 변환 헬퍼를 쓰므로 `set_my_posts_results()`·`my_post_row()`
헬퍼를 그대로 재사용합니다. 두 API의 차이인 WHERE 조건(내 댓글 `EXISTS`)과 집계 범위는 생성된
SQL을 SELECT 목록과 바깥 `FROM post JOIN "user"` 이후로 나눠 검증합니다.

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_read_my_commented_posts_returns_posts_with_counts | 다른 사용자 게시글 2건 | 200 + 응답 JSON 전체 일치(게시글 작성자 닉네임), `db.add`·`db.commit` 호출 없음 | PASS |
| 정상 변형 | test_read_my_commented_posts_returns_empty_list_when_no_comment | 댓글 단 게시글 없음 | 200 + `posts: []`, `hasNext: false` | PASS |
| 정상 변형 | test_read_my_commented_posts_returns_has_next_true_when_more_rows_exist | page=1, size=2, 3건 조회 | 앞 2건만 반환 + `hasNext: true` | PASS |
| 정상 변형 | test_read_my_commented_posts_includes_own_and_reported_posts | 내 게시글 + `REPORTED` 게시글 | 둘 다 포함 | PASS |
| 정상 변형 | test_read_my_commented_posts_returns_null_author_nickname | 작성자 닉네임 `NULL` | `authorNickname: null` | PASS |
| 정책 | test_read_my_commented_posts_filters_by_my_visible_comments_with_exists | 조회 SQL 검증 | 게시글 상태·삭제 조건 + `EXISTS (SELECT comment.id ...)` 안에 `comment.user_id = 1`·`status IN ('ACTIVE','REPORTED')`·`deleted_at IS NULL`, `post.user_id` 조건·`JOIN comment`·게시판·검색 조건 없음 | PASS |
| 정책 | test_read_my_commented_posts_counts_all_active_comments_of_post | 집계 SQL 검증 | 좋아요 집계·내 좋아요 여부, `count(comment.id)` + `status = 'ACTIVE'`, 댓글 수에 `comment.user_id` 조건 없음 | PASS |
| 정책 | test_read_my_commented_posts_orders_by_post_created_at_and_id_desc | page=2, size=5 | `ORDER BY post.created_at DESC, post.id DESC`, 댓글 작성 시각 미사용, `LIMIT 6`, `OFFSET 10` | PASS |
| 경계값 | test_read_my_commented_posts_allows_minimum_page_and_size | page=0, size=1 | 200 | PASS |
| 경계값 | test_read_my_commented_posts_returns_400_when_page_is_negative | page=-1 | 400 INVALID_REQUEST + 조회 안 함 | PASS |
| 경계값 | test_read_my_commented_posts_returns_400_when_size_is_zero | size=0 | 400 INVALID_REQUEST + 조회 안 함 | PASS |
| 요청 검증 | test_read_my_commented_posts_returns_400_when_size_is_not_number | size=abc | 400 INVALID_REQUEST + 조회 안 함 | PASS |
| 문서 | test_read_my_commented_posts_swagger_contract | OpenAPI 스키마 | 응답 코드 `{200, 400}`, Query `page`·`size`, tag `mypage`, `HTTPBearer` | PASS |

### 검증하지 않은 항목

- **같은 게시글에 댓글을 여러 개 단 경우 1건만 반환**되는 동작은 Mock DB가 쿼리를 실행하지 않아
  재현할 수 없으므로, 댓글을 JOIN하지 않고 `EXISTS` 로만 거르는 SQL 구조로 검증했습니다.
- **삭제된 댓글만 남은 게시글 제외 / 삭제된 게시글 제외**도 같은 이유로 SQL 조건으로 검증했습니다.
- **소유권**은 남의 게시글도 조회 대상이라 게시글 작성자 조건이 없는 것을 SQL로 확인했습니다.
- **오류(도메인 오류 코드)**, **상태 전이·예외(rollback)** 는 조회 전용이고 도메인 오류가 없어
  해당 없음입니다.
- **size 최댓값**은 명세에 상한이 없어 검증하지 않았습니다.
