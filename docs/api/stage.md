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
- 두 숫자의 범위와 영상 길이는 검증하지 않고 필수값 누락 여부만 확인한다.

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




## 스테이지 캡쳐 저장
- http 메서드: post
- 엔드포인트: api/v1/users/me/stage-sessions/{stageSessionId}/captures

### API 설명

AR 관람 리포트에서 사용자가 특정 사진의 `Gallery에 저장하기`를 누르면 호출한다.

프론트가 임시 저장하고 있던 이미지 파일을 백엔드로 전송하면 백엔드는 해당 이미지를 Azure Blob Storage에 저장하고 Azure Blob URL을 DB에 저장한다.

- 파일 크기, 촬영 위치 값, 세션 상태, 관람 모드는 별도로 검증하지 않는다.
- 동일한 사진을 여러 번 요청하면 각각 새로운 캡처로 저장한다.
- Azure 저장 경로: `stage_capture/{userId}/{stageSessionId}/{UUID}.확장자`

---

### 요청 Query

---

### 요청 Path

요청 예시: api/v1/users/me/stage-sessions/501/captures

---

### 요청 Body

이미지 파일을 전송해야 하므로 JSON이 아니라 `multipart/form-data` 형식을 사용한다.

```json
image: <이미지 파일>
capturedPositionSeconds: 74
capturedAt: 2026-07-29T15:05:20+09:00
```

- `image`: 프론트 임시 저장소에 있는 실제 이미지 파일
    - **허용 형식:** JPEG(`.jpg`, `.jpeg`), PNG, WebP (GIF 불가)
    - MIME 타입은 `image/jpeg`, `image/jpg`, `image/png`, `image/webp`를 허용하며 대소문자는 구분하지 않는다.
    - 허용하지 않는 파일은 공통 `400 INVALID_REQUEST`
    반환
- `capturedPositionSeconds`: 이미지를 촬영했을 때의 영상 재생 위치
- `capturedAt`: 실제 이미지를 촬영한 시각
    - KST 오프셋(+09:00) 포함 문자열로 보내줘야 한다. (한국 시간 사용)

`capturedAt`은 Gallery 저장 버튼을 누른 시각이 아니라 원래 사진을 촬영한 시각이다.

---

### 정상 응답 데이터

Status Code : 204

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

```json
{
  "code": "STAGE_SESSION_NOT_FOUND",
  "message": "스테이지 재생 세션을 찾을 수 없습니다."
}
```
