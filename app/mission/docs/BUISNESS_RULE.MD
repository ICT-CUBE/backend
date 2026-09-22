# Mission 도메인 비즈니스 룰

## 데일리 미션 상세 조회

- 데일리 미션 상세 조회는 현재 사용자의 활성 마지막 접근 큐브 소유권을 기준으로 허용한다.
- 상세 조회 식별자로 미션 진행 정보 id가 아닌 미션 id를 사용한다.
- 활성 상태이고 삭제되지 않은 `DAILY` 미션만 상세 조회할 수 있다.
- 미션 진행 정보의 존재 여부는 상세 조회 가능 여부에 영향을 주지 않는다.
- 미션 안내 문구는 `mission_info`에 저장된 사용자 표시용 문자열을 그대로 사용한다.
- 미션과 연결된 보상 아이템이 삭제되었거나 존재하지 않으면 해당 미션을 유효하지 않은 것으로 처리한다.
- 상세 응답에는 미션 수행 조건을 나타내는 `target_action`을 노출하지 않는다.
- 상세 조회는 미션 및 미션 진행 상태를 변경하지 않는다.

## 미션 보상 수령

### API 기본 규칙

- 미션 보상 수령은 `POST /api/v1/users/me/missions/{missionId}/rewards` 엔드포인트를 사용한다.
- Path의 `missionId`와 요청 Body의 `missionType`을 필수값으로 받는다.
- `missionId`는 1 이상의 정수여야 한다.
- `missionType`은 `DAILY` 또는 `EVENT`만 허용한다.
- 요청값 검증에 실패하면 공통 `400 INVALID_REQUEST`를 반환한다.
- 보상 수령 성공 시 `200 OK`와 레벨 상승 정보를 반환한다.

### 인증 및 지급 대상

- 이 API는 인증이 필요한 API다.
- 클라이언트가 전달한 `Authorization: Bearer {accessToken}` 헤더의 JWT를 공통 인증 의존성에서 검증한다.
- 서비스에는 검증된 JWT의 `sub`에서 얻은 현재 사용자 ID를 전달한다.
- 보상은 현재 사용자의 `ownership_status = ACTIVE`이고 `is_last_accessed = true`인 큐브 소유권에 귀속한다.
- 조건을 충족하는 큐브 소유권이 없으면 `404 CUBE_OWNERSHIP_NOT_FOUND`를 반환한다.
- `user_reward`와 `affinity`는 사용자 ID가 아니라 조회한 `cube_ownership.id`를 기준으로 처리한다.

### 미션과 진행 상태 검증

- `mission.id`와 요청한 `missionId`가 일치해야 한다.
- `mission.mission_type`과 요청한 `missionType`이 일치해야 한다.
- 미션은 `is_active = true`이고 `deleted_at IS NULL`이어야 한다.
- 연결된 보상 아이템이 존재하고 `reward_item.deleted_at IS NULL`이어야 한다.
- 위 조건을 충족하는 미션이 없거나 보상 아이템이 유효하지 않으면 `404 MISSION_NOT_FOUND`를 반환한다.
- 요청한 유형과 실제 미션 유형이 일치하지 않는 경우에도 `404 MISSION_NOT_FOUND`를 반환한다.
- 현재 큐브 소유권과 미션에 대응하는 `mission_progress`를 조회한다.
- 진행 상태가 `COMPLETED` 또는 `REWARDED`인 경우 보상을 지급한다.
- 진행 상태가 `IN_PROGRESS`이거나 진행 정보가 존재하지 않으면 `409 MISSION_NOT_COMPLETED`를 반환한다.
- 별도의 중복 지급 검사는 수행하지 않는다.
- 이미 `REWARDED`인 진행 정보를 다시 요청해도 미션 보상을 다시 지급한다.

### 미션 보상 지급

- 미션에 연결된 `reward_item`으로 `user_reward`를 생성한다.
- `user_reward.cube_ownership_id`에는 현재 활성 마지막 접근 큐브 소유권 id를 저장한다.
- `user_reward.reward_item_id`에는 미션의 보상 아이템 id를 저장한다.
- `user_reward.acquired_at`에는 한국시간 기준 현재 시각을 저장한다.
- `AFFINITY_POINT`를 포함한 모든 보상 유형은 보상 수령 요청마다 `user_reward`에 추가한다.
- `CONVERSATION_COUNT`, `COMMENT_TYPE`, `SPECIAL_COMMENT`, `AVATAR_FIRST_TALK`, `BADGE`는 별도 상태를 변경하지 않고 `user_reward` 추가만 수행한다.

### 친밀도 포인트 지급

