## 트랙 재생 세션 생성
- http 메서드: POST
- 엔드포인트: `/api/v1/tracks/{trackId}/sessions`
- 도메인: track

### API 설명

사용자가 트랙 재생을 하면 호출된다. 

일반 재생인지 특별 재생인지 `playMode`로 전달받고, 백엔드는 해당 트랙 재생 세션을 생성한다.

---

### 처리 정책

- 로그인 구현 전에는 현재 사용자를 항상 id=1로 간주한다.
- `trackId`에 해당하는 트랙이 존재하는 경우에만 세션을 생성한다.
- 트랙이 존재하지 않으면 404: TRACK_NOT_FOUND를 반환한다.
- 현재 사용자의 큐브 소유권 중 `ownership_status = ACTIVE`이고 `is_last_accessed = true`인 소유권을 기준으로 세션을 생성한다.
- 조건에 맞는 큐브 소유권이 없으면 404: CUBE_OWNERSHIP_NOT_FOUND를 반환한다.
- 생성되는 세션의 `started_at`은 서버의 현재 한국시간 기준 offset 없는 datetime으로 저장한다.
- 생성되는 세션의 `last_position_seconds`와 `viewed_seconds`는 0으로 저장한다.
- 생성되는 세션의 `status`는 `PLAYING`으로 저장한다.
- `play_mode`는 요청 Body의 `playMode` 값을 그대로 저장한다.

---

### 요청 Query

없음

---

### 요청 Path

| 필드 | 타입 | 필수 | 설명 |
|---|---:|:---:|---|
| `trackId` | number | O | 재생 세션을 생성할 트랙 id |

요청 예시: /api/v1/tracks/35/sessions

---

### 요청 Body

| 필드 | 타입 | 필수 | 설명 |
|---|---:|:---:|---|
| `playMode` | string | O | 트랙 재생 모드. `NORMAL`, `SPECIAL` 중 하나 |

```json
{
  "playMode": "NORMAL"
}
```

```json
{
  "playMode": "SPECIAL"
}
```

---

### 정상 응답 데이터
Status Code : 201

| 필드 | 타입 | 설명 |
|---|---:|---|
| `trackSession.id` | number | 생성된 트랙 재생 세션 id |
| `trackSession.playMode` | string | 생성된 세션의 재생 모드 |

```json
{
  "trackSession": {
    "id": 601,
    "playMode": "NORMAL"
  }
}
```

---

### 오류 응답 데이터
Status Code : 404

트랙이 존재하지 않는 경우

```json
{
  "code": "TRACK_NOT_FOUND",
  "message": "앨범 트랙을 찾을 수 없습니다."
}
```

현재 사용자의 마지막 접근 ACTIVE 큐브 소유권이 존재하지 않는 경우

```json
{
  "code": "CUBE_OWNERSHIP_NOT_FOUND",
  "message": "큐브 소유권을 찾을 수 없습니다."
}
```




## 트랙 재생 세션 상태 저장
- http 메서드: PATCH
- 엔드포인트: `/api/v1/users/me/track-sessions/{trackSessionId}`
- 도메인: track

### API 설명

재생이 완료되거나, 뒤로 가기 혹은 특별 재생으로 전환되어 세션 상태가 변할 때 호출한다.

재생 중인 `TRACK_SESSION`의 최종 재생 위치, 실제 감상 시간과 종료 상태를 저장한다.

---

### 처리 정책

- 로그인 구현 전에는 현재 사용자를 항상 id=1로 간주한다.
- `trackSessionId`에 해당하는 트랙 재생 세션이 현재 사용자의 큐브 소유권에 속한 경우에만 저장할 수 있다.
- 세션이 존재하지 않거나 현재 사용자의 세션이 아니면 404: TRACK_SESSION_NOT_FOUND를 반환한다.
- `status = PLAYING`인 세션만 저장할 수 있다.
- 이미 `COMPLETED` 또는 `CANCELLED`로 종료된 세션이면 409: TRACK_SESSION_ALREADY_ENDED를 반환한다.
- 요청 Body의 `status` 값은 `COMPLETED`, `CANCELLED` 중 하나다.
- 사용자가 트랙 감상 중 뒤로 가면 `CANCELLED`로 저장한다.
- 트랙이 끝까지 재생되면 `COMPLETED`로 저장한다.
- 특별 재생 전환 시 이 API로 기존 `NORMAL` 세션을 `CANCELLED` 처리한 후, 프론트가 세션 생성 API를 다시 호출해 새로운 `SPECIAL` 세션을 만든다.
- `lastPositionSeconds`는 트랙을 종료한 시점의 재생 위치로 저장한다.
- `viewedSeconds`는 사용자가 실제로 감상한 누적 시간으로 저장한다.
- `lastPositionSeconds`, `viewedSeconds`의 숫자 범위와 트랙 길이는 검증하지 않고 필수값 누락 여부만 확인한다.
- API 호출이 성공하면 `ended_at`을 서버의 현재 한국시간 기준 offset 없는 datetime으로 저장한다.

---

### 요청 Query

없음

---

### 요청 Path

| 필드 | 타입 | 필수 | 설명 |
|---|---:|:---:|---|
| `trackSessionId` | number | O | 저장할 트랙 재생 세션 id |

요청 예시: /api/v1/users/me/track-sessions/36

---

### 요청 Body

