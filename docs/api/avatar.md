## 아바타 소환 세션 생성
- http 메서드: POST
- 엔드포인트: `/api/v1/users/me/avatar-interaction-sessions`
- 도메인: avatar

### API 설명

사용자가 아바타 소환 버튼을 누르면 호출한다.

현재 사용자의 활성 큐브 소유권을 기준으로 아바타 소환 세션을 생성하고, 생성된 세션 id를 반환한다.

---

### 처리 정책

- 현재 사용자의 `ACTIVE` 큐브 소유권 중 `is_last_accessed = true`인 소유권을 기준으로 세션을 생성한다.
- 이미 진행 중인 아바타 소환 세션이 있어도 새 세션을 생성할 수 있다.
- `avatar_interaction_session.cube_ownership_id`는 조회된 큐브 소유권 id로 저장한다.
- `avatar_interaction_session.started_at`은 서버의 현재 한국시간 기준 offset 없는 datetime으로 저장한다.
- `avatar_interaction_session.ended_at`은 `null`로 저장한다.
- `avatar_interaction_session.status`는 `ACTIVE`로 저장한다.
- 현재 사용자의 활성 큐브 소유권을 찾을 수 없으면 404: CUBE_OWNERSHIP_NOT_FOUND를 반환한다.

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

Status Code : 201

| 필드 | 타입 | 설명 |
|---|---:|---|
| `avatarInteractionSession.id` | number | 생성된 아바타 소환 세션 id |

```json
{
  "avatarInteractionSession": {
    "id": 1101
  }
}
```

---

### 오류 응답 데이터

Status Code : 404

현재 사용자의 활성 큐브 소유권을 찾을 수 없는 경우

```json
{
  "code": "CUBE_OWNERSHIP_NOT_FOUND",
  "message": "큐브 소유권 정보를 찾을 수 없습니다."
}
```




## 예절샷 프레임 조회
- http 메서드: GET
- 엔드포인트: `/api/v1/users/me/album/yezul-frames`
- 도메인: avatar

### API 설명

아바타 소환 중 사용자가 예절샷 프레임을 선택할 때 호출한다.

앨범 이미지 테이블에 저장된 예절샷 프레임 이미지를 전체 조회한다.

---

### 처리 정책

- `album_image.image_type = YEZUL_FRAME`인 항목만 반환한다.
- `id` 오름차순으로 반환한다.
- 페이지네이션 없이 전체 반환한다.
- `title`은 `null`일 수 있다.
- 조회 결과가 없으면 빈 배열을 반환한다.
- 별도의 사용자 소유권 검증은 하지 않는다.

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
| `yezulFrames[].id` | number | 예절샷 프레임 이미지 id |
| `yezulFrames[].title` | string \| null | 예절샷 프레임 제목 |
| `yezulFrames[].imageUrl` | string | 예절샷 프레임 이미지 URL |

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

없음




## 아바타 소환 세션 상태 저장
- http 메서드: PATCH
- 엔드포인트: `/api/v1/users/me/avatar-interaction-sessions/{avatarInteractionSessionId}`
- 도메인: avatar

### API 설명

사용자가 아바타 AR 소환 세션을 종료하면 호출한다.

아바타 소환 세션의 종료 시각과 상태를 저장한다.

---

### 처리 정책

- 현재 사용자의 `ACTIVE` 큐브 소유권에 속한 아바타 소환 세션만 상태를 저장할 수 있다.
- 요청 Body 없이 호출한다.
- 호출 시 `avatar_interaction_session.status`는 `COMPLETED`로 저장한다.
- `avatar_interaction_session.ended_at`은 서버의 현재 한국시간 기준 offset 없는 datetime으로 저장한다.
- `status = COMPLETED`이거나 `ended_at IS NOT NULL`인 세션은 이미 종료된 세션으로 처리한다.
- 아바타 소환 세션이 존재하지 않거나, 현재 사용자의 활성 큐브 소유권에 속하지 않으면 404: AVATAR_INTERACTION_SESSION_NOT_FOUND를 반환한다.
- 이미 종료된 세션이면 409: AVATAR_INTERACTION_SESSION_ALREADY_COMPLETED를 반환한다.

---

### 요청 Query

없음

---

### 요청 Path

| 필드 | 타입 | 필수 | 설명 |
|---|---:|:---:|---|
| `avatarInteractionSessionId` | number | O | 상태를 저장할 아바타 소환 세션 id |

```json
{
  "avatarInteractionSessionId": 1101
}
```

