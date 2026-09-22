## 마이페이지 조회
- http 메서드: get
- domain: mypage
- endpoint: /api/v1/users/me

### API 설명

로그인한 사용자가 마이페이지 화면에 진입할 때 호출한다.

사용자의 프로필 정보와 작성한 게시글 수, 댓글을 작성한 게시글 수를 반환한다.

---

### 처리 정책

- 사용자 정보는 Access Token으로 식별한 현재 사용자를 기준으로 조회한다.
- 작성한 게시글 수는 삭제되지 않은 `ACTIVE`, `REPORTED` 게시글의 개수다.
- 댓글 단 게시글 수는 사용자가 댓글을 작성한 서로 다른 게시글의 개수다.

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
| --- | --- | --- |
| `user` | object | 현재 사용자 정보 |
| `user.nickname` | string | null | 사용자 닉네임. 설정되지 않았으면 `null` |
| `user.email` | string | 사용자 이메일 |
| `user.profileCharacterImgUrl` | string | null | 사용자 프로필 캐릭터 이미지 URL. 설정되지 않았으면 `null` |
| `activity` | object | 사용자의 커뮤니티 활동 요약 |
| `activity.writtenPostCount` | number | 사용자가 작성한 게시글 수 |
| `activity.commentedPostCount` | number | 사용자가 댓글을 작성한 서로 다른 게시글 수 |

```json
{
  "user": {
    "nickname": "DORI",
    "email": "dodorori@gmail.com",
    "profileCharacterImgUrl": "https://haniumstorage.blob.core.windows.net/hanium/profile_image/profile_001.png"
  },
  "activity": {
    "writtenPostCount": 4,
    "commentedPostCount": 2
  }
}
```

---

### 오류 응답 데이터

별도 오류 응답 없음


## 사용자 프로필 수정
- http 메서드: patch
- domain: mypage
- endpoint: /api/v1/users/me/profile

### API 설명

로그인한 사용자가 자신의 닉네임과 프로필 캐릭터를 변경할 때 호출한다.

전달받은 프로필 캐릭터 코드를 이미지 URL로 변환하여 닉네임과 함께 현재 사용자 정보에 저장한다.

---

### 처리 정책

- 사용자 정보는 Access Token으로 식별한 현재 사용자를 기준으로 수정한다.
- `nickname`과 `profileCharacterCode`는 모두 필수다.
- `nickname`은 앞뒤 공백을 제거한 후 1자 이상 20자 이하여야 하며, 다른 사용자와의 중복을 허용한다.
- `profileCharacterCode`는 `profile_001`, `profile_002`, `profile_003` 중 하나만 허용한다.
- 프로필 캐릭터 코드는 회원가입과 동일한 공통 정의와 URL 변환 규칙을 사용한다.
- 프로필 이미지 URL은 `https://haniumstorage.blob.core.windows.net/hanium/profile_image/{profileCharacterCode}.png` 형식으로 조합한다.
- 검증한 닉네임과 조합한 이미지 URL을 각각 `user.nickname`, `user.profile_character_img_url`에 저장한다.
- 프로필 이미지는 Azure Blob에 새로 업로드하지 않는다.
- 유효하지 않은 요청값은 공통 오류 정책에 따라 `400 INVALID_REQUEST`를 반환한다.

---

### 요청 Query

없음

---

### 요청 Path

없음

---

### 요청 Body

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `nickname` | string | O | 사용자 닉네임. 앞뒤 공백 제거 후 1~20자, 중복 허용 |
| `profileCharacterCode` | string | O | 프로필 캐릭터 코드: profile_001 \| profile_002 \| profile_003 |

```json
{
  "nickname": "DORI",
  "profileCharacterCode": "profile_001"
}
```

---

### 정상 응답 데이터

Status Code : 204

응답 Body 없음

---

### 오류 응답 데이터

Status Code : 400