- 미션 보상의 `reward_type = AFFINITY_POINT`인 경우에만 친밀도 포인트와 레벨을 변경한다.
- 현재 큐브 소유권에 연결된 `affinity`가 없으면 `404 CUBE_AFFINITY_NOT_FOUND`를 반환한다.
- 동시 보상 수령에 의한 포인트 유실을 막기 위해 친밀도 행을 잠금 조회한다.
- `reward_item.reward_count`를 기존 `affinity.current_xp`에 더한 값을 새 누적 XP로 저장한다.
- `AFFINITY_POINT` 보상의 `reward_count`가 `NULL`이거나 0 이하이면 서버 기준 데이터 오류로 보고 공통 `500 INTERNAL_SERVER_ERROR`를 반환한다.
- `current_xp`는 레벨별 구간 XP가 아닌 전체 누적 친밀도 포인트로 유지한다.

### 레벨 계산과 변경

- 새 레벨은 `level.level_xp`가 새 누적 XP 이하인 레벨 중 `level.level`이 가장 높은 레벨로 결정한다.
- 결정된 레벨이 기존 레벨보다 높으면 레벨이 상승한 것으로 판단한다.
- 새 누적 XP가 다음 레벨의 `level_xp`에 도달하지 못하면 `affinity.level_id`를 변경하지 않는다.
- 레벨이 상승하면 `affinity.level_id`를 최종 도달 레벨의 id로 변경한다.
- 한 번의 포인트 지급으로 여러 레벨 기준을 통과할 수 있으며 이 경우 가장 높은 최종 레벨로 변경한다.
- 현재 `affinity.level_id`에 대응하는 레벨 데이터가 없거나 새 레벨을 계산할 수 없으면 서버 기준 데이터 오류로 보고 공통 `500 INTERNAL_SERVER_ERROR`를 반환한다.
- 최고 레벨에서 포인트를 추가로 받아도 `current_xp`는 계속 누적하며 레벨 상승으로 처리하지 않는다.

### 레벨 보상 지급

- 레벨이 상승하면 기존 레벨보다 높고 최종 도달 레벨 이하인 모든 레벨의 보상을 지급한다.
- 지급 대상은 `reward_item.reward_level > 기존 레벨`, `reward_item.reward_level <= 최종 도달 레벨`, `reward_item.deleted_at IS NULL` 조건을 모두 만족하는 보상이다.
- 여러 레벨을 한 번에 통과하면 중간에 통과한 레벨의 보상도 빠짐없이 지급한다.
- 각 레벨 보상마다 현재 큐브 소유권을 대상으로 별도의 `user_reward`를 생성한다.
- 레벨 보상에 대해서도 별도의 중복 지급 검사는 수행하지 않는다.
- 레벨이 상승하지 않으면 레벨 보상을 지급하지 않는다.

### 미션 진행 상태 변경

- 보상 지급 후 `mission_progress.status`를 `REWARDED`로 변경한다.
- `mission_progress.reward_claimed`를 `true`로 변경한다.
- `mission_progress.claimed_at`에는 이번 요청의 한국시간 기준 수령 시각을 저장한다.
- 이미 `REWARDED`인 미션을 다시 수령하면 `claimed_at`을 이번 수령 시각으로 갱신한다.

### 응답

- 레벨이 상승하면 `levelUp`에 최종 도달 레벨의 숫자와 이름을 반환한다.
- 여러 레벨을 한 번에 통과해도 중간 레벨 목록은 반환하지 않고 최종 레벨만 반환한다.
- 레벨이 상승하지 않으면 `levelUp`은 `null`이다.
- 포인트가 아닌 미션 보상을 지급한 경우에도 `levelUp`은 `null`이다.
- 레벨 이름은 `level.level_name`에 저장된 `Intro`, `Friend`, `Close`, `Special` 중 해당 값을 반환한다.

### 트랜잭션과 오류 처리

- 미션 보상 생성, 친밀도 포인트와 레벨 변경, 레벨 보상 생성 및 미션 진행 상태 변경은 하나의 DB 트랜잭션에서 처리한다.
- 모든 `user_reward.acquired_at`과 `mission_progress.claimed_at`은 한 번 계산한 동일한 수령 시각을 사용한다.
- 처리 중 하나라도 실패하면 전체 트랜잭션을 롤백한다.
- 잘못된 요청값은 공통 `400 INVALID_REQUEST`로 처리한다.
- 유효하지 않거나 만료된 Access Token은 공통 `401 INVALID_ACCESS_TOKEN`으로 처리한다.
- 활성 마지막 접근 큐브 소유권이 없으면 `404 CUBE_OWNERSHIP_NOT_FOUND`를 반환한다.
- 미션 또는 보상 아이템이 유효하지 않으면 `404 MISSION_NOT_FOUND`를 반환한다.
- 친밀도 정보가 없으면 `404 CUBE_AFFINITY_NOT_FOUND`를 반환한다.
- 완료되지 않은 미션은 `409 MISSION_NOT_COMPLETED`를 반환한다.
- 기준 데이터가 유효하지 않거나 저장 중 오류가 발생하면 공통 `500 INTERNAL_SERVER_ERROR`로 처리한다.
