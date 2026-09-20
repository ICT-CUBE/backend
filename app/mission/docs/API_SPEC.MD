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
