## 아바타 소환 세션 생성
- http 메서드: post
- 엔드포인트: api/v1/users/me/avatar-interaction-sessions

### API 설명

사용자가 아바타 소환 버튼을 누르면 호출된다.

해당 소환 세션을 만들고 세션 id를 반환한다.

---

### 요청 Query

---

### 요청 Path

---

### 요청 Body

---

### 정상 응답 데이터

Status Code : 201

```json
{
  "avatarInteractionSession": {
    "id": 1101
  }
}
```

---

### 오류 응답 데이터




## 예절샷 프레임 조회
- http 메서드: get
- 엔드포인트: api/v1/users/me/album/yezul-frames

### API 설명

아바타 소환 중에 예절샷 프레임을 선택할때 호출된다.

예절샷 프레임 이미지의 URL을 전부 반환한다.

- `album_image.image_type = YEZUL_FRAME`인 항목만 반환한다.
- `id` 오름차순으로 반환한다.
- 페이지네이션 없이 전체 반환한다.
- `title`은 null일 수 있다.
- 조회 결과가 없으면 빈 배열을 반환한다.

---

### 요청 Query

---

### 요청 Path

---

### 요청 Body

---

### 정상 응답 데이터

Status Code : 200

```json
{
  "yezulFrames": [
    {
      "id": 31,
      "title": "미니멀",
      "imageUrl": "https://cdn.example.com/frames/YEZUL_FRAME_01.png"
    },
    {
      "id": 32,
      "title": "필름 카메라",
      "imageUrl": "https://cdn.example.com/frames/YEZUL_FRAME_02.png"
    }
  ]
}
```

```json
{
  "yezulFrames": []
}
```

---

### 오류 응답 데이터




## 아바타 소환 세션 상태 저장
- http 메서드: patch
- 엔드포인트: api/v1/users/me/avatar-interaction-sessions/{avatarInteractionSessionId}

### API 설명

사용자가 아바타 AR 소환 세션을 종료하면 호출된다.

세션 상태를 completed로 db에 업데이트 한다.

- 요청 Body 없이 호출한다.
- 호출 시 `status`는 `COMPLETED`로 저장한다.
- `ended_at`은 서버가 저장하는 현재 한국 시간 기준 시각으로 저장한다.
- `status = COMPLETED`이거나 `ended_at`이 null이 아닌 세션은 이미 종료된 세션으로 처리한다.

---

### 요청 Query

---

### 요청 Path

```json
{
	"avatarInteractionSessionId": 1101
}
```

요청 예시: api/v1/users/me/avatar-interaction-sessions/1101

---

### 요청 Body

---

### 정상 응답 데이터

Status Code : 204

응답 Body 없음

---

### 오류 응답 데이터

Status Code: 404

```json
{
  "code": "AVATAR_INTERACTION_SESSION_NOT_FOUND",
  "message": "아바타 소환 세션을 찾을 수 없습니다."
}
```

Status Code : 409

```json
{
  "code": "AVATAR_INTERACTION_SESSION_ALREADY_COMPLETED",
  "message": "이미 종료된 아바타 소환 세션입니다."
}
```




## 아바타 소환 캡처 저장
- http 메서드: post
- 엔드포인트: api/v1/users/me/avatar-interaction-sessions/{avatarInteractionSessionId}/pictures

### API 설명

사용자가 아바타 소환 중 촬영한 사진을 Gallery에 저장할 때 호출한다.

프론트가 이미지 파일과 이미지 생성 시간을 보내주면 해당 이미지를 서버에 올리고 관련 정보를 저장한다.

- 아바타 소환 세션 상태는 검사하지 않는다.
- 이미지 URL은 `avatar_interaction_picture.picture_img_url`에 저장한다.
- 촬영 시각은 `avatar_interaction_picture.pictured_at`에 저장한다.
- Blob 저장 경로는 `avatar_interaction_picture/{userId}/{avatarInteractionSessionId}/{UUID}.{확장자}` 형식을 사용한다.

---

### 요청 Query

---

### 요청 Path

```json
{
	"avatarInteractionSessionId": 1101
}
```

api/v1/users/me/avatar-interaction-sessions/1101/pictures

---

### 요청 Body

이미지 파일을 전송해야 하므로 JSON이 아니라 `multipart/form-data` 형식을 사용한다.

```json
image: <이미지 파일>
picturedAt: 2026-07-29T15:05:20
```

- `image`: 프론트 임시 저장소에 있는 실제 이미지 파일
    - **허용 확장자:** `.jpg/.jpeg`, `.png`, `.webp` (GIF 불가)
    - MIME 타입은 `image/jpeg`, `image/jpg`, `image/png`, `image/webp`를 허용하며 대소문자는 구분하지 않는다.
    - 허용하지 않는 파일은 공통 `400 INVALID_REQUEST`
    반환
- `picturedAt`: 실제 이미지를 촬영한 시각
    - 한국시간 기준 offset 없는 문자열로 보내줘야 한다.

`picturedAt`은 Gallery 저장 버튼을 누른 시각이 아니라 원래 사진을 촬영한 시각이다.

---

### 정상 응답 데이터

Status Code : 204

응답 Body 없음

---

### 오류 응답 데이터

Status Code : 404

```json
{
  "code": "AVATAR_INTERACTION_SESSION_NOT_FOUND",
  "message": "아바타 소환 세션을 찾을 수 없습니다."
}
```
