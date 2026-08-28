## 커뮤니티 조회
- http 메서드: get
- domain: community
- endpoint: /api/v1/community/posts

### API 설명

커뮤니티 화면에서 게시판 유형과 제목 검색어에 맞는 게시글 목록을 조회한다.

게시글과 작성자 정보, 좋아요 수, 댓글 수를 페이지 단위로 반환한다.

---

### 처리 정책

- `boardType`을 생략하면 전체 게시판을 조회하고, `FREE` 또는 `CERTIFICATION`을 전달하면 해당 게시판만 조회한다.
- `keyword`를 전달하면 게시글 내용이 아닌 제목에 해당 키워드가 포함된 게시글만 조회한다.
- `boardType`과 `keyword`를 함께 전달하면 두 조건을 모두 만족하는 게시글을 조회한다.
- 게시글은 최신 작성 순으로 반환한다.
- 페이지는 0부터 시작하며 한 페이지의 기본 게시글 수는 20개이다.
- 조회 결과가 없으면 오류 없이 빈 게시글 목록을 반환한다.

---

### 요청 Query

| 필드 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `boardType` | string | X | `ALL` | 게시판 필터: ALL | FREE | CERTIFICATION |
| `keyword` | string | X | 없음 | 게시글 제목에 포함된 문자열을 검색하는 키워드 |
| `page` | number | X | 0 | 조회할 페이지 번호, 0부터 시작 |
| `size` | number | X | 20 | 한 페이지에 반환할 게시글 수 |

일반 조회 예시: /api/v1/community/posts?boardType=ALL&page=0&size=20

검색 예시: /api/v1/community/posts?boardType=CERTIFICATION&keyword=큐브&page=0&size=20

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
| `posts` | array | 게시글 목록 |
| `posts[].id` | number | 게시글 id |
| `posts[].boardType` | string | 게시판 유형: FREE | CERTIFICATION |
| `posts[].title` | string | 게시글 제목 |
| `posts[].content` | string | 게시글 내용 |
| `posts[].author.id` | number | 작성자 사용자 id |
| `posts[].author.nickname` | string | null | 작성자 닉네임 |
| `posts[].author.profileImageUrl` | string | null | 작성자 프로필 이미지 URL |
| `posts[].createdAt` | string(date-time) | 게시글 작성 시각 |
| `posts[].likeCount` | number | 게시글 좋아요 수 |
| `posts[].commentCount` | number | 게시글 댓글 수 |
| `posts[].isLiked` | boolean | 현재 사용자의 게시글 좋아요 여부 |
| `posts[].isMine` | boolean | 현재 사용자가 작성한 게시글인지 여부 |
| `pagination.page` | number | 현재 페이지 번호 |
| `pagination.size` | number | 페이지당 게시글 수 |
| `pagination.hasNext` | boolean | 다음 페이지 존재 여부 |

```json
{
  "posts": [
    {
      "id": 2,
      "boardType": "CERTIFICATION",
      "title": "큐브 인증 완료",
      "content": "발매일에 바로 인증 성공했습니다. 코드 입력하고 3초 만에 됐어요.",
      "author": {
        "id": 1,
        "nickname": "블링크",
        "profileImageUrl": "https://haniumstorage.blob.core.windows.net/hanium/profile_image/profile_002.png"
      },
      "createdAt": "2026-08-28T20:30:00",
      "likeCount": 0,
      "commentCount": 1,
      "isLiked": false,
      "isMine": true
    },
    {
      "id": 1,
      "boardType": "FREE",
      "title": "Ruby 큐브 26번 등록했어요",
      "content": "앨범 나오자마자 큐브 등록했습니다. AR로 like JENNIE 무대 보는데 진짜 눈앞에 있는 것 같아요.",
      "author": {
        "id": 1,
        "nickname": "블링크",
        "profileImageUrl": "https://haniumstorage.blob.core.windows.net/hanium/profile_image/profile_002.png"
      },
      "createdAt": "2026-08-28T20:20:00",
      "likeCount": 1,
      "commentCount": 1,
      "isLiked": true,
      "isMine": true
    }
  ],
  "pagination": {
    "page": 0,
    "size": 20,
    "hasNext": false
  }
}
```

조회 결과가 없는 경우

```json
{
  "posts": [],
  "pagination": {
    "page": 0,
    "size": 20,
    "hasNext": false
  }
}
```

---

### 오류 응답 데이터

없음