요청 예시: `/api/v1/users/me/avatar-interaction-sessions/1101`

---

### 요청 Body

없음

---

### 정상 응답 데이터

Status Code : 204

응답 Body 없음

---

### 오류 응답 데이터

Status Code : 404

아바타 소환 세션이 존재하지 않거나 현재 사용자의 활성 큐브 소유권에 속하지 않는 경우

```json
{
  "code": "AVATAR_INTERACTION_SESSION_NOT_FOUND",
  "message": "아바타 소환 세션을 찾을 수 없습니다."
}
```

Status Code : 409

이미 종료된 아바타 소환 세션인 경우

```json
{
  "code": "AVATAR_INTERACTION_SESSION_ALREADY_COMPLETED",
  "message": "이미 종료된 아바타 소환 세션입니다."
}
```




## 아바타 소환 캡처 저장
- http 메서드: POST
- 엔드포인트: `/api/v1/users/me/avatar-interaction-sessions/{avatarInteractionSessionId}/pictures`
- 도메인: avatar

### API 설명

아바타 소환 화면에서 사용자가 촬영한 사진을 Gallery에 저장할 때 호출한다.

프론트가 임시 저장하고 있던 이미지 파일을 백엔드로 전송하면 백엔드는 해당 이미지를 Azure Blob Storage에 저장하고 Azure Blob URL을 DB에 저장한다.

---

### 처리 정책

- 로그인 구현 전에는 현재 사용자를 항상 id=1로 간주한다.
- `avatarInteractionSessionId`에 해당하는 아바타 소환 세션이 현재 사용자의 `ACTIVE` 큐브 소유권에 속한 경우에만 캡처를 저장할 수 있다.
- 세션이 존재하지 않거나 현재 사용자의 세션이 아니면 404: AVATAR_INTERACTION_SESSION_NOT_FOUND를 반환한다.
- 아바타 소환 세션의 `status`, `ended_at`은 별도로 검증하지 않는다.
- 동일한 사진을 여러 번 요청하면 각각 새로운 캡처로 저장한다.
- 이미지 파일은 JPEG, PNG, WebP만 허용한다.
- 지원하지 않는 이미지 형식이면 400: INVALID_REQUEST를 반환한다.
- `picturedAt`은 실제 이미지를 촬영한 시각으로 저장한다.
- `picturedAt`은 한국시간 기준 offset 없는 ISO 8601 형식으로 전달한다.
- Azure 저장 경로: `avatar_interaction_picture/{userId}/{avatarInteractionSessionId}/{UUID}.확장자`
- Azure Blob Storage에 저장된 이미지 URL을 `avatar_interaction_picture.picture_img_url`에 저장한다.
- 촬영 시각은 `avatar_interaction_picture.pictured_at`에 저장한다.

---

### 요청 Query

없음

---

### 요청 Path

| 필드 | 타입 | 필수 | 설명 |
|---|---:|:---:|---|
| `avatarInteractionSessionId` | number | O | 캡처를 저장할 아바타 소환 세션 id |

요청 예시: `/api/v1/users/me/avatar-interaction-sessions/1101/pictures`

---

### 요청 Body

이미지 파일을 전송해야 하므로 JSON이 아니라 `multipart/form-data` 형식을 사용한다.

| 필드 | 타입 | 필수 | 설명 |
|---|---:|:---:|---|
| `image` | file | O | 저장할 캡처 이미지 파일 |
| `picturedAt` | string(date-time) | O | 실제 이미지를 촬영한 시각 |

```text
image: <이미지 파일>
picturedAt: 2026-07-29T15:05:20
```

- `image`: 프론트 임시 저장소에 있는 실제 이미지 파일
  - 허용 형식: JPEG(`.jpg`, `.jpeg`), PNG, WebP (GIF 불가)
  - MIME 타입은 `image/jpeg`, `image/jpg`, `image/png`, `image/webp`를 허용하며 대소문자는 구분하지 않는다.
  - 허용하지 않는 파일은 400: INVALID_REQUEST를 반환한다.
- `picturedAt`: 실제 이미지를 촬영한 시각
  - 한국시간 기준 offset 없는 문자열로 보내줘야 한다.

`picturedAt`은 Gallery 저장 버튼을 누른 시각이 아니라 원래 사진을 촬영한 시각이다.

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
  "code": "AVATAR_INTERACTION_SESSION_NOT_FOUND",
  "message": "아바타 소환 세션을 찾을 수 없습니다."
}
```