| 필드 | 타입 | 필수 | 설명 |
|---|---:|:---:|---|
| `status` | string | O | 세션 종료 상태. `COMPLETED`, `CANCELLED` 중 하나 |
| `lastPositionSeconds` | number | O | 트랙을 종료한 시점의 재생 위치 |
| `viewedSeconds` | number | O | 사용자가 실제로 감상한 누적 시간 |

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
  "lastPositionSeconds": 179,
  "viewedSeconds": 179
}
```

---

### 정상 응답 데이터
Status Code : 204

응답 Body 없음

---

### 오류 응답 데이터
Status Code : 404

세션이 존재하지 않거나 현재 사용자의 세션이 아닌 경우

```json
{
  "code": "TRACK_SESSION_NOT_FOUND",
  "message": "트랙 재생 세션을 찾을 수 없습니다."
}
```

Status Code : 409

이미 종료된 트랙 재생 세션인 경우

```json
{
  "code": "TRACK_SESSION_ALREADY_ENDED",
  "message": "이미 종료된 트랙 재생 세션입니다."
}
```




## 트랙 재생 캡처 저장
- http 메서드: POST
- 엔드포인트: `/api/v1/users/me/track-sessions/{trackSessionId}/captures`
- 도메인: track

### API 설명

트랙 특별 재생이 끝난 후 프론트가 임시 캡처 이미지로 감상 완료 화면을 표시한다.

사용자가 특정 사진의 `Gallery에 저장하기`를 누르면 이 API를 호출한다.

백엔드는 이미지를 Azure Blob Storage에 저장하고 공개 이미지 URL을 DB에 저장한다.

---

### 처리 정책

- 로그인 구현 전에는 현재 사용자를 항상 id=1로 간주한다.
- `trackSessionId`에 해당하는 트랙 재생 세션이 현재 사용자의 큐브 소유권에 속한 경우에만 캡처를 저장할 수 있다.
- 세션이 존재하지 않거나 현재 사용자의 세션이 아니면 404: TRACK_SESSION_NOT_FOUND를 반환한다.
- 파일 크기, 촬영 위치 값, 세션 상태, 재생 모드는 별도로 검증하지 않는다.
- 동일한 사진을 여러 번 요청하면 각각 새로운 캡처로 저장한다.
- 이미지 파일은 JPEG, PNG, WebP만 허용한다.
- 지원하지 않는 이미지 형식이면 400: INVALID_REQUEST를 반환한다.
- `capturedPositionSeconds`는 이미지를 촬영했을 때의 트랙 재생 위치로 저장한다.
- `capturedAt`은 실제 이미지를 촬영한 시각으로 저장한다.
- `capturedAt`은 한국시간 기준 offset 없는 ISO 8601 형식으로 전달한다.
- Azure 저장 경로: `track_capture/{userId}/{trackSessionId}/{UUID}.확장자`
- Azure Blob Storage에 저장된 이미지 URL을 `track_capture.track_capture_img_url`에 저장한다.

---

### 요청 Query

없음

---

### 요청 Path

| 필드 | 타입 | 필수 | 설명 |
|---|---:|:---:|---|
| `trackSessionId` | number | O | 캡처를 저장할 트랙 재생 세션 id |

요청 예시: /api/v1/users/me/track-sessions/40/captures

---

### 요청 Body

이미지 파일을 전송해야 하므로 JSON이 아니라 `multipart/form-data` 형식을 사용한다.

| 필드 | 타입 | 필수 | 설명 |
|---|---:|:---:|---|
| `image` | file | O | 저장할 캡처 이미지 파일 |
| `capturedPositionSeconds` | number | O | 이미지를 촬영했을 때의 트랙 재생 위치 |
| `capturedAt` | string(date-time) | O | 실제 이미지를 촬영한 시각 |

```text
image: <이미지 파일>
capturedPositionSeconds: 74
capturedAt: 2026-07-29T15:05:20
```

- `image`: 프론트 임시 저장소에 있는 실제 이미지 파일
  - 허용 형식: JPEG(`.jpg`, `.jpeg`), PNG, WebP (GIF 불가)
  - MIME 타입은 `image/jpeg`, `image/jpg`, `image/png`, `image/webp`를 허용하며 대소문자는 구분하지 않는다.
  - 허용하지 않는 파일은 400: INVALID_REQUEST를 반환한다.
- `capturedPositionSeconds`: 이미지를 촬영했을 때의 트랙 재생 위치
- `capturedAt`: 실제 이미지를 촬영한 시각
  - 한국시간 기준 offset 없는 문자열로 보내줘야 한다.

`capturedAt`은 Gallery 저장 버튼을 누른 시각이 아니라 원래 사진을 촬영한 시각이다.

---

### 정상 응답 데이터
Status Code : 204

응답 Body 없음

---

### 오류 응답 데이터
Status Code : 400

필수 multipart 필드가 없거나 JPEG, PNG, WebP 이외의 파일 형식이면 반환한다.

```json
{
  "code": "INVALID_REQUEST",
  "message": "요청값이 올바르지 않습니다."
}
```


Status Code : 404

세션이 존재하지 않거나 현재 사용자의 세션이 아닌 경우

```json
{
  "code": "TRACK_SESSION_NOT_FOUND",
  "message": "트랙 재생 세션을 찾을 수 없습니다."
}
```
