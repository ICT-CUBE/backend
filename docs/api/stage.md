## 스테이지 재생 세션 생성
- http 메서드: post
- 엔드포인트: api/v1/stages/{stageId}/sessions

### API 설명

사용자가 스테이지 영상 조회를 한 후 플레이를 시작하면 호출한다.

프론트는 일반 관람 모드인지 ar 모드인지 전달을 하고 db에는 하나의 재생 세션이 생성됨.

---

### 요청 Query

---

### 요청 Path

요청 예시: api/v1/stages/23/sessions

---

### 요청 Body

```json
{
	"viewMode": "NORMAL"
}
```

```json
{
	"viewMode": "AR"
}
```

- viewMode는 반드시 반환해야 함.

---

### 정상 응답 데이터

Status Code : 201

```json
{
  "stageSession": {
    "id": 501,
    "viewMode": "AR"
  }
}
```

---

### 오류 응답 데이터

Status Code : 404

```json
{
  "code": "STAGE_NOT_FOUND",
  "message": "스테이지 영상을 찾을 수 없습니다."
}
```

```json
{
  "code": "CUBE_OWNERSHIP_NOT_FOUND",
  "message": "큐브 소유권 정보를 찾을 수 없습니다."
}
```

Status Code : 409

```json
{
  "code": "STAGE_SESSION_ALREADY_PLAYING",
  "message": "이미 재생 중인 스테이지 세션이 있습니다."
}
```






## 스테이지 재생 세션 저장
- http 메서드: patch
- 엔드포인트: api/v1/users/me/stage-sessions/{stageSessionId}

### API 설명

사용자가 스테이지 영상 재생을 하다가 영상이 끝나거나, 뒤로 가기 혹은 AR 모드로 전환을 하여 영상이 중간에 취소되면 세션 정보를 갱신해 저장하기 위해 호출된다.

재생 중인 `STAGE_SESSION`의 최종 재생 위치, 실제 시청 시간과 종료 상태를 저장한다.

- 사용자가 영상을 시청하다가 나감 → `CANCELLED`
- 영상이 끝까지 재생됨 → `COMPLETED`
- 일반 모드에서 AR 모드로 변경함 → 기존 일반 세션을 `CANCELLED`
- AR 모드에서 일반 모드로 변경함 → 기존 AR 세션을 `CANCELLED`

---

### 요청 Query

---

### 요청 Path

요청 예시: api/v1/users/me/stage-sessions/501

---

### 요청 Body

```json
{
	"status": "CANCELLED",
	"lastPositionSeconds": 74,
	"viewedSeconds": 62
}
```

```json
{
  "status": "COMPLETED",
  "lastPositionSeconds": 222,
  "viewedSeconds": 222
}
```

- `lastPositionSeconds`: 영상을 종료한 시점의 재생 위치
- `viewedSeconds`: 사용자가 실제로 시청한 누적 시간

---

### 정상 응답 데이터

Status Code : 204

---

### 오류 응답 데이터

Status Code : 404

```json
{
  "code": "STAGE_SESSION_NOT_FOUND",
  "message": "스테이지 재생 세션을 찾을 수 없습니다."
}
```

Status Code : 409

```json
{
  "code": "STAGE_SESSION_ALREADY_ENDED",
  "message": "이미 종료된 스테이지 재생 세션입니다."
}
```