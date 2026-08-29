# 큐브 도메인 테스트 가이드

테스트 파일: `tests/test_cube.py`
실행: `.venv\Scripts\python.exe -m pytest tests/test_cube.py -q`
최종 실행 결과: 35 passed (2026-08-29)

DB는 `unittest.mock.Mock` 으로 대체하고 `app.dependency_overrides[get_db]` 로 주입합니다.
실제 MySQL에는 접속하지 않습니다.

---

## 아바타 닉네임 설정 — `PATCH /api/v1/users/me/cube-ownerships/{cubeOwnershipId}/avatar-nickname`

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_update_avatar_nickname_success_saves_nickname | `"젠득이"` | 204, `avatar_nickname="젠득이"`, commit 1회 | PASS |
| 정상 변형 | test_update_avatar_nickname_trims_surrounding_whitespace | `"  젠득이  "` | 204, `"젠득이"` 로 저장 | PASS |
| 정상 변형 | test_update_avatar_nickname_overwrites_existing_nickname | 기존 `"이전닉네임"` → `"새닉네임"` | 204, 새 값으로 변경 | PASS |
| 정상 변형 | test_update_avatar_nickname_allows_same_nickname_as_current | 기존과 동일한 값 | 204, commit 1회 | PASS |
| 정상 변형 | test_update_avatar_nickname_allows_special_characters_and_inner_space | `"Jennie 젠득 01 ♥!"` | 204, 문자 종류 제한 없음 | PASS |
| 경계값 | test_update_avatar_nickname_allows_minimum_length_nickname | 1자 | 204 | PASS |
| 경계값 | test_update_avatar_nickname_allows_maximum_length_nickname | 30자 | 204 | PASS |
| 경계값 | test_update_avatar_nickname_allows_maximum_length_after_trimming | 공백 + 30자 + 공백 (원문 34자) | 204, trim 후 30자로 통과 | PASS |
| 경계값 | test_update_avatar_nickname_returns_400_when_nickname_exceeds_maximum_length | 31자 | 400 INVALID_REQUEST | PASS |
| 요청 검증 | test_update_avatar_nickname_returns_400_when_nickname_is_empty | `""` | 400 INVALID_REQUEST | PASS |
| 요청 검증 | test_update_avatar_nickname_returns_400_when_nickname_is_only_whitespace | `"   "` | 400 INVALID_REQUEST | PASS |
| 요청 검증 | test_update_avatar_nickname_returns_400_when_nickname_is_null | `null` | 400 INVALID_REQUEST | PASS |
| 요청 검증 | test_update_avatar_nickname_returns_400_when_nickname_is_missing | Body에 필드 없음 | 400 INVALID_REQUEST | PASS |
| 요청 검증 | test_update_avatar_nickname_returns_400_when_nickname_type_is_invalid | `1234` (number) | 400 INVALID_REQUEST | PASS |
| 경계값 | test_update_avatar_nickname_allows_minimum_ownership_id | `cubeOwnershipId=1` | 204 | PASS |
| 경계값 | test_update_avatar_nickname_returns_400_when_ownership_id_is_zero | `cubeOwnershipId=0` | 400 INVALID_REQUEST | PASS |
| 요청 검증 | test_update_avatar_nickname_returns_400_when_ownership_id_is_not_a_number | `cubeOwnershipId=abc` | 400 INVALID_REQUEST | PASS |
| 오류 | test_update_avatar_nickname_returns_404_when_ownership_not_found | 조회 결과 없음 | 404 CUBE_OWNERSHIP_NOT_FOUND, commit 없음 | PASS |
| 소유권/상태 | test_update_avatar_nickname_queries_only_own_active_last_accessed_ownership | 조회 SQL 검증 | WHERE에 `id`, `user_id=1`, `ownership_status='ACTIVE'`, `is_last_accessed IS true`, `FOR UPDATE` 포함 | PASS |
| 예외 | test_update_avatar_nickname_rolls_back_when_commit_fails | commit이 예외 발생 | 500, rollback 1회 | PASS |
| 문서 | test_update_avatar_nickname_swagger_contract | OpenAPI 스키마 | 응답 코드 `{204, 400, 404}` | PASS |

### 검증하지 않은 항목