## 커뮤니티 상세 조회
- http 메서드: get
- domain: community
- endpoint: /api/v1/community/posts/{postId}

### API 설명

커뮤니티 목록에서 선택한 게시글의 본문, 첨부 이미지, 좋아요와 댓글 정보를 조회한다.

---

### 처리 정책

- 삭제되지 않은 게시글만 상세 조회할 수 있다.
- 게시글에 등록된 사진과 삭제되지 않은 댓글을 모두 반환한다.
- 신고 상태인 게시글과 댓글도 조회 결과에 포함한다.
- 사진이 없으면 `imageUrls`, 댓글이 없으면 `comments`를 빈 배열로 반환한다.
- 댓글은 먼저 작성된 댓글부터 반환한다.

---

### 요청 Query

없음

---

### 요청 Path

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `postId` | number | O | 조회할 게시글 id |

요청 예시: /api/v1/community/posts/1

---

### 요청 Body

없음

---

### 정상 응답 데이터

Status Code : 200

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `post.id` | number | 게시글 id |
| `post.boardType` | string | 게시판 유형: FREE | CERTIFICATION |
| `post.author.id` | number | 게시글 작성자 사용자 id |
| `post.author.nickname` | string | null | 게시글 작성자 닉네임 |
| `post.author.profileImageUrl` | string | null | 게시글 작성자 프로필 이미지 URL |
| `post.createdAt` | string(date-time) | 게시글 작성 시각 |
| `post.title` | string | 게시글 제목 |
| `post.content` | string | 게시글 내용 |
| `post.imageUrls` | string[] | 게시글에 첨부된 전체 이미지 URL 목록 |
| `post.likeCount` | number | 게시글 좋아요 수 |
| `post.isLiked` | boolean | 현재 사용자의 게시글 좋아요 여부 |
| `post.commentCount` | number | 게시글 댓글 수 |
| `post.isMine` | boolean | 현재 사용자가 작성한 게시글인지 여부 |
| `post.comments` | array | 게시글에 등록된 댓글 목록 |
| `post.comments[].id` | number | 댓글 id |
| `post.comments[].author.id` | number | 댓글 작성자 사용자 id |
| `post.comments[].author.nickname` | string | null | 댓글 작성자 닉네임 |
| `post.comments[].author.profileImageUrl` | string | null | 댓글 작성자 프로필 이미지 URL |
| `post.comments[].content` | string | 댓글 내용 |
| `post.comments[].createdAt` | string(date-time) | 댓글 작성 시각 |
| `post.comments[].likeCount` | number | 댓글 좋아요 수 |
| `post.comments[].isLiked` | boolean | 현재 사용자의 댓글 좋아요 여부 |
| `post.comments[].isMine` | boolean | 현재 사용자가 작성한 댓글인지 여부 |

```json
{
  "post": {
    "id": 1,
    "boardType": "FREE",
    "author": {
      "id": 1,
      "nickname": "블링크",
      "profileImageUrl": "https://haniumstorage.blob.core.windows.net/hanium/profile_image/profile_002.png"
    },
    "createdAt": "2026-08-28T09:10:00",
    "title": "Ruby 큐브 26번 등록했어요",
    "content": "앨범 나오자마자 큐브 등록했습니다. AR로 like JENNIE 무대 보는데 진짜 눈앞에 있는 것 같아요.",
    "imageUrls": [],
    "likeCount": 4,
    "isLiked": true,
    "commentCount": 4,
    "isMine": true,
    "comments": [
      {
        "id": 1,
        "author": {
          "id": 2,
          "nickname": "지드래곤짱",
          "profileImageUrl": "https://haniumstorage.blob.core.windows.net/hanium/profile_image/profile_002.png"
        },
        "content": "축하해요! 26번 큐브 정말 부럽네요.",
        "createdAt": "2026-08-28T09:20:00",
        "likeCount": 2,
        "isLiked": false,
        "isMine": false
      },
      {
        "id": 2,
        "author": {
          "id": 4,
          "nickname": "한강블링크",
          "profileImageUrl": "https://haniumstorage.blob.core.windows.net/hanium/profile_image/profile_002.png"
        },
        "content": "AR 무대가 실제로 보는 것처럼 생생하더라고요.",
        "createdAt": "2026-08-28T09:30:00",
        "likeCount": 1,
        "isLiked": true,
        "isMine": false
      },
      {
        "id": 3,
        "author": {
          "id": 6,
          "nickname": "젠득이팬",
          "profileImageUrl": "https://haniumstorage.blob.core.windows.net/hanium/profile_image/profile_002.png"
        },
        "content": "저도 같은 큐브 등록하고 싶어요.",
        "createdAt": "2026-08-28T09:40:00",
        "likeCount": 0,
        "isLiked": false,
        "isMine": false
      },
      {
        "id": 4,
        "author": {
          "id": 9,
          "nickname": "큐브마스터",
          "profileImageUrl": "https://haniumstorage.blob.core.windows.net/hanium/profile_image/profile_002.png"
        },
        "content": "시리얼 번호가 멋집니다.",
        "createdAt": "2026-08-28T09:50:00",
        "likeCount": 0,
        "isLiked": false,
        "isMine": false
      }
    ]
  }
}
```

