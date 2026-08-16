## 갤러리 조회
- http 메서드: GET
- 엔드포인트: `/api/v1/users/me/gallery`
- 도메인: gallery

### API 설명

갤러리에 들어가면 호출된다.

앨범 관련 콘텐츠 이미지들과 사용자가 캡처한 이미지들을 반환한다.

사용자 캡처 이미지에는 스테이지 캡처, 트랙 특별 재생 캡처, 아바타 현실 소환 사진이 있다.

프론트가 전달한 `size` 값을 기준으로 페이징해서 반환한다.

---

### 처리 정책

- 로그인 구현 전에는 현재 사용자를 항상 id=1로 간주한다.
- `category`를 보내지 않으면 기본값은 `ALL`이다.
- `page`를 보내지 않으면 기본값은 0이다.
- `size`를 보내지 않으면 기본값은 20이다.
- `size`는 1 이상의 숫자를 허용한다.
- 삭제된 항목, 즉 `deleted_at`이 null이 아닌 사진은 반환하지 않는다.
- 캡처 이미지는 현재 사용자의 `ACTIVE` 큐브 소유권에 연결된 항목만 반환한다.
- 앨범 이미지는 사용자 소유권과 무관하게 전체 앨범 이미지를 반환한다.
- `ALL` 카테고리는 캡처 이미지, 앨범 이미지, 콘서트 스틸컷을 모두 반환한다.
- `CAPTURE` 카테고리는 스테이지 캡처, 트랙 캡처, 아바타 현실 소환 사진을 반환한다.
- `ALBUM` 카테고리는 `album_image.image_type = ALBUM_IMAGE`인 항목만 의미한다.
- `CONCERT_STILLCUT` 카테고리는 `album_image.image_type = CONCERT_STILLCUT`인 항목만 의미한다.
- `YEZUL_FRAME`은 갤러리 조회 응답에 포함하지 않는다.
- 스테이지 캡처와 트랙 캡처의 `displayDate`는 `captured_at` 기준이다.
- 아바타 현실 소환 사진의 `displayDate`는 `pictured_at` 기준이다.
- 앨범 이미지의 `displayDate`는 앨범 `release_date` 기준이다.
- `id`는 원본 테이블의 id를 그대로 반환하며, 프론트는 `sourceType`과 조합해 항목을 식별한다.
- Query 값이 잘못되면 400: INVALID_REQUEST를 반환한다.

---

### 요청 Query

| 필드 | 타입 | 필수 | 설명 |
|---|---:|:---:|---|
| `category` | string | X | 조회할 갤러리 카테고리. `ALL`, `CAPTURE`, `ALBUM`, `CONCERT_STILLCUT` 중 하나 |
| `page` | number | X | 조회할 페이지 번호. 0부터 시작 |
| `size` | number | X | 페이지 크기. 1 이상의 숫자 |

요청 예시: /api/v1/users/me/gallery?category=ALL&page=0&size=20

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
| `galleryItems[].id` | number | 원본 테이블의 항목 id |
| `galleryItems[].sourceType` | string | 이미지 출처 타입 |
| `galleryItems[].category` | string | 갤러리 카테고리 |
| `galleryItems[].imageUrl` | string | 이미지 URL |
| `galleryItems[].displayDate` | string(date) | 화면에 표시할 날짜 |
| `pagination.page` | number | 현재 페이지 번호 |
| `pagination.size` | number | 페이지 크기 |
| `pagination.hasNext` | boolean | 다음 페이지 존재 여부 |

