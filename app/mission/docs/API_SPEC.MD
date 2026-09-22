## 데일리 미션 상세 조회
- http 메서드: get
- domain: mission
- endpoint: api/v1/users/me/daily-missions/{missionId}

### API 설명

사용자가 미션 목록에서 데일리 미션을 선택하면 호출한다.

선택한 데일리 미션의 안내 문구와 연결된 보상 정보를 반환한다.

---

### 처리 정책

- 현재 사용자의 `ownership_status = ACTIVE`이고 `is_last_accessed = true`인 큐브 소유권을 확인한다.
- 조건을 충족하는 큐브 소유권이 없으면 404: CUBE_OWNERSHIP_NOT_FOUND를 반환한다.
- `missionId`에 해당하는 미션이 `mission_type = DAILY`, `is_active = true`, `deleted_at IS NULL`인 경우에만 조회한다.
- 조건을 충족하는 데일리 미션이 없으면 404: DAILY_MISSION_NOT_FOUND를 반환한다.
- 미션 진행 정보의 존재 여부는 상세 조회 조건으로 사용하지 않는다.
- `missionInfo`는 `mission.mission_info`에 저장된 사용자 표시용 안내 문구를 그대로 반환한다.
- 미션과 연결된 보상 아이템이 존재하고 `deleted_at IS NULL`인 경우에만 정상 조회한다.
- 연결된 보상 아이템이 없거나 삭제되었으면 해당 데일리 미션을 유효하지 않은 것으로 보고 404: DAILY_MISSION_NOT_FOUND를 반환한다.
- 응답에는 `targetAction`을 포함하지 않는다.
- 이 API는 미션 또는 미션 진행 정보를 변경하지 않는다.

---

### 요청 Query

없음

---

### 요청 Path

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `missionId` | number | O | 상세 조회할 데일리 미션 id. 1 이상의 정수 |

```json
{
  "missionId": 4
}
```

---

### 요청 Body

없음

---

### 정상 응답 데이터

Status Code : 200

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `mission.id` | number | 데일리 미션 id |
| `mission.missionType` | string | 미션 유형. `DAILY` |
| `mission.title` | string | 미션 제목 |
| `mission.missionInfo` | string \| null | 사용자에게 표시할 미션 안내 문구 |
| `mission.rewardItem.id` | number | 보상 아이템 id |
| `mission.rewardItem.name` | string | 보상 아이템 이름 |
| `mission.rewardItem.rewardType` | string | 보상 유형 |
| `mission.rewardItem.rewardCount` | number \| null | 지급되는 보상 수량 |

```json
{
  "mission": {
    "id": 4,
    "missionType": "DAILY",
    "title": "아바타 현실 소환하기",
    "missionInfo": "아바타를 현실에 소환해 예절샷을 남겨보세요. AR 카메라로 3회 촬영하면 미션이 완료돼요!",
    "rewardItem": {
      "id": 5,
      "name": "친밀도 포인트",
      "rewardType": "AFFINITY_POINT",
      "rewardCount": 30
    }
  }
}
```

---

### 오류 응답 데이터

Status Code : 404

현재 사용자의 활성 마지막 접근 큐브 소유권을 찾을 수 없는 경우

```json
{
  "code": "CUBE_OWNERSHIP_NOT_FOUND",
  "message": "큐브 소유권 정보를 찾을 수 없습니다."
}
```

데일리 미션이 존재하지 않거나 조회 가능한 상태가 아니거나 연결된 보상 아이템이 유효하지 않은 경우

```json
{
  "code": "DAILY_MISSION_NOT_FOUND",
  "message": "데일리 미션 정보를 찾을 수 없습니다."
}
```

Path 값이 올바르지 않은 경우의 400, 인증 실패에 대한 401과 서버 내부 오류에 대한 500은 공통 오류 정책을 따른다.


## 미션 보상 수령
- http 메서드: post
- domain: mission
- endpoint: /api/v1/users/me/missions/{missionId}/rewards

### API 설명

사용자가 완료한 데일리 미션 또는 이벤트 미션의 보상을 수령할 때 호출한다.

미션 보상을 현재 사용자의 활성 마지막 접근 큐브 소유권에 지급한다. 친밀도 포인트 보상으로 레벨이 상승하면 새롭게 도달한 레벨의 보상도 함께 지급하고 최종 레벨 정보를 반환한다.

