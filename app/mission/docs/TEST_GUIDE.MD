# mission 테스트 가이드

테스트 파일: `app/mission/tests/test_mission.py`
실행: `.venv\Scripts\python.exe -m pytest app/mission/tests/test_mission.py -q`
최종 실행 결과: 58 passed (2026-09-22)

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

## 미션 보상 수령 — `POST /api/v1/users/me/missions/{missionId}/rewards`

서비스가 `db.scalar` 를 큐브 소유권 → 미션 → 미션 진행 정보 → (친밀도 포인트 보상일 때만)
친밀도(잠금) → 현재 레벨 → 도달 레벨 순서로 호출하고, 레벨이 오르면 `db.scalars` 로 레벨 보상을
조회합니다. `set_mission_reward_results()` 가 그 순서대로 결과를 지정하고 `db.add` 로 저장한
`user_reward` 를 모읍니다. 포인트 보상의 기본 조회 결과는 `set_point_reward_results()` 로 만들며,
레벨 기준 데이터는 목데이터와 같은 `LEVELS` (0 / 100 / 800 / 2000 XP)를 씁니다.

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_create_mission_reward_grants_point_without_level_up | 1레벨 40XP + 30포인트 | 200 + `{levelUp: null}`, `user_reward` 1건, XP 70·레벨 유지, 진행 `REWARDED`·`reward_claimed`·`claimed_at`(naive), 레벨 보상 조회 없음, commit 1회 | PASS |
| 정상 변형 | test_create_mission_reward_grants_level_reward_when_level_up | 1레벨 90XP + 30포인트 | 200 + `{levelUp: {level: 2, levelName: "Friend"}}`, 미션·2레벨 보상 2건, XP 120·`level_id=2` | PASS |
| 정상 변형 | test_create_mission_reward_grants_every_passed_level_reward | 1레벨 90XP + 1000포인트 | 200 + 최종 3레벨 `Close`만 반환, 미션·2·3레벨 보상 3건, 레벨 보상 SQL `reward_level > 1`·`<= 3`·삭제 제외·정렬 | PASS |
| 정상 변형 | test_create_mission_reward_uses_same_time_for_all_rewards_and_progress | 레벨 상승 | 모든 `acquired_at` 과 `claimed_at` 이 같은 시각 | PASS |
| 정상 변형 | test_create_mission_reward_keeps_max_level_and_accumulates_xp | 4레벨 2500XP + 30포인트 | `levelUp: null`, XP 2530 누적·레벨 유지, 레벨 보상 조회 없음 | PASS |
| 정상 변형 | test_create_mission_reward_grants_non_point_reward_only | BADGE 보상 | `levelUp: null`, `user_reward` 1건, 진행 `REWARDED`, 친밀도·레벨 조회 없음(scalar 3회) | PASS |
| 정상 변형 | test_create_mission_reward_accepts_event_mission | `missionType: EVENT` | 200 + 미션 SQL `mission_type = 'EVENT'` | PASS |
| 상태 전이 | test_create_mission_reward_grants_again_when_already_rewarded | 이미 `REWARDED` | 200 + 보상 재지급, `claimed_at` 갱신 (명세상 중복 검사 없음) | PASS |
| 오류 | test_create_mission_reward_returns_404_when_cube_ownership_not_found | 소유권 없음 | 404 CUBE_OWNERSHIP_NOT_FOUND + 이후 조회·저장 없음 | PASS |
| 오류 | test_create_mission_reward_returns_404_when_mission_not_found | 미션 조회 결과 없음 | 404 MISSION_NOT_FOUND + 이후 조회·저장 없음 | PASS |
| 오류 | test_create_mission_reward_returns_404_when_affinity_not_found | 포인트 보상 + 친밀도 없음 | 404 CUBE_AFFINITY_NOT_FOUND + 저장 없음 | PASS |
| 오류 | test_create_mission_reward_returns_409_when_mission_in_progress | 진행 `IN_PROGRESS` | 409 MISSION_NOT_COMPLETED + 상태 변경·저장 없음 | PASS |
| 오류 | test_create_mission_reward_returns_409_when_progress_not_found | 진행 정보 없음 | 409 MISSION_NOT_COMPLETED + 저장 없음 | PASS |
| 예외 | test_create_mission_reward_returns_500_when_point_reward_count_is_null | 포인트 `reward_count = NULL` | 공통 500 JSON + 저장 없음 | PASS |
| 예외 | test_create_mission_reward_returns_500_when_point_reward_count_is_zero | 포인트 `reward_count = 0` | 공통 500 JSON + commit 없음 | PASS |
| 예외 | test_create_mission_reward_returns_500_when_current_level_not_found | 현재 레벨 데이터 없음 | 공통 500 JSON + 저장 없음 | PASS |
| 예외 | test_create_mission_reward_returns_500_when_reached_level_not_found | 도달 레벨 계산 불가 | 공통 500 JSON + commit 없음 | PASS |
| 예외 | test_create_mission_reward_rolls_back_when_commit_fails | commit이 예외 발생 | 500 + rollback 1회 | PASS |
| 소유권 | test_create_mission_reward_queries_active_last_accessed_ownership | 로그인 사용자 id=1 | `user_id = 1` + `ownership_status = 'ACTIVE'` + `is_last_accessed IS true` | PASS |
| 정책 | test_create_mission_reward_queries_active_mission_of_requested_type | missionId=4, DAILY | `JOIN reward_item` + `mission.id = 4` + `mission_type = 'DAILY'` + `is_active IS true` + 미션·보상 아이템 삭제 제외 | PASS |
| 정책 | test_create_mission_reward_queries_progress_of_current_ownership | 기본 요청 | `mission_progress.cube_ownership_id = 1` + `mission_id = 4` | PASS |
| 정책 | test_create_mission_reward_locks_affinity_and_finds_reached_level | 90XP + 30포인트 | 친밀도 `cube_ownership_id = 1` + `FOR UPDATE`, 도달 레벨 `level_xp <= 120` + `ORDER BY level DESC` | PASS |
| 경계값 | test_create_mission_reward_allows_minimum_mission_id | missionId=1 | 200 | PASS |
| 경계값 | test_create_mission_reward_returns_400_when_mission_id_is_zero | missionId=0 | 400 INVALID_REQUEST + 조회 안 함 | PASS |
| 요청 검증 | test_create_mission_reward_returns_400_when_mission_id_is_not_number | missionId=abc | 400 INVALID_REQUEST + 조회 안 함 | PASS |
| 요청 검증 | test_create_mission_reward_returns_400_when_mission_type_is_missing | Body `{}` | 400 INVALID_REQUEST + 조회 안 함 | PASS |
| 요청 검증 | test_create_mission_reward_returns_400_for_unsupported_mission_type | `missionType: WEEKLY` | 400 INVALID_REQUEST + 조회 안 함 | PASS |
| 문서 | test_create_mission_reward_swagger_contract | OpenAPI 문서 | 응답 코드 `{200, 404, 409}` + 파라미터 `{missionId}` + 요청 Body + HTTPBearer | PASS |