```json
{
  "galleryItems": [
    {
      "id": 701,
      "sourceType": "STAGE_CAPTURE",
      "category": "CAPTURE",
      "imageUrl": "https://cdn.example.com/stage-captures/capture-701.jpg",
      "displayDate": "2026-06-24"
    },
    {
      "id": 801,
      "sourceType": "TRACK_CAPTURE",
      "category": "CAPTURE",
      "imageUrl": "https://cdn.example.com/track-captures/capture-801.jpg",
      "displayDate": "2026-06-24"
    },
    {
      "id": 901,
      "sourceType": "INTERACTION_CAPTURE",
      "category": "CAPTURE",
      "imageUrl": "https://cdn.example.com/avatar-interactions/picture-901.jpg",
      "displayDate": "2026-06-24"
    },
    {
      "id": 902,
      "sourceType": "ALBUM_IMAGE",
      "category": "CONCERT_STILLCUT",
      "imageUrl": "https://cdn.example.com/concert-stillcuts/born-pink-01.jpg",
      "displayDate": "2026-04-20"
    }
  ],
  "pagination": {
    "page": 0,
    "size": 20,
    "hasNext": true
  }
}
```

---

### 오류 응답 데이터
Status Code : 400

Query 값이 잘못된 경우

```json
{
  "code": "INVALID_REQUEST",
  "message": "요청값이 올바르지 않습니다."
}
```



## AR에서 다시 경험하기
- http 메서드: GET
- 엔드포인트: `/api/v1/users/me/gallery/{sourceType}/{galleryItemId}/ar-experience`
- 도메인: gallery

### API 설명

사용자가 갤러리 캡쳐 목록에서 특정 이미지를 클릭하고 AR에서 다시 경험하기를 누르면 호출된다.

해당 캡처의 원본 스테이지 또는 트랙 정보를 반환한다.

---

### 처리 정책

- 로그인 구현 전에는 현재 사용자를 항상 id=1로 간주한다.
- `sourceType`은 `STAGE_CAPTURE`, `TRACK_CAPTURE`만 허용한다.
- 현재 사용자의 `ACTIVE` 큐브 소유권에 속한 캡처만 조회할 수 있다.
- 삭제된 캡처(`deleted_at`이 null이 아닌 항목)는 조회하지 않는다.
- 캡처가 존재하지 않거나 현재 사용자의 ACTIVE 큐브 소유권에 속한 항목이 아니면 404: GALLERY_ITEM_NOT_FOUND를 반환한다.
- 스테이지의 `requiredMode`는 항상 `AR`이다.
- 트랙의 `requiredMode`는 항상 `SPECIAL`이다.
- `startPositionSeconds`는 캡처가 찍힌 원본 콘텐츠 재생 위치이다.
- `sourceType = STAGE_CAPTURE`이면 원본 스테이지 정보를 반환한다.
- `sourceType = TRACK_CAPTURE`이면 원본 트랙 정보를 반환한다.
- 트랙 정보를 반환할 때는 아티스트 이름과 가사를 함께 반환한다.

---

### 요청 Query

없음

---

### 요청 Path

| 필드 | 타입 | 필수 | 설명 |
|---|---:|:---:|---|
| `sourceType` | string | O | AR에서 다시 경험할 캡처 출처 타입. `STAGE_CAPTURE`, `TRACK_CAPTURE` 중 하나 |
| `galleryItemId` | number | O | 갤러리 항목 id |

요청 예시: /api/v1/users/me/gallery/STAGE_CAPTURE/701/ar-experience

---

### 요청 Body

없음

---

### 정상 응답 데이터
Status Code : 200

| 필드 | 타입 | 설명 |
|---|---:|---|
| `galleryItem.contentType` | string | 원본 콘텐츠 타입. `STAGE` 또는 `TRACK` |
| `galleryItem.requiredMode` | string | 다시 경험하기에 필요한 재생 모드 |
| `galleryItem.startPositionSeconds` | number \| null | 캡처가 찍힌 원본 콘텐츠 재생 위치 |
| `galleryItem.stage.id` | number | 스테이지 id |
| `galleryItem.stage.title` | string | 스테이지 제목 |
| `galleryItem.stage.videoUrl` | string | 스테이지 영상 URL |
| `galleryItem.stage.durationSeconds` | number | 스테이지 영상 길이 |
| `galleryItem.track.id` | number | 트랙 id |
| `galleryItem.track.title` | string | 트랙 제목 |
| `galleryItem.track.artistName` | string | 트랙 아티스트 이름 |
| `galleryItem.track.audioUrl` | string | 트랙 오디오 URL |
| `galleryItem.track.durationSeconds` | number | 트랙 길이 |
| `galleryItem.track.lyrics` | string | 트랙 가사 |

