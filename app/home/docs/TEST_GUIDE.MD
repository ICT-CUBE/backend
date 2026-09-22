# home 테스트 가이드

테스트 파일: `app/home/tests/test_home.py`
실행: `.venv\Scripts\python.exe -m pytest app/home/tests/test_home.py -q`
최종 실행 결과: 39 passed (2026-09-22)

---

## 홈 정보 조회 — `GET /api/v1/users/me/home`

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_home_returns_orm_values_in_korea_time | ACTIVE 소유권 + 친밀도 존재 | 200 + `{user, cubeOwnership, cube, affinity}` 전체 | PASS |
| 오류 | test_home_returns_404_when_ownership_does_not_exist | 소유권 없음 | 404 CUBE_OWNERSHIP_NOT_FOUND | PASS |
| 오류 | test_home_returns_404_when_affinity_does_not_exist | 친밀도 없음 | 404 CUBE_AFFINITY_NOT_FOUND | PASS |
| 오류 | test_home_returns_403_when_only_inactive_ownership_exists | REVOKED 소유권만 존재 | 403 CUBE_OWNERSHIP_FORBIDDEN | PASS |
| 문서 | test_home_swagger_contains_only_endpoint_specific_errors | OpenAPI 문서 | 응답 코드 `{200, 403, 404}` + HTTPBearer | PASS |

### 검증하지 않은 항목
- 실제 MySQL 연동 동작. Mock 세션으로 대체합니다.

---

## 알림 목록 조회 — `GET /api/v1/users/me/notifications`

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_read_notifications_returns_notifications_with_pagination | type=ALL, 알림 2건 | 200 + `{notifications[2], pagination}` 전체 + add/commit 호출 없음 | PASS |
| 정상 변형 | test_read_notifications_returns_empty_list_when_no_notification | 조회 결과 없음 | 200 + `{notifications: [], hasNext: false}` | PASS |
| 정상 변형 | test_read_notifications_returns_has_next_true_when_more_rows_exist | page=1&size=2, size+1건 조회됨 | 200 + size만큼만 반환 + `hasNext: true` | PASS |
| 정상 변형 | test_read_notifications_queries_all_types_when_type_is_all | type=ALL | 200 + WHERE에 notification_type 조건 없음 | PASS |
| 정상 변형 | test_read_notifications_filters_mission_type | type=MISSION | 200 + `notification_type = 'MISSION'` | PASS |
| 정상 변형 | test_read_notifications_filters_event_type | type=EVENT | 200 + `notification_type = 'EVENT'` | PASS |
| 정상 변형 | test_read_notifications_filters_market_type | type=MARKET | 200 + `notification_type = 'MARKET'` | PASS |
| 소유권 | test_read_notifications_queries_only_current_user_rows | 로그인 사용자 id=1 | `notification.user_id = 1` + 큐브 소유권 조인 없음 | PASS |
| 정상 변형 | test_read_notifications_orders_by_sent_at_and_id_desc | page=2&size=5 | `ORDER BY sent_at DESC, id DESC` + `LIMIT 6` + `OFFSET 10` | PASS |
| 경계값 | test_read_notifications_allows_minimum_page_and_size | page=0&size=1 | 200 | PASS |
| 경계값 | test_read_notifications_returns_400_when_page_is_negative | page=-1 | 400 INVALID_REQUEST + 조회 안 함 | PASS |
| 경계값 | test_read_notifications_returns_400_when_size_is_zero | size=0 | 400 INVALID_REQUEST + 조회 안 함 | PASS |
| 요청 검증 | test_read_notifications_returns_400_when_type_is_missing | type 누락 | 400 INVALID_REQUEST + 조회 안 함 | PASS |
| 요청 검증 | test_read_notifications_returns_400_for_unsupported_type | type=NOTICE | 400 INVALID_REQUEST + 조회 안 함 | PASS |
| 문서 | test_read_notifications_swagger_contract | OpenAPI 문서 | 응답 코드 `{200, 400}` + 파라미터 `{type, page, size}` + HTTPBearer | PASS |

### 검증하지 않은 항목
- 오류: 명세에 이 API의 도메인 오류가 없어 404/409 케이스는 해당 없음.
- 상태 전이: 목록 조회는 상태를 바꾸지 않아 해당 없음.
- 예외: 쓰기 트랜잭션이 없어 commit 실패/rollback 케이스는 해당 없음.
  대신 정상 케이스에서 `db.add` / `db.commit` 이 호출되지 않아
  `is_read`·`read_at` 이 바뀌지 않음을 확인합니다.
- 소유권: "없는 알림" vs "남의 알림" 은 Mock DB로 구분할 수 없어,
  조회 select를 `literal_binds` 로 컴파일해 `notification.user_id = 1` 조건을 검증합니다.

---

