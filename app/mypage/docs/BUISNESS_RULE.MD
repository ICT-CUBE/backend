# 마이페이지 도메인 비즈니스 룰

## 마이페이지 조회

### 인증 및 사용자 식별

- 이 API는 인증이 필요한 API다.
- 클라이언트가 전달한 `Authorization: Bearer {accessToken}` 헤더의 JWT를 공통 인증 의존성에서 검증한다.
- 서비스에는 클라이언트가 임의로 전달한 사용자 ID가 아니라, 검증된 JWT의 `sub`에서 얻은 현재 사용자 ID를 전달한다.
- 공통 인증 단계에서 활성 사용자의 존재까지 확인하므로 마이페이지 조회 로직은 별도의 사용자 404 오류를 정의하지 않는다.

### 사용자 정보 조회

- 현재 사용자 ID와 일치하는 `user` 행에서 `nickname`, `email`, `profile_character_img_url`을 조회한다.
- `nickname` 또는 `profile_character_img_url`이 DB에서 `NULL`이면 응답에서도 그대로 `null`을 반환한다.
- `NULL`을 빈 문자열이나 기본 이미지 URL로 치환하지 않는다.

### 작성한 게시글 수 계산

- `post.user_id`가 현재 사용자 ID와 같은 게시글을 대상으로 한다.
- `post.status`가 `ACTIVE` 또는 `REPORTED`인 게시글을 포함한다.
- `post.deleted_at IS NULL`인 게시글만 포함한다.
- 위 조건을 만족하는 `post.id`의 개수를 `writtenPostCount`로 반환한다.
- 조건을 만족하는 게시글이 없으면 `0`을 반환한다.

### 댓글 단 게시글 수 계산

- 댓글 개수가 아니라 현재 사용자가 댓글을 작성한 서로 다른 게시글의 개수를 계산한다.
- `comment.user_id`가 현재 사용자 ID와 같은 댓글을 대상으로 한다.
- `comment.status`가 `ACTIVE` 또는 `REPORTED`이고 `comment.deleted_at IS NULL`인 댓글만 포함한다.
- 댓글이 연결된 게시글도 `post.status`가 `ACTIVE` 또는 `REPORTED`이고 `post.deleted_at IS NULL`이어야 한다.
- `COUNT(DISTINCT comment.post_id)` 방식으로 계산하여 같은 게시글에 댓글을 여러 개 작성해도 한 건으로 센다.
- 자신이 작성한 게시글에 자신이 댓글을 작성한 경우도 조건을 만족하면 포함한다.
- 조건을 만족하는 게시글이 없으면 `0`을 반환한다.

### 응답 및 트랜잭션

- 응답은 `user`와 `activity` 객체로 구분한다.
- `activity.writtenPostCount`에는 작성한 게시글 수를, `activity.commentedPostCount`에는 댓글을 작성한 서로 다른 게시글 수를 담는다.
- 조회 전용 API이므로 데이터 생성·수정, `commit`, 행 잠금을 수행하지 않는다.
- 요약 수치만 반환하므로 페이징을 적용하지 않는다.
- API 고유 오류 응답은 정의하지 않으며 요청 형식, 인증, 서버 오류는 공통 오류 정책을 따른다.
