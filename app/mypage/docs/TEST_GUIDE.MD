# 마이페이지 도메인 테스트 가이드

테스트 파일: `app/mypage/tests/test_mypage.py`
실행: `.venv\Scripts\python.exe -m pytest app/mypage/tests/test_mypage.py -q`
최종 실행 결과: 9 passed (2026-08-29)

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