- **"다른 사용자의 소유권" 과 "존재하지 않는 소유권" 을 개별 테스트로 나누지 않았습니다.**
  DB가 Mock이라 두 경우 모두 `db.scalar()` 가 `None` 을 반환해 결과가 동일합니다.
  대신 `..._queries_only_own_active_last_accessed_ownership` 에서 실제 생성되는 SQL의
  WHERE 절에 `user_id` / `ownership_status` / `is_last_accessed` 조건이 들어가는지를 검증했습니다.
  같은 이유로 `ownership_status != ACTIVE`, `is_last_accessed = false` 케이스도 SQL 검증으로 대신했습니다.
- **닉네임 중복 허용**은 DB 제약이 없고(UNIQUE 아님) 서비스에서 중복 조회도 하지 않으므로
  별도 테스트를 만들지 않았습니다. 다른 사용자와 같은 닉네임을 막는 코드 자체가 없습니다.
- **DB 저장 결과 자체**(실제 UPDATE 반영)는 Mock 환경이라 검증 대상이 아닙니다.
  ORM 객체의 `avatar_nickname` 속성 변경과 `commit()` 호출까지만 확인합니다.

---

## 큐브 코드 인증 — `POST /api/v1/cubes/verification`

`set_verification_results()` 헬퍼로 `db.scalar` 호출 순서(큐브 → 기존 소유권 → 1레벨)와
`db.scalars` 의 1레벨 보상 목록을 지정하고, `db.add` 로 저장된 ORM 객체를 모아 검증합니다.

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_create_cube_verification_success_creates_ownership | 인증번호 일치, 미등록 큐브 | 201 + `{"cubeOwnershipId": 4}`, 인증·소유권 생성 | PASS |
| 정상 | test_create_cube_verification_success_creates_first_level_affinity | 인증번호 일치, 1레벨 데이터 존재 | 친밀도 1건 생성(`cube_ownership_id=4`, `level_id=7`, `current_xp=0`), commit 1회 | PASS |
| 정책 | test_create_cube_verification_queries_first_level_row | 1레벨 조회 SQL 검증 | `FROM level`, `level.level = 1` | PASS |
| 정상 | test_create_cube_verification_success_grants_first_level_rewards | 1레벨 보상 2건 존재 | `UserReward` 2건 생성(`reward_item_id=[6, 10]`, `cube_ownership_id=4`), commit 1회 | PASS |
| 정상 | test_create_cube_verification_uses_same_acquired_at_for_rewards | 인증 성공 | 보상의 `acquired_at` 이 소유권 `acquired_at` 과 동일 | PASS |
| 정책 | test_create_cube_verification_queries_only_first_level_rewards | 보상 조회 SQL 검증 | `reward_item.reward_level = 1`, `deleted_at IS NULL`, `ORDER BY reward_item.id ASC` | PASS |
| 예외 | test_create_cube_verification_rolls_back_when_reward_query_fails | 보상 조회·저장 실패 | 500 + 보상 미생성, rollback 1회, commit 없음 | PASS |
| 예외 | test_create_cube_verification_rolls_back_when_first_level_is_missing | `level = 1` 데이터 없음 | 500 INTERNAL_SERVER_ERROR, 친밀도 미생성, rollback 1회, commit 없음 | PASS |
| 예외 | test_create_cube_verification_rolls_back_when_commit_fails | commit이 예외 발생 | 500 + rollback 1회 | PASS |
| 오류 | test_create_cube_verification_returns_404_when_cube_not_found | 큐브 없음 | 404 CUBE_NOT_FOUND | PASS |
| 오류 | test_create_cube_verification_returns_409_when_cube_already_owned | 이미 소유권 존재 | 409 CUBE_NOT_REGISTRABLE | PASS |
| 오류 | test_create_cube_verification_returns_409_when_cube_status_is_not_unregistered | status=OWNED | 409 CUBE_NOT_REGISTRABLE | PASS |
| 오류 | test_create_cube_verification_returns_400_when_code_invalid | 인증번호 불일치 | 400 INVALID_CUBE_CODE, FAILED 이력만 저장(소유권·친밀도·보상 미생성) | PASS |
| 요청 검증 | test_create_cube_verification_returns_400_when_required_body_missing | ownershipCode 누락 | 400 INVALID_REQUEST | PASS |
