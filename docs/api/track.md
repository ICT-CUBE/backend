## 트랙 재생 세션 생성
- http 메서드: post
- 엔드포인트: api/v1/tracks/{trackId}/sessions

### API 설명

사용자가 트랙 재생을 하면 호출된다. 

일반 재생인지 특별 재생인지 `playMode`로 전달받고 db에 해당 트랙 재생 세션을 생성 및 저장한다.

---

### 요청 Query

---

### 요청 Path

요청 예시: api/v1/tracks/35/sessions

---

### 요청 Body

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

```json
{
  "code": "TRACK_NOT_FOUND",
  "message": "앨범 트랙을 찾을 수 없습니다."
}
```

```json
{
  "code": "CUBE_OWNERSHIP_NOT_FOUND",
  "message": "큐브 소유권을 찾을 수 없습니다."
}
```

Status Code : 409

같은 큐브 소유권과 같은 트랙에 이미 `PLAYING` 상태인 세션이 있으면 반환한다.
다른 트랙의 `PLAYING` 세션은 검사하지 않는다.

```json
{
  "code": "TRACK_SESSION_ALREADY_PLAYING",
  "message": "이미 재생 중인 트랙 세션이 있습니다."
}
```




## 트랙 재생 세션 상태 저장
- http 메서드: patch
- 엔드포인트: api/v1/users/me/track-sessions/{trackSessionId}

### API 설명

재생이 완료되거나, 뒤로 가기 혹은 특별 재생을 하게 되서 세션 상태가 변화할때 호출된다. 스테이지 세션과 마찬가지로 ar 특별 재생을 하는 경우에는 현재 일반 재생 세션을 취소하고 새로운 새션을 생성해야한다.

재생 중인 `TRACK_SESSION`의 최종 재생 위치, 실제 감상 시간과 종료 상태를 저장한다.

- 숫자 범위와 트랙 길이는 검증하지 않고 필수값 누락 여부만 확인한다.
- 특별 재생 전환 시 이 API로 기존 `NORMAL` 세션을 `CANCELLED` 처리한 후, 프론트가 세션 생성 API를 다시 호출해 새로운 `SPECIAL` 세션을 만든다.
- 이 API에서는 새 세션, 미션, 친밀도 정보를 생성하거나 변경하지 않는다.

---

### 요청 Query

---

### 요청 Path

요청 예시: api/v1/users/me/track-sessions/36

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
  "lastPositionSeconds": 179,
  "viewedSeconds": 179
}
```

---

### 정상 응답 데이터

Status Code : 204

---

### 오류 응답 데이터

Status Code : 404

```json
{
  "code": "TRACK_SESSION_NOT_FOUND",
  "message": "트랙 재생 세션을 찾을 수 없습니다."
}
```

Status Code : 409

```json
{
  "code": "TRACK_SESSION_ALREADY_ENDED",
  "message": "이미 종료된 트랙 재생 세션입니다."
}
```




## 트랙 재생 캡처 저장
- http 메서드: post
- 엔드포인트: api/v1/users/me/track-sessions/{trackSessionId}/captures

### API 설명

트랙 특별 재생이 끝난 후 프론트가 임시 캡처 이미지로 감상 완료 화면을 표시한다.

사용자가 특정 사진의 `Gallery에 저장하기`를 누르면 이 API를 호출한다.

백엔드는 이미지를 Azure Blob Storage에 저장하고 공개 이미지 URL을 DB에 저장한다.

- 파일 크기, 촬영 위치 값, 세션 상태, 재생 모드는 별도로 검증하지 않는다.
- 동일한 사진을 여러 번 요청하면 각각 새로운 캡처로 저장한다.
- Azure 저장 경로: `track_capture/{userId}/{trackSessionId}/{UUID}.확장자`

---

### 요청 Query

---

### 요청 Path

요청 예시: api/v1/users/me/track-sessions/40/captures

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
  "code": "TRACK_SESSION_NOT_FOUND",
  "message": "트랙 재생 세션을 찾을 수 없습니다."
}
```