필수값이 누락되었거나 닉네임 또는 프로필 캐릭터 코드가 유효하지 않은 경우

```json
{
  "code": "INVALID_REQUEST",
  "message": "요청값이 올바르지 않습니다."
}
```


## 댓글 단 글 조회
- http 메서드: get
- domain: mypage
- endpoint: /api/v1/users/me/commented-posts

### API 설명

로그인한 사용자가 마이페이지에서 자신이 댓글을 작성한 게시글 목록을 확인할 때 호출한다.

현재 사용자가 댓글을 작성한 서로 다른 게시글을 최신순으로 조회하고 게시판 유형, 작성자 닉네임, 좋아요 수와 댓글 수를 페이지 단위로 반환한다.

---

### 처리 정책

- Access Token으로 식별한 현재 사용자가 삭제되지 않은 댓글을 작성한 게시글을 조회한다.
- 같은 게시글에 댓글을 여러 개 작성했어도 해당 게시글은 한 번만 반환한다.
- 현재 사용자가 작성한 게시글에 직접 댓글을 작성한 경우도 조회 결과에 포함한다.
- 삭제되지 않은 `ACTIVE`, `REPORTED` 게시글을 포함한다.
- 게시글은 최신 작성 순으로 반환한다.
- 별도의 게시판 필터와 검색 기능은 제공하지 않는다.
- 게시글 내용은 축약하지 않고 전체를 반환하며 화면의 말줄임 처리는 프론트엔드에서 수행한다.
- 페이지는 0부터 시작하며 한 페이지의 기본 게시글 수는 20개이다.
- 조회 결과가 없으면 오류 없이 빈 게시글 목록을 반환한다.

---

### 요청 Query

| 필드 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `page` | number | X | 0 | 조회할 페이지 번호, 0부터 시작 |
| `size` | number | X | 20 | 한 페이지에 반환할 게시글 수, 1 이상 |

요청 예시: /api/v1/users/me/commented-posts?page=0&size=20

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
| `posts` | array | 현재 사용자가 댓글을 작성한 서로 다른 게시글 목록 |
| `posts[].id` | number | 게시글 id |
| `posts[].boardType` | string | 게시판 유형: FREE \| CERTIFICATION |
| `posts[].title` | string | 게시글 제목 |
| `posts[].content` | string | 축약하지 않은 게시글 내용 |
| `posts[].authorNickname` | string \| null | 게시글 작성자의 닉네임 |
| `posts[].createdAt` | string(date-time) | 게시글 작성 시각 |
| `posts[].likeCount` | number | 게시글 좋아요 수 |
| `posts[].commentCount` | number | 삭제되지 않은 `ACTIVE` 댓글 수 |
| `posts[].isLiked` | boolean | 현재 사용자의 게시글 좋아요 여부 |
| `pagination.page` | number | 현재 페이지 번호 |
| `pagination.size` | number | 페이지당 게시글 수 |
| `pagination.hasNext` | boolean | 다음 페이지 존재 여부 |