## 개별 알림 읽음 처리 — `PATCH /api/v1/users/me/notifications/{notificationId}/read`

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_read_notification_marks_unread_notification_as_read | 미읽음 알림 | 204 + Body 없음 + `is_read=true` + `read_at` 저장(tz 없음) + commit 1회 | PASS |
| 정상 | test_read_notification_stores_read_at_in_korea_time | 미읽음 알림 | `read_at`에 KST 시각을 offset 없이 저장 + `datetime.now(KOREA_TIMEZONE)` 호출 | PASS |
| 상태 전이 | test_read_notification_keeps_read_at_when_already_read | 이미 읽은 알림 | 204 + 기존 `read_at` 유지 + commit 호출 없음 (멱등) | PASS |
| 오류 | test_read_notification_returns_404_when_notification_not_found | 조회 결과 없음 | 404 NOTIFICATION_NOT_FOUND + commit 없음 | PASS |
| 소유권 | test_read_notification_queries_only_current_user_row_with_lock | 로그인 사용자 id=1 | `notification.id = 31` + `user_id = 1` + `FOR UPDATE` + 큐브 소유권 조인 없음 | PASS |
| 경계값 | test_read_notification_allows_minimum_notification_id | notificationId=1 | 204 | PASS |
| 경계값 | test_read_notification_returns_400_when_notification_id_is_zero | notificationId=0 | 400 INVALID_REQUEST + 조회 안 함 | PASS |
| 요청 검증 | test_read_notification_returns_400_when_notification_id_is_not_number | notificationId=abc | 400 INVALID_REQUEST + 조회 안 함 | PASS |
| 예외 | test_read_notification_rolls_back_when_commit_fails | commit 실패 | 500 + rollback 1회 | PASS |
| 문서 | test_read_notification_swagger_contract | OpenAPI 문서 | 응답 코드 `{204, 404}` + 파라미터 `{notificationId}` + HTTPBearer | PASS |

### 검증하지 않은 항목
- 오류: 명세상 404 외의 도메인 오류가 없어 409 케이스는 해당 없음.
- 소유권: "없는 알림" vs "남의 알림" 은 Mock DB로 구분할 수 없어, 두 조건이 하나의
  select WHERE 절에 함께 들어가는지를 `literal_binds` 컴파일로 검증합니다.
  명세상 두 경우의 응답이 동일한 404라 응답만으로는 구분할 필요도 없습니다.
- 실제 행 잠금(`FOR UPDATE`)의 동시성 동작. SQL에 절이 붙는지까지만 확인합니다.

---

## 전체 알림 읽음 처리 — `PATCH /api/v1/users/me/notifications/read-all`

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_read_all_notifications_updates_unread_rows_in_single_statement | 기본 요청 | 204 + Body 없음 + execute 1회 + commit 1회 + add 호출 없음 | PASS |
| 정상 | test_read_all_notifications_targets_only_current_user_unread_rows | 기본 요청 | `UPDATE notification SET` + `user_id = 1` + `is_read IS false` + 소유권·유형 조건 없음 | PASS |
| 정상 | test_read_all_notifications_stores_same_korea_read_at_for_every_row | 기본 요청 | KST 시각 1회만 생성 + 모든 대상에 동일한 `read_at` + `is_read=true` | PASS |
| 정상 변형 | test_read_all_notifications_succeeds_when_no_unread_notification | 대상 0건 | 204 + commit 1회 (멱등) | PASS |
| 예외 | test_read_all_notifications_rolls_back_when_commit_fails | commit 실패 | 500 + rollback 1회 | PASS |
| 문서 | test_read_all_notifications_swagger_contract | OpenAPI 문서 | 응답 코드 `{204}` + 파라미터 없음 + HTTPBearer | PASS |

### 검증하지 않은 항목
- 오류: 명세에 이 API의 도메인 오류가 없어 404/409 케이스는 해당 없음.
- 요청 검증·경계값: Path/Query/Body가 모두 없어 해당 없음.
- 이미 읽은 알림의 `read_at` 보존은 UPDATE의 `is_read IS false` 조건으로 보장되므로,
  행별 결과가 아니라 WHERE 절로 검증합니다.

---

## 미션 진행도 반영 — `GET /api/v1/users/me/home`

autouse fixture `mission_progress` 가 `app.home.service.increase_mission_progress` 를 patch 합니다.
진행도 계산 자체는 `app/mission/docs/TEST_GUIDE.MD` 의 미션 진행도 반영 섹션에서 검증합니다.
홈 조회는 진행도 저장 때문에 commit 을 하게 되어 rollback 도 함께 검증합니다.

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_home_increases_home_view_mission_progress_and_commits | 홈 조회 성공 | `HOME_VIEW` 로 1회 호출 + commit 1회 | PASS |
| 오류 | test_home_does_not_increase_progress_when_ownership_is_inactive | 비활성 소유권만 있음 | 403 + 호출·commit 없음 | PASS |
| 예외 | test_home_rolls_back_when_commit_fails | commit 이 예외 발생 | 500 + rollback 1회 | PASS |
