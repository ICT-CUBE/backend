## 친밀도 상세 조회
- http 메서드: get
- domain: affinity
- endpoint: api/v1/users/me/affinity

### API 설명

사용자가 친밀도 현황 화면에 진입하면 호출한다.

현재 친밀도 진행 상황, 레벨 보상, 오늘의 친밀도 활동과 전체 레벨 정보를 반환한다.

---

### 처리 정책

- 현재 사용자의 `ownership_status = ACTIVE`이고 `is_last_accessed = true`인 큐브 소유권을 기준으로 조회한다.
- 조건을 충족하는 큐브 소유권이 없으면 404: CUBE_OWNERSHIP_NOT_FOUND를 반환한다.
- 해당 큐브 소유권에 연결된 친밀도 정보가 없으면 404: CUBE_AFFINITY_NOT_FOUND를 반환한다.
- 현재 레벨은 `affinity.level_id`로 연결된 `level` 정보를 사용한다.
- `currentXp`는 누적 친밀도 포인트이며, 다음 레벨의 `level_xp`를 진행도 목표값으로 사용한다.
- `progressPercent`는 `currentXp / nextLevel.requiredXp * 100`의 소수점 이하를 버린 정수이며 최대 100으로 제한한다.
- `remainingXp`는 다음 레벨의 필요 XP에서 현재 XP를 뺀 값이며 최소 0으로 제한한다.
- 최고 레벨인 경우 `nextLevel`은 `null`, `progressPercent`는 100, `remainingXp`는 0으로 반환한다.
- 현재 레벨 보상은 현재 사용자가 실제 획득한 `user_reward` 중 `reward_item.reward_level`이 현재 레벨과 같은 항목만 반환한다.
- 다음 레벨 보상은 `reward_item.reward_level`이 다음 레벨과 같은 항목을 반환한다.
- `reward_level IS NULL`인 미션 보상은 레벨 보상 목록에 포함하지 않는다.
- 삭제된 보상 아이템은 제외하고 보상 아이템 id 오름차순으로 반환한다.
- 오늘의 활동은 현재 소유권에 적용되는 활성 `DAILY` 미션을 전체 반환한다.
- 미션 진행 정보가 없으면 `currentCount = 0`, `status = IN_PROGRESS`, `rewardClaimed = false`로 반환한다.
- 각 활동에는 프론트가 이동 동작을 결정할 수 있도록 `targetAction`을 포함한다.
- 전체 레벨은 레벨 숫자 오름차순으로 반환하고 현재 레벨을 기준으로 `COMPLETED`, `CURRENT`, `LOCKED` 상태를 계산한다.
- 레벨명과 보상 정보는 DB 값을 그대로 반환한다.

---

### 요청 Query

없음

---

### 요청 Path

없음

---

### 요청 Body

없음

---

### 정상 응답 데이터

Status Code : 200

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `affinity.id` | number | 친밀도 id |
| `affinity.currentXp` | number | 현재 누적 친밀도 포인트 |
| `affinity.progressPercent` | number | 다음 레벨까지의 진행률, 최고 레벨은 100 |
| `affinity.remainingXp` | number | 다음 레벨까지 필요한 친밀도 포인트 |
| `affinity.currentLevel.id` | number | 현재 레벨 id |
| `affinity.currentLevel.level` | number | 현재 레벨 숫자 |
| `affinity.currentLevel.levelName` | string | 현재 레벨명 |
| `affinity.currentLevel.requiredXp` | number | 현재 레벨 진입에 필요한 누적 XP |
| `affinity.currentLevel.rewards` | array | 현재 레벨에서 실제 획득한 보상 목록 |
| `affinity.nextLevel` | object | null | 다음 레벨과 해금 예정 보상, 최고 레벨이면 null |
| `dailyActivities` | array | 오늘 수행할 수 있는 친밀도 활동 목록 |
| `dailyActivities[].targetAction` | string | 활동 이동 및 수행 판별에 사용하는 동작 타입 |
| `dailyActivities[].reward` | object | 활동 완료 시 지급되는 보상 |
| `levels` | array | 전체 친밀도 레벨 목록 |
| `levels[].status` | string | `COMPLETED`, `CURRENT`, `LOCKED` 중 하나 |