---

### 처리 정책

- 현재 사용자의 `ownership_status = ACTIVE`이고 `is_last_accessed = true`인 큐브 소유권을 지급 대상으로 사용한다.
- `missionId`와 요청 Body의 `missionType`이 모두 일치하고 활성 상태이며 삭제되지 않은 미션만 조회한다.
- 미션과 연결된 보상 아이템이 존재하고 삭제되지 않은 경우에만 지급한다.
- 현재 큐브 소유권에 해당 미션의 진행 정보가 존재하고 상태가 `COMPLETED` 또는 `REWARDED`인 경우에만 지급한다.
- `IN_PROGRESS` 상태이거나 진행 정보가 없으면 `409 MISSION_NOT_COMPLETED`를 반환한다.
- 중복 지급 여부는 검사하지 않으므로 이미 `REWARDED`인 미션을 다시 요청해도 보상을 다시 지급한다.
- 미션 보상은 보상 유형과 관계없이 `user_reward`에 추가한다.
- 보상 유형이 `AFFINITY_POINT`이면 `rewardCount`를 누적 친밀도 포인트에 더하고 레벨 상승 여부를 계산한다.
- 여러 레벨 기준을 한 번에 통과하면 새롭게 도달한 모든 레벨의 보상을 지급하고, 응답에는 최종 도달 레벨만 반환한다.
- 포인트가 아닌 보상은 `user_reward`에만 추가하며 친밀도 포인트와 레벨을 변경하지 않는다.
- 지급 후 미션 진행 상태를 `REWARDED`, `reward_claimed`를 `true`로 변경하고 `claimed_at`에 수령 시각을 저장한다.
- 미션 보상, 친밀도 변경, 레벨 보상과 미션 진행 상태 변경은 하나의 DB 트랜잭션으로 처리한다.

---

### 요청 Query

없음

---

### 요청 Path

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `missionId` | number | O | 보상을 수령할 미션 id. 1 이상의 정수 |

요청 예시: /api/v1/users/me/missions/4/rewards

---

### 요청 Body

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `missionType` | string | O | 미션 유형: DAILY \| EVENT |

```json
{
  "missionType": "DAILY"
}
```

---

### 정상 응답 데이터

Status Code : 200

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `levelUp` | object \| null | 이번 보상 수령으로 레벨이 상승한 경우의 최종 레벨. 레벨이 상승하지 않으면 `null` |
| `levelUp.level` | number | 최종 도달 레벨 숫자 |
| `levelUp.levelName` | string | 최종 도달 레벨 이름 |

친밀도 포인트 보상으로 레벨이 상승한 경우

```json
{
  "levelUp": {
    "level": 2,
    "levelName": "Friend"
  }
}
```

친밀도 포인트를 받았지만 레벨이 상승하지 않았거나 포인트가 아닌 보상을 받은 경우

```json
{
  "levelUp": null
}
```

---

### 오류 응답 데이터

Status Code : 404

현재 사용자의 활성 마지막 접근 큐브 소유권을 찾을 수 없는 경우

```json
{
  "code": "CUBE_OWNERSHIP_NOT_FOUND",
  "message": "큐브 소유권 정보를 찾을 수 없습니다."
}
```

요청한 id와 유형에 해당하는 활성 미션이 없거나 연결된 보상 아이템이 유효하지 않은 경우

```json
{
  "code": "MISSION_NOT_FOUND",
  "message": "미션 정보를 찾을 수 없습니다."
}
```

현재 큐브 소유권의 친밀도 정보를 찾을 수 없는 경우

```json
{
  "code": "CUBE_AFFINITY_NOT_FOUND",
  "message": "큐브 친밀도 정보를 찾을 수 없습니다."
}
```

Status Code : 409

현재 큐브 소유권에서 미션을 아직 완료하지 않은 경우

```json
{
  "code": "MISSION_NOT_COMPLETED",
  "message": "완료되지 않은 미션입니다."
}
```

Path 또는 Body 값이 올바르지 않은 경우의 400, 인증 실패에 대한 401과 서버 내부 오류에 대한 500은 공통 오류 정책을 따른다.