스테이지 캡처인 경우

```json
{
  "galleryItem": {
    "contentType": "STAGE",
    "requiredMode": "AR",
    "startPositionSeconds": 74,
    "stage": {
      "id": 1,
      "title": "SOLO",
      "videoUrl": "app://assets/stages/SOLO_SPECIAL_MV.mp4",
      "durationSeconds": 222
    }
  }
}
```

트랙 캡처인 경우

```json
{
  "galleryItem": {
    "contentType": "TRACK",
    "requiredMode": "SPECIAL",
    "startPositionSeconds": 35,
    "track": {
      "id": 101,
      "title": "SOLO",
      "artistName": "JENNIE",
      "audioUrl": "app://assets/tracks/SOLO.mp3",
      "durationSeconds": 179,
      "lyrics": "천진난만 청순가련..."
    }
  }
}
```

---

### 오류 응답 데이터
Status Code : 404

캡처가 존재하지 않거나 현재 사용자의 ACTIVE 큐브 소유권에 속한 항목이 아닌 경우

```json
{
  "code": "GALLERY_ITEM_NOT_FOUND",
  "message": "갤러리 항목을 찾을 수 없습니다."
}
```



## 갤러리 항목 삭제
- http 메서드: DELETE
- 엔드포인트: `/api/v1/users/me/gallery/{sourceType}/{galleryItemId}`
- 도메인: gallery

### API 설명

사용자가 갤러리 상세 화면에서 직접 저장한 캡처 사진의 `삭제` 버튼을 누르면 호출한다.

실제 데이터를 삭제하지 않고 `deleted_at`에 삭제 시각을 저장하는 소프트 딜리트를 수행한다.

이때 사용자가 생성한 이미지인 캡처 이미지들만 삭제가 가능하다.

---

### 처리 정책

- 로그인 구현 전에는 현재 사용자를 항상 id=1로 간주한다.
- 삭제 가능 항목은 `STAGE_CAPTURE`, `TRACK_CAPTURE`, `INTERACTION_CAPTURE`뿐이다.
- `ALBUM_IMAGE` 등 사용자가 직접 저장한 캡처가 아닌 항목은 삭제할 수 없다.
- 현재 사용자의 `ACTIVE` 큐브 소유권에 속한 캡처만 삭제할 수 있다.
- 이미 삭제된 항목(`deleted_at`이 null이 아닌 항목)은 찾을 수 없는 항목으로 처리한다.
- 삭제할 항목이 존재하지 않거나 현재 사용자의 ACTIVE 큐브 소유권에 속한 항목이 아니면 404: GALLERY_ITEM_NOT_FOUND를 반환한다.
- Azure Blob Storage의 실제 이미지 파일은 삭제하지 않는다.
- 삭제 시각은 서버의 현재 한국시간 기준 offset 없는 datetime으로 `deleted_at`에 저장한다.

---

### 요청 Query

없음

---

### 요청 Path

| 필드 | 타입 | 필수 | 설명 |
|---|---:|:---:|---|
| `sourceType` | string | O | 삭제할 갤러리 항목 출처 타입. `STAGE_CAPTURE`, `TRACK_CAPTURE`, `INTERACTION_CAPTURE` 중 하나 |
| `galleryItemId` | number | O | 삭제할 갤러리 항목 id |

요청 예시: /api/v1/users/me/gallery/INTERACTION_CAPTURE/901

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

삭제할 캡처가 존재하지 않거나 현재 사용자의 ACTIVE 큐브 소유권에 속한 항목이 아닌 경우

```json
{
  "code": "GALLERY_ITEM_NOT_FOUND",
  "message": "삭제할 갤러리 항목을 찾을 수 없습니다."
}
```