보상 객체는 `id`, `name`, `rewardType`, `description`, `rewardCount`, `rewardLevel`을 포함한다.

```json
{
  "affinity": {
    "id": 1,
    "currentXp": 1245,
    "progressPercent": 62,
    "remainingXp": 755,
    "currentLevel": {
      "id": 3,
      "level": 3,
      "levelName": "Close",
      "requiredXp": 800,
      "rewards": [
        {
          "id": 8,
          "name": "일일 대화 가능 횟수",
          "rewardType": "CONVERSATION_COUNT",
          "description": "하루에 대화 제한 100회",
          "rewardCount": 100,
          "rewardLevel": 3
        },
        {
          "id": 12,
          "name": "멘트 종류",
          "rewardType": "COMMENT_TYPE",
          "description": "사적인 멘트와 비하인드 대화",
          "rewardCount": null,
          "rewardLevel": 3
        },
        {
          "id": 13,
          "name": "스페셜 음성",
          "rewardType": "SPECIAL_COMMENT",
          "description": "유행어 음성 해금 및 시즌 한정 음성 추가",
          "rewardCount": null,
          "rewardLevel": 3
        },
        {
          "id": 15,
          "name": "아바타 선대화",
          "rewardType": "AVATAR_FIRST_TALK",
          "description": "아바타 선대화 1일 1회",
          "rewardCount": 1,
          "rewardLevel": 3
        }
      ]
    },
    "nextLevel": {
      "id": 4,
      "level": 4,
      "levelName": "Special",
      "requiredXp": 2000,
      "rewards": [
        {
          "id": 9,
          "name": "일일 대화 가능 횟수",
          "rewardType": "CONVERSATION_COUNT",
          "description": "하루에 대화 제한 없음",
          "rewardCount": null,
          "rewardLevel": 4
        },
        {
          "id": 16,
          "name": "아바타 선대화",
          "rewardType": "AVATAR_FIRST_TALK",
          "description": "아바타 선대화 1일 5회",
          "rewardCount": 5,
          "rewardLevel": 4
        }
      ]
    }
  },
  "dailyActivities": [
    {
      "id": 1,
      "title": "홈 화면 방문하기",
      "description": "AR ZONE 접속",
      "targetAction": "HOME_VIEW",
      "currentCount": 1,
      "targetCount": 1,
      "status": "REWARDED",
      "rewardClaimed": true,
      "reward": {
        "id": 2,
        "name": "친밀도 포인트",
        "rewardType": "AFFINITY_POINT",
        "description": "친밀도 5포인트 제공",
        "rewardCount": 5,
        "rewardLevel": null
      }
    },
    {
      "id": 2,
      "title": "아바타와 대화하기",
      "description": "텍스트 또는 음성 대화",
      "targetAction": "CONVERSATION",
      "currentCount": 3,
      "targetCount": 3,
      "status": "COMPLETED",
      "rewardClaimed": false,
      "reward": {
        "id": 1,
        "name": "친밀도 포인트",
        "rewardType": "AFFINITY_POINT",
        "description": "친밀도 3포인트 제공",
        "rewardCount": 3,
        "rewardLevel": null
      }
    }
  ],
  "levels": [
    {
      "id": 1,
      "level": 1,
      "levelName": "Intro",
      "requiredXp": 0,
      "status": "COMPLETED"
    },
    {
      "id": 2,
      "level": 2,
      "levelName": "Friend",
      "requiredXp": 100,
      "status": "COMPLETED"
    },
    {
      "id": 3,
      "level": 3,
      "levelName": "Close",
      "requiredXp": 800,
      "status": "CURRENT"
    },
    {
      "id": 4,
      "level": 4,
      "levelName": "Special",
      "requiredXp": 2000,
      "status": "LOCKED"
    }
  ]
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

큐브 소유권에 연결된 친밀도 정보를 찾을 수 없는 경우

```json
{
  "code": "CUBE_AFFINITY_NOT_FOUND",
  "message": "큐브 친밀도 정보를 찾을 수 없습니다."
}
```