### 검증하지 않은 항목
- "없는 미션" / "비활성 미션" / "삭제된 미션" / "유형 불일치" / "보상 아이템이 삭제된 미션" 은
  Mock DB로는 모두 `db.scalar` 가 `None` 을 돌려주는 같은 경로라, 같은 404
  `MISSION_NOT_FOUND` 응답과 미션 조회 SQL 조건으로 검증했습니다.
- 도달 레벨 계산 결과 자체(`level_xp <= 누적 XP` 중 최고 레벨)는 Mock DB가 계산하지 않으므로
  지정한 결과가 반영되는지와 계산 SQL 조건만 확인했습니다.
- 친밀도 행 잠금(`FOR UPDATE`)의 실제 동시성 동작은 SQL에 절이 붙는지까지만 확인했습니다.
- 소유권: 다른 사용자의 큐브 소유권은 소유권 조회 SQL의 `user_id` 조건으로 걸러지므로
  별도 케이스 없이 SQL로 검증했습니다.

---

## 미션 진행도 반영 — `app/mission/progress.py` `increase_mission_progress`

API가 아니라 다른 도메인 서비스가 호출하는 공통 함수라 함수를 직접 호출해 검증합니다.
`db.scalar` 를 활성 마지막 접근 소유권 id → 미션별 진행 행(잠금) 순서로, `db.scalars` 를 미션
목록 조회에 쓰므로 `set_progress_results()` 가 그 순서대로 결과를 지정하고 `db.add` 로 새로 만든
진행 행을 모읍니다.

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_increase_mission_progress_creates_progress_when_no_history | 진행 행 없음, 목표 3 | 새 행 1건 `count=1`·`IN_PROGRESS`·`reward_claimed=false` | PASS |
| 정상 | test_increase_mission_progress_increments_in_progress_count | `count=1`, 목표 3 | `count=2`, `IN_PROGRESS` 유지, 새 행 없음 | PASS |
| 정상 변형 | test_increase_mission_progress_completes_new_progress_when_target_is_one | 진행 행 없음, 목표 1 | 새 행 `count=1`·`COMPLETED`·`completed_at`(naive) | PASS |
| 정상 변형 | test_increase_mission_progress_completes_when_reaching_target_count | `count=2`, 목표 3 | `count=3`·`COMPLETED`·`completed_at` 설정 | PASS |
| 정상 변형 | test_increase_mission_progress_updates_every_mission_of_action | 같은 행동의 미션 2개 | 두 미션 모두 반영 | PASS |
| 정상 변형 | test_increase_mission_progress_does_nothing_when_no_matching_mission | 해당 행동의 활성 미션 없음 | 진행 행 조회·생성 없음 | PASS |
| 정상 변형 | test_increase_mission_progress_skips_when_cube_ownership_not_found | 활성 마지막 접근 소유권 없음 | 미션 조회·생성 없이 종료(오류 없음) | PASS |
| 상태 전이 | test_increase_mission_progress_keeps_completed_progress | 이미 `COMPLETED` | 횟수·상태·`completed_at` 그대로 | PASS |
| 상태 전이 | test_increase_mission_progress_keeps_rewarded_progress | 이미 `REWARDED` | 횟수·상태·`reward_claimed` 그대로 | PASS |
| 상태 전이 | test_increase_mission_progress_resets_daily_progress_of_previous_day | DAILY, 어제 갱신된 `REWARDED` | 초기화 후 `count=1`·`IN_PROGRESS`, `reward_claimed=false`, `completed_at`·`claimed_at` NULL | PASS |
| 상태 전이 | test_increase_mission_progress_resets_and_completes_daily_target_one | DAILY 목표 1, 3일 전 `COMPLETED` | 초기화 후 오늘 날짜로 다시 `COMPLETED` | PASS |
| 상태 전이 | test_increase_mission_progress_does_not_reset_event_progress | EVENT, 어제 갱신된 `REWARDED` | 초기화하지 않고 그대로 | PASS |
| 트랜잭션 | test_increase_mission_progress_does_not_commit | 새 행 생성 | commit·rollback 호출 없음(호출한 서비스가 commit) | PASS |
| 소유권 | test_increase_mission_progress_queries_active_last_accessed_ownership | 사용자 id=1 | `user_id = 1` + `ownership_status = 'ACTIVE'` + `is_last_accessed IS true` | PASS |
| 정책 | test_increase_mission_progress_queries_active_missions_in_period | OPEN_GALLERY | `target_action = 'OPEN_GALLERY'` + `is_active IS true` + `deleted_at IS NULL` + 기간 조건(NULL 허용) | PASS |
| 정책 | test_increase_mission_progress_locks_progress_row | 미션 2 | 진행 행 조회 `cube_ownership_id = 1` + `mission_id = 2` + `FOR UPDATE` | PASS |

