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