```json
{
  "posts": [
    {
      "id": 21,
      "boardType": "FREE",
      "title": "팬미팅 후기 공유해요!",
      "content": "어제 있었던 팬미팅 너무 감동적이었어요! 여러분은 어떤 순간이 가장 좋았나요?",
      "authorNickname": "fandomlove_12",
      "createdAt": "2026-09-22T10:15:00",
      "likeCount": 987,
      "commentCount": 15,
      "isLiked": true
    },
    {
      "id": 18,
      "boardType": "CERTIFICATION",
      "title": "큐브 인증 완료했습니다",
      "content": "오늘 드디어 큐브를 등록했어요. 인증 과정도 간단하고 좋았습니다.",
      "authorNickname": "blink_02",
      "createdAt": "2026-09-21T18:20:00",
      "likeCount": 152,
      "commentCount": 8,
      "isLiked": false
    }
  ],
  "pagination": {
    "page": 0,
    "size": 20,
    "hasNext": true
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

Status Code : 400

`page`가 0보다 작거나 `size`가 1보다 작은 경우

```json
{
  "code": "INVALID_REQUEST",
  "message": "요청값이 올바르지 않습니다."
}
```


## 내가 쓴 글 조회
- http 메서드: get
- domain: mypage
- endpoint: /api/v1/users/me/posts

### API 설명

로그인한 사용자가 마이페이지에서 자신이 작성한 게시글 목록을 확인할 때 호출한다.

현재 사용자가 작성한 게시글을 최신순으로 조회하고 게시판 유형, 작성자 닉네임, 좋아요 수와 댓글 수를 페이지 단위로 반환한다.

---

### 처리 정책

- Access Token으로 식별한 현재 사용자가 작성한 게시글만 조회한다.
- 삭제되지 않은 `ACTIVE`, `REPORTED` 게시글을 포함한다.
- 게시글은 최신 작성 순으로 반환한다.
- 별도의 게시판 필터와 검색 기능은 제공하지 않는다.
- 게시글 내용은 축약하지 않고 전체를 반환하며 화면의 말줄임 처리는 프론트엔드에서 수행한다.
- 페이지는 0부터 시작하며 한 페이지의 기본 게시글 수는 20개이다.
- 조회 결과가 없으면 오류 없이 빈 게시글 목록을 반환한다.

---

### 요청 Query

| 필드 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `page` | number | X | 0 | 조회할 페이지 번호, 0부터 시작 |
| `size` | number | X | 20 | 한 페이지에 반환할 게시글 수, 1 이상 |

요청 예시: /api/v1/users/me/posts?page=0&size=20

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
| `posts` | array | 현재 사용자가 작성한 게시글 목록 |
| `posts[].id` | number | 게시글 id |
| `posts[].boardType` | string | 게시판 유형: FREE \| CERTIFICATION |
| `posts[].title` | string | 게시글 제목 |
| `posts[].content` | string | 축약하지 않은 게시글 내용 |
| `posts[].authorNickname` | string \| null | 현재 사용자의 닉네임 |
| `posts[].createdAt` | string(date-time) | 게시글 작성 시각 |
| `posts[].likeCount` | number | 게시글 좋아요 수 |
| `posts[].commentCount` | number | 삭제되지 않은 `ACTIVE` 댓글 수 |
| `posts[].isLiked` | boolean | 현재 사용자의 게시글 좋아요 여부 |
| `pagination.page` | number | 현재 페이지 번호 |
| `pagination.size` | number | 페이지당 게시글 수 |
| `pagination.hasNext` | boolean | 다음 페이지 존재 여부 |

```json
{
  "posts": [
    {
      "id": 15,
      "boardType": "FREE",
      "title": "리액트 상태 관리 질문있습니다",
      "content": "다들 상태 관리 라이브러리 어떤 걸 주로 사용하시나요? 요즘 Zustand가 인기 많던데 도입해볼까 고민중입니다.",
      "authorNickname": "dodoriruru7",
      "createdAt": "2026-09-22T09:30:00",
      "likeCount": 2111,
      "commentCount": 34,
      "isLiked": false
    },
    {
      "id": 12,
      "boardType": "CERTIFICATION",
      "title": "K-드라마 추천해 주세요!",
      "content": "최근에 어떤 드라마가 재미있나요? 요즘 너무 많은 작품들이 나와서 선택하기 힘드네요.",
      "authorNickname": "dodoriruru7",
      "createdAt": "2026-09-21T21:10:00",
      "likeCount": 1523,
      "commentCount": 20,
      "isLiked": true
    }
  ],
  "pagination": {
    "page": 0,
    "size": 20,
    "hasNext": true
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

Status Code : 400

`page`가 0보다 작거나 `size`가 1보다 작은 경우

```json
{
  "code": "INVALID_REQUEST",
  "message": "요청값이 올바르지 않습니다."
}
```
