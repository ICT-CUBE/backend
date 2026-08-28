# 친밀도 도메인 테스트 가이드

테스트 파일: `tests/test_affinity.py`
실행: `.venv\Scripts\python.exe -m pytest tests/test_affinity.py -q`
최종 실행 결과: 15 passed (2026-08-28)

DB는 `Mock(spec=Session)` 으로 대체하고 `app.dependency_overrides[get_db]` 로 주입합니다.
실제 MySQL에는 접속하지 않습니다.

이 API는 `db.scalars` 를 순서대로 여러 번 호출하므로, 테스트는 `set_query_results()` 헬퍼로
호출 순서에 맞춰 결과를 지정합니다.

```text
1) level 전체          2) 현재 레벨 획득 보상    3) 다음 레벨 보상(최고 레벨이면 생략)
4) DAILY 미션          5) 미션 진행(미션이 없으면 생략)
```

---

## 친밀도 상세 조회 — `GET /api/v1/users/me/affinity`

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_read_affinity_returns_full_detail | 레벨3, XP 1245, 보상·미션·진행 존재 | 200 + 응답 JSON 전체 일치 | PASS |
| 정상 변형 | test_read_affinity_returns_null_next_level_at_maximum_level | 최고 레벨(4), XP 2500 | `nextLevel=null`, `progressPercent=100`, `remainingXp=0`, 최고 레벨만 CURRENT | PASS |
| 정상 변형 | test_read_affinity_returns_defaults_for_mission_without_progress | 진행 정보 없는 DAILY 미션 | `currentCount=0`, `IN_PROGRESS`, `rewardClaimed=false` | PASS |
| 정상 변형 | test_read_affinity_returns_empty_daily_activities_when_no_mission | DAILY 미션 0건 | `dailyActivities=[]`, 진행 조회 쿼리 미실행(scalars 4회) | PASS |
| 정상 변형 | test_read_affinity_returns_empty_rewards_when_none_acquired | 획득/해금 보상 0건 | 현재·다음 레벨 `rewards=[]` | PASS |
| 경계값 | test_read_affinity_truncates_progress_percent | XP 1999 / 다음 레벨 2000 | 99.95 → `99`, `remainingXp=1` (버림 확인) | PASS |
| 경계값 | test_read_affinity_returns_zero_progress_when_no_xp_earned | 레벨1, XP 0 | `progressPercent=0`, `remainingXp=100` | PASS |
| 경계값 | test_read_affinity_caps_progress_percent_at_100_when_xp_exceeds_next_level | XP 99999 | `progressPercent=100`(상한), `remainingXp=0`(하한) | PASS |
| 오류 | test_read_affinity_returns_404_when_ownership_not_found | 소유권 조회 결과 없음 | 404 CUBE_OWNERSHIP_NOT_FOUND, 이후 쿼리 미실행 | PASS |
| 오류 | test_read_affinity_returns_404_when_affinity_not_found | 소유권은 있으나 친밀도 없음 | 404 CUBE_AFFINITY_NOT_FOUND, 이후 쿼리 미실행 | PASS |
| 소유권 | test_read_affinity_queries_only_own_active_last_accessed_ownership | 조회 SQL 검증 | WHERE에 `user_id=1`, `ownership_status='ACTIVE'`, `is_last_accessed IS true` 포함 | PASS |
| 정책 | test_read_affinity_excludes_deleted_reward_items_and_orders_by_id | 보상 조회 SQL 검증 | 두 쿼리 모두 `deleted_at IS NULL` + `ORDER BY reward_item.id ASC`, 현재 레벨 쿼리만 `user_reward` 조인 + `DISTINCT` | PASS |
| 정책 | test_read_affinity_filters_daily_missions_by_active_state_and_period | 미션 조회 SQL 검증 | `mission_type`, `is_active IS true`, `deleted_at IS NULL`, 기간 NULL 허용, `ORDER BY mission.id ASC` | PASS |
| 정책 | test_read_affinity_orders_levels_by_level_number | 레벨 조회 SQL 검증 | `ORDER BY level.level ASC` | PASS |
| 문서 | test_read_affinity_swagger_contract | OpenAPI 스키마 | 응답 코드 `{200, 404}` | PASS |

### 목데이터 대조 검증 (일회성)

단위 테스트와 별개로, `scripts/sql/02-data-mock.sql` 의 실제 데이터(사용자 1, 소유권 1,
레벨 3, XP 1245)를 SQLite에 적재하고 `get_affinity()` 를 그대로 실행해 API_SPEC의 예시 응답과
대조했습니다. 아래 값이 명세 예시와 일치함을 확인했습니다.

```text
progressPercent: 62 | remainingXp: 755
currentLevel: 3 Close  rewards: [8, 12, 13, 15]
nextLevel:    4 Special rewards: [9, 16]
levels: [(1 COMPLETED) (2 COMPLETED) (3 CURRENT) (4 LOCKED)]
```

### 검증하지 않은 항목

- **"다른 사용자의 소유권" 과 "존재하지 않는 소유권"** 은 Mock DB에서 결과가 같아 개별 테스트로
  나누지 않고, `..._queries_only_own_active_last_accessed_ownership` 의 SQL 검증으로 대신했습니다.
  `ownership_status != ACTIVE`, `is_last_accessed = false` 도 같은 이유입니다.
- **삭제된 보상 아이템 제외, 기간이 지난 미션 제외**는 Mock DB가 WHERE 절을 실제로 실행하지 않아
  결과로 확인할 수 없어, 생성된 SQL에 조건이 포함되는지로 검증했습니다.
- **`reward_level` 값이 실제 존재하는 `level.level` 인지에 대한 검증**은 이 API의 책임이 아닙니다.
  BUISNESS_RULE에 "보상 등록 또는 변경 시 검증한다"고 되어 있어, 조회 API에서는 검사하지 않습니다.
- **조회 시 부수효과 없음**은 대표 케이스에서 `db.commit.assert_not_called()` 로만 확인했습니다.
