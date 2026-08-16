## 홈 정보 조회
- http 메서드: GET
- 엔드포인트: `/api/v1/users/me/home`
- 도메인: home

### API 설명

서비스 메인 홈 화면에서 호출한다.

홈 화면에 필요한 사용자, 큐브 소유권, 큐브, 친밀도 정보를 반환한다.

---

### 처리 정책

- 로그인 구현 전에는 현재 사용자를 항상 id=1로 간주한다.
- 현재 사용자의 큐브 소유권 정보를 조회한다.
- `ownership_status = ACTIVE`인 큐브 소유권을 우선 조회한다.
- ACTIVE 소유권이 없으면 최근 접근 소유권과 최근 획득 소유권을 기준으로 소유권을 조회한다.
- 큐브 소유권이 아예 존재하지 않으면 404: CUBE_OWNERSHIP_NOT_FOUND를 반환한다.
- 큐브 소유권은 존재하지만 `ownership_status = ACTIVE`가 아니면 403: CUBE_OWNERSHIP_FORBIDDEN을 반환한다.
- ACTIVE 큐브 소유권에 연결된 친밀도 정보가 없으면 404: CUBE_AFFINITY_NOT_FOUND를 반환한다.
- 친밀도 레벨 이름은 DB에 저장된 enum 값을 그대로 반환한다. 예: `Intro`, `Friend`, `Close`, `Special`
- 날짜/시간 값은 한국시간 기준 offset 없는 ISO 8601 형식으로 반환한다.

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
|---|---:|---|
| `user.id` | number | 현재 사용자 id |
| `user.profileCharacterImgUrl` | string \| null | 사용자 프로필 캐릭터 이미지 URL |
| `cubeOwnership.id` | number | 큐브 소유권 id |
| `cubeOwnership.avatarNickname` | string \| null | 사용자가 설정한 아바타 닉네임 |
| `cubeOwnership.acquiredAt` | string(date-time) | 큐브 획득 시각 |
| `cube.id` | number | 큐브 id |
| `cube.artistName` | string | 아티스트 이름 |
| `affinity.id` | number | 친밀도 id |
| `affinity.currentXp` | number | 현재 친밀도 XP |
| `affinity.level.id` | number | 친밀도 레벨 id |
| `affinity.level.level` | number | 현재 친밀도 레벨 숫자 |
| `affinity.level.levelName` | string | DB enum 기준 친밀도 레벨 이름 |
| `affinity.level.levelXp` | number | 현재 레벨을 완료하는 데 필요한 최대 XP |

```json
{
  "user": {
    "id": 1,
    "profileCharacterImgUrl": "https://example.com/profile.png"
  },
  "cubeOwnership": {
    "id": 12,
    "avatarNickname": "제니",
    "acquiredAt": "2026-03-19T10:30:00"
  },
  "cube": {
    "id": 15,
    "artistName": "JENNIE"
  },
  "affinity": {
    "id": 7,
    "currentXp": 1245,
    "level": {
      "id": 3,
      "level": 3,
      "levelName": "Close",
      "levelXp": 2000
    }
  }
}
```

---

### 오류 응답 데이터
Status Code : 404

큐브 소유권 정보가 존재하지 않는 경우

```json
{
  "code": "CUBE_OWNERSHIP_NOT_FOUND",
  "message": "큐브 소유권 정보를 찾을 수 없습니다."
}
```

큐브 친밀도 정보가 존재하지 않는 경우

```json
{
  "code": "CUBE_AFFINITY_NOT_FOUND",
  "message": "큐브 친밀도 정보를 찾을 수 없습니다."
}
```

Status Code : 403

큐브 소유권은 존재하지만 ACTIVE 상태가 아닌 경우

```json
{
  "code": "CUBE_OWNERSHIP_FORBIDDEN",
  "message": "해당 큐브 소유권 정보를 조회할 권한이 없습니다."
}
```