### 행동별 API 연결 (각 도메인 테스트 파일)

각 도메인 테스트 파일은 autouse fixture `mission_progress` 로 `app.<도메인>.service.increase_mission_progress`
를 patch 해 기존 테스트의 조회 순서에 영향을 주지 않게 하고, 아래 테스트에서만 호출 인자를 확인합니다.

| 행동 | API | 테스트 파일 | 호출 확인 | 실패 시 미호출 |
|---|---|---|---|---|
| HOME_VIEW | `GET /api/v1/users/me/home` | `app/home/tests/test_home.py` | test_home_increases_home_view_mission_progress_and_commits | test_home_does_not_increase_progress_when_ownership_is_inactive |
| CONVERSATION | `POST /api/v1/users/me/conversation-sessions/{id}/messages` | `app/conversation/tests/test_conversation.py` | test_reply_conversation_message_increases_conversation_mission_progress | test_reply_conversation_message_does_not_increase_progress_when_404 |
| ALBUM_PLAY | `POST /api/v1/tracks/{trackId}/sessions` | `app/album/tests/test_track.py` | test_create_track_session_increases_album_play_mission_progress | test_create_track_session_does_not_increase_progress_when_track_not_found |
| OPEN_GALLERY | `GET /api/v1/users/me/gallery/{sourceType}/{id}/ar-experience` | `app/gallery/tests/test_gallery.py` | test_gallery_ar_experience_increases_open_gallery_progress_and_commits | test_gallery_ar_experience_does_not_increase_progress_when_capture_missing |
| COMMUNITY_POST | `POST /api/v1/community/posts` | `app/community/tests/test_community.py` | test_create_post_increases_community_post_mission_progress | test_create_post_does_not_increase_progress_when_request_is_invalid |
| SUMMON_AVATAR | `POST /api/v1/users/me/avatar-interaction-sessions/{id}/pictures` | `app/avatar/tests/test_avatar.py` | test_save_avatar_interaction_picture_increases_summon_avatar_progress | test_save_avatar_interaction_picture_does_not_increase_progress_when_404 |
| PLAY_MUSIC_VIDEO | `POST /api/v1/stages/{stageId}/sessions` | `app/stage/tests/test_stage.py` | test_create_stage_session_increases_play_music_video_mission_progress | test_create_stage_session_does_not_increase_progress_when_stage_not_found |

조회 API였던 홈·갤러리는 진행도 저장 때문에 commit 이 새로 생겨
`test_home_rolls_back_when_commit_fails`, `test_gallery_ar_experience_rolls_back_when_commit_fails`
로 rollback 을 확인합니다.

### 검증하지 않은 항목
- 같은 (소유권, 미션) 진행 행이 없을 때 동시에 두 요청이 들어와 둘 다 INSERT 하는 경우는
  DDL 유니크 키가 한쪽을 막으며, Mock DB로 재현할 수 없어 검증하지 않았습니다.
- 데일리 초기화 기준인 `updated_at` 은 DB가 채우는 값이라 테스트에서는 직접 지정했습니다.
  날짜가 바뀌는 자정 직전·직후 경계는 시각 고정 없이 검증하지 않았습니다.
- 진행 행 잠금(`FOR UPDATE`)의 실제 동시성 동작은 SQL에 절이 붙는지까지만 확인했습니다.

---

## 미션 목록 조회 — `GET /api/v1/users/me/missions`

테스트 없음. 이번 작업(데일리 미션 상세 조회) 범위 밖이라 작성하지 않았습니다.
