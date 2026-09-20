# mission 테스트 가이드

테스트 파일: `app/mission/tests/test_mission.py`
실행: `.venv\Scripts\python.exe -m pytest app/mission/tests/test_mission.py -q`
최종 실행 결과: 14 passed (2026-09-20)

---

## 데일리 미션 상세 조회 — `GET /api/v1/users/me/daily-missions/{missionId}`

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_read_daily_mission_returns_mission_with_reward_item | 활성 소유권 + 활성 DAILY 미션 | 200 + `{mission: {..., rewardItem}}` 전체 + add/commit 호출 없음 | PASS |
| 정상 | test_read_daily_mission_does_not_expose_target_action | 활성 DAILY 미션 | 응답에 `targetAction`·`targetCount` 없음 | PASS |
| 정상 변형 | test_read_daily_mission_returns_null_mission_info | `mission_info = NULL` | 200 + `missionInfo: null` | PASS |
| 정상 변형 | test_read_daily_mission_returns_null_reward_count | `reward_count = NULL` (BADGE) | 200 + `rewardCount: null` | PASS |
| 오류 | test_read_daily_mission_returns_404_when_cube_ownership_not_found | 활성 마지막 접근 소유권 없음 | 404 CUBE_OWNERSHIP_NOT_FOUND + 미션 조회 안 함 | PASS |
| 오류 | test_read_daily_mission_returns_404_when_daily_mission_not_found | 미션 조회 결과 없음 | 404 DAILY_MISSION_NOT_FOUND | PASS |
| 소유권 | test_read_daily_mission_queries_active_last_accessed_ownership | 로그인 사용자 id=1 | `user_id = 1` + `ownership_status = 'ACTIVE'` + `is_last_accessed IS true` | PASS |
| 정상 | test_read_daily_mission_queries_only_active_daily_mission | missionId=4 | `mission.id = 4` + `mission_type = 'DAILY'` + `is_active IS true` + `deleted_at IS NULL` | PASS |
| 정상 | test_read_daily_mission_excludes_deleted_reward_item | 기본 요청 | `JOIN reward_item` + `reward_item.deleted_at IS NULL` | PASS |
| 정상 | test_read_daily_mission_does_not_filter_by_mission_progress | 기본 요청 | 미션 조회에 `mission_progress` 없음 + 조회 2회로 끝 | PASS |
| 경계값 | test_read_daily_mission_allows_minimum_mission_id | missionId=1 | 200 | PASS |
| 경계값 | test_read_daily_mission_returns_400_when_mission_id_is_zero | missionId=0 | 400 INVALID_REQUEST + 조회 안 함 | PASS |
| 요청 검증 | test_read_daily_mission_returns_400_when_mission_id_is_not_number | missionId=abc | 400 INVALID_REQUEST + 조회 안 함 | PASS |
| 문서 | test_read_daily_mission_swagger_contract | OpenAPI 문서 | 응답 코드 `{200, 404}` + 파라미터 `{missionId}` + HTTPBearer | PASS |

### 검증하지 않은 항목
- 상태 전이: 상세 조회는 미션·미션 진행 상태를 바꾸지 않아 해당 없음.
  대신 정상 케이스에서 `db.add` / `db.commit` 이 호출되지 않음을 확인합니다.
- 예외: 쓰기 트랜잭션이 없어 commit 실패/rollback 케이스는 해당 없음.
- 오류: 명세에 404 두 건 외의 도메인 오류가 없어 409 케이스는 해당 없음.
- "존재하지 않는 미션" / "EVENT 미션" / "비활성 미션" / "삭제된 미션" /
  "보상 아이템이 삭제된 미션" 은 Mock DB로는 모두 `db.scalar` 가 `None` 을 돌려주는
  동일한 경로라 응답으로 구분할 수 없습니다. 명세상 넷 다 같은 404
  `DAILY_MISSION_NOT_FOUND` 이므로 구분할 필요도 없고, 대신 select 문을
  `literal_binds` 로 컴파일해 네 조건이 WHERE·JOIN 절에 모두 들어가는지 검증합니다.
- 미션 목록 조회 API(`GET /api/v1/users/me/missions`)는 이번 작업 범위가 아니라
  테스트를 작성하지 않았습니다. (5장 참고)

---

## 미션 목록 조회 — `GET /api/v1/users/me/missions`

테스트 없음. 이번 작업(데일리 미션 상세 조회) 범위 밖이라 작성하지 않았습니다.