---

### 오류 응답 데이터

Status Code : 404

게시글이 존재하지 않거나 삭제된 경우

```json
{
  "code": "POST_NOT_FOUND",
  "message": "게시글을 찾을 수 없습니다."
}
```



## 커뮤니티 게시글 작성
- http 메서드: post
- domain: community
- endpoint: /api/v1/community/posts

### API 설명

현재 사용자가 자유게시판 또는 인증게시판에 새 게시글을 작성한다.

---

### 처리 정책

- 요청은 게시글 정보와 이미지 파일을 함께 전송할 수 있도록 `multipart/form-data` 형식을 사용한다.
- `boardType`은 `FREE` 또는 `CERTIFICATION`만 허용한다.
- `title`과 `content`는 필수이며, 앞뒤 공백을 제거한 값이 빈 문자열이면 허용하지 않는다.
- `title`은 최대 150자까지 허용한다.
- 이미지는 선택값이며 최대 5장까지 첨부할 수 있다.
- 이미지 형식은 JPG/JPEG, PNG 또는 WebP만 허용한다.
- 게시글 작성이 완료되면 생성된 게시글 id를 반환한다.

---

### 요청 Query

없음

---

### 요청 Path

없음

---

### 요청 Body

Content-Type : multipart/form-data

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `boardType` | string | O | 게시판 유형: FREE | CERTIFICATION |
| `title` | string | O | 게시글 제목. 공백으로만 구성할 수 없으며 최대 150자 |
| `content` | string | O | 게시글 내용. 공백으로만 구성할 수 없음 |
| `images` | file[] | null | X | 게시글 첨부 이미지. 최대 5장 |

이미지 허용 형식

| Content-Type | 확장자 |
| --- | --- |
| `image/jpeg` | `.jpg`, `.jpeg` |
| `image/png` | `.png` |
| `image/webp` | `.webp` |

요청 예시

```bash
curl -X POST 'https://hanium.azurewebsites.net/api/v1/community/posts' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'boardType=FREE' \
  -F 'title=새로운 UI 디자인을 소개합니다' \
  -F 'content=이번에 새롭게 작업한 디자인입니다.' \
  -F 'images=@community_image_1.jpg;type=image/jpeg' \
  -F 'images=@community_image_2.png;type=image/png'
```

---

### 정상 응답 데이터

Status Code : 201

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `postId` | number | 생성된 게시글 id |

```json
{
  "postId": 11
}
```

---

### 오류 응답 데이터

공통 `400 INVALID_REQUEST`, `500 INTERNAL_SERVER_ERROR` 외 별도 오류 응답 없음


## 커뮤니티 게시글 삭제
- http 메서드: delete
- domain: community
- endpoint: /api/v1/community/posts/{postId}

### API 설명

현재 사용자가 작성한 커뮤니티 게시글을 삭제 상태로 변경한다.

---

### 처리 정책

- 현재 사용자가 작성한 게시글만 삭제할 수 있다.
- 일반 게시글과 신고 상태인 게시글을 삭제할 수 있다.
- 게시글은 실제 데이터와 첨부 정보를 제거하지 않고 소프트 삭제한다.
- 게시글이 존재하지 않거나 이미 삭제됐거나 현재 사용자가 작성한 게시글이 아니면 동일한 404 오류를 반환한다.

---

### 요청 Query

없음

---

### 요청 Path

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `postId` | number | O | 삭제할 게시글 id. 1 이상의 정수 |

요청 예시: /api/v1/community/posts/1

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

게시글이 존재하지 않거나, 이미 삭제됐거나, 현재 사용자가 작성한 게시글이 아닌 경우

```json
{
  "code": "POST_NOT_FOUND",
  "message": "게시글을 찾을 수 없습니다."
}
```