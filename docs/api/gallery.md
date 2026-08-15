## 갤러리 조회
- http 메서드: get
- 엔드포인트: api/v1/users/me/gallery

### API 설명

갤러리에 들어가면 호출된다.

앨범 관련 콘텐츠 이미지들, 사용자가 캡처한 이미지들을 반환한다. 사용자 캡처 이미지에는 스테이지 캡쳐, 트랙 특별 재생 캡쳐, 아바타 현실 소환 사진이 있다.

이때 삭제된 항목, deleted_at이 null이 아닌 사진은 반환되지 않는다. 

한 번의 호출당 20개의 사진으로 페이징해서 전송한다. `size`는 20으로 고정한다.

- 로그인 구현 전에는 mock 현재 사용자 ID 1을 사용한다.
- 캡처 이미지는 현재 사용자의 `ACTIVE` 큐브 소유권에 연결된 항목만 반환한다.
- 앨범 이미지는 사용자 소유권과 무관하게 전체 앨범 이미지를 반환한다.
- `ALBUM` 카테고리는 `album_image.image_type = ALBUM_IMAGE`인 항목만 의미한다.
- `CONCERT_STILLCUT` 카테고리는 `album_image.image_type = CONCERT_STILLCUT`인 항목만 의미한다.
- `YEZUL_FRAME`은 갤러리 조회 응답에 포함하지 않는다.
- 스테이지 캡처와 트랙 캡처의 `displayDate`는 `captured_at` 기준이다.
- 아바타 현실 소환 사진의 `displayDate`는 `pictured_at` 기준이다.
- 앨범 이미지의 `displayDate`는 앨범 `release_date` 기준이다.
- `id`는 원본 테이블의 id를 그대로 반환하며, 프론트는 `sourceType`과 조합해 항목을 식별한다.
- 이미지 URL이 null인 아바타 현실 소환 사진은 반환하지 않는다.

---

### 요청 Query

```json
{
  "category": "ALL",
  "page": 0,
  "size": 20
}
```

```json
{
  "category": "CAPTURE",
  "page": 0,
  "size": 20
}
```

```json
{
  "category": "ALBUM",
  "page": 0,
  "size": 20
}
```

```json
{
  "category": "CONCERT_STILLCUT",
  "page": 0,
  "size": 20
}
```
요청 예시: api/v1/users/me/gallery?category=ALL&page=0&size=20

---

### 요청 Path

---

### 요청 Body

---

### 정상 응답 데이터

Status Code : 200

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
      "id": 801,
      "sourceType": "INTERACTION_CAPTURE",
      "category": "CAPTURE",
      "imageUrl": "https://cdn.example.com/track-captures/capture-801.jpg",
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



## AR에서 다시 경험하기
- http 메서드: get
- 엔드포인트: api/v1/users/me/gallery/{sourceType}/{galleryItemId}/ar-experience

### API 설명

사용자가 갤러리 캡쳐 목록에서 특정 이미지를 클릭하고 AR에서 다시 경험하기를 누르면 호출된다.
해당 캡처의 원본 스테이지 또는 트랙 정보를 반환한다.

- `sourceType`은 `STAGE_CAPTURE`, `TRACK_CAPTURE`만 허용한다.
- `INTERACTION_CAPTURE`, `ALBUM_IMAGE` 등 지원하지 않는 `sourceType`은 공통 400 `INVALID_REQUEST`를 반환한다.
- 현재 사용자의 `ACTIVE` 큐브 소유권에 속한 캡처만 조회할 수 있다.
- 삭제된 캡처(`deleted_at`이 null이 아닌 항목)는 조회하지 않는다.
- 스테이지의 `requiredMode`는 항상 `AR`이다.
- 트랙의 `requiredMode`는 항상 `SPECIAL`이다.
- `startPositionSeconds`는 캡처가 찍힌 원본 콘텐츠 재생 위치이다.

---

### 요청 Query

---

### 요청 Path

```json
{
	"sourceType": "STAGE_CAPTURE",
	"galleryItemId": 701
}
```

```json
{
  "sourceType": "TRACK_CAPTURE",
  "galleryItemId": 801
}
```

요청 예시: api/v1/users/me/gallery/STAGE_CAPTURE/701/ar-experience

---

### 요청 Body

---

### 정상 응답 데이터

Status Code : 200

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

```json
{
  "galleryItem": {
    "contentType": "TRACK",
    "requiredMode": "SPECIAL",
    "startPositionSeconds": 35,
    "track": {
      "id": 101,
      "title": "SOLO",
      "audioUrl": "app://assets/tracks/SOLO.mp3",
      "durationSeconds": 179
    }
  }
}
```

---

### 오류 응답 데이터


Status Code : 404

```json
{
  "code": "GALLERY_ITEM_NOT_FOUND",
  "message": "갤러리 항목을 찾을 수 없습니다."
}
```



## 갤러리 항목 삭제
- http 메서드: delete
- 엔드포인트: api/v1/users/me/gallery/{sourceType}/{galleryItemId}

### API 설명

사용자가 갤러리 상세 화면에서 직접 저장한 캡처 사진의 `삭제` 버튼을 누르면 호출한다.

실제 데이터를 삭제하지 않고 다음 필드에 삭제 시각을 저장하는 소프트 딜리트를 수행한다.

이때 사용자가 생성한 이미지인 캡처 이미지들만 삭제가 가능하다.

- 삭제 가능 항목은 `STAGE_CAPTURE`, `TRACK_CAPTURE`, `INTERACTION_CAPTURE`뿐이다.
- `ALBUM_IMAGE` 등 사용자가 직접 저장한 캡처가 아닌 항목은 삭제할 수 없다.
- 현재 사용자의 `ACTIVE` 큐브 소유권에 속한 캡처만 삭제할 수 있다.
- 이미 삭제된 항목(`deleted_at`이 null이 아닌 항목)은 찾을 수 없는 항목으로 처리한다.
- Azure Blob Storage의 실제 이미지 파일은 삭제하지 않는다.
- 삭제 시각은 한국 시간 기준으로 `deleted_at`에 저장한다.

---

### 요청 Query

---

### 요청 Path

```json
{
  "sourceType": "STAGE_CAPTURE",
  "galleryItemId": 701
}
```

```json
{
  "sourceType": "TRACK_CAPTURE",
  "galleryItemId": 801
}
```

```json
{
  "sourceType": "INTERACTION_CAPTURE",
  "galleryItemId": 901
}
```

요청 예시: api/v1/users/me/gallery/INTERACTION_CAPTURE/901

---

### 요청 Body

---

### 정상 응답 데이터

Status Code : 204

---

### 오류 응답 데이터

Status Code : 404

```json
{
  "code": "GALLERY_ITEM_NOT_FOUND",
  "message": "삭제할 갤러리 항목을 찾을 수 없습니다."
}
```
