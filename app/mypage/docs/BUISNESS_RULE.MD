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

## 사용자 프로필 수정

### API 기본 규칙

- 사용자 프로필 수정은 `PATCH /api/v1/users/me/profile` 엔드포인트를 사용한다.
- 요청 Body는 JSON 형식으로 전달받는다.
- `nickname`과 `profileCharacterCode`를 모두 필수값으로 받는다.
- 두 필드 중 하나라도 누락되거나 입력값 검증에 실패하면 공통 `400 INVALID_REQUEST`를 반환한다.
- 수정 성공 시 응답 Body 없이 `204 No Content`를 반환한다.

### 인증 및 사용자 식별

- 이 API는 인증이 필요한 API다.
- 클라이언트가 전달한 `Authorization: Bearer {accessToken}` 헤더의 JWT를 공통 인증 의존성에서 검증한다.
- 서비스에는 클라이언트가 임의로 전달한 사용자 ID가 아니라, 검증된 JWT의 `sub`에서 얻은 현재 사용자 ID를 전달한다.
- 공통 인증 단계에서 `status = ACTIVE`, `deleted_at IS NULL`인 사용자의 존재를 확인한다.
- 인증이 완료된 사용자 행이 프로필 수정 단계에서 존재하지 않으면 데이터 정합성 문제이므로 공통 `500 INTERNAL_SERVER_ERROR`로 처리하며 별도의 사용자 404 오류를 정의하지 않는다.

### 닉네임 검증과 저장

- 닉네임은 필수값이지만 다른 사용자와의 중복을 허용한다.
- 닉네임은 회원가입과 동일하게 앞뒤 공백을 제거한 값을 검증하고 저장한다.
- 공백 제거 결과가 빈 문자열이면 공통 `400 INVALID_REQUEST`를 반환한다.
- 닉네임은 DB의 `user.nickname VARCHAR(20)`에 맞춰 1자 이상 20자 이하로 제한한다.
- 한글, 영문, 숫자, 공백, 특수문자 등 문자 종류는 별도로 제한하지 않는다.
- 검증한 닉네임을 현재 사용자의 `user.nickname`에 저장한다.

### 프로필 캐릭터 검증과 저장

- `profileCharacterCode`는 `profile_001`, `profile_002`, `profile_003`만 허용한다.
- 허용 목록에 없는 값은 공통 `400 INVALID_REQUEST`를 반환한다.
- 프로필 캐릭터 코드의 허용 목록과 이미지 URL 변환 로직은 사용자 도메인의 공통 모듈로 분리하여 회원가입과 프로필 수정에서 함께 사용한다.
- 프로필 이미지 URL은 `https://haniumstorage.blob.core.windows.net/hanium/profile_image/{profileCharacterCode}.png` 형식으로 조합한다.
- 조합한 절대 URL을 현재 사용자의 `user.profile_character_img_url`에 저장한다.
- 프로필 수정 과정에서는 Azure Blob에 파일을 새로 업로드하지 않는다.
- 프로필 캐릭터 코드는 별도 DB 컬럼에 저장하지 않는다.

### 수정 및 트랜잭션

- 닉네임과 프로필 이미지 URL은 하나의 DB 트랜잭션에서 함께 수정한다.
- 두 값 중 하나만 선택적으로 변경하는 요청은 지원하지 않는다.
- 기존 값과 동일한 닉네임 또는 프로필 캐릭터 코드로 요청해도 정상 처리한다.
- 저장에 성공하면 트랜잭션을 커밋하고 `204 No Content`를 반환한다.
- 저장 중 오류가 발생하면 트랜잭션을 롤백하고 공통 `500 INTERNAL_SERVER_ERROR`로 처리한다.

### 오류 응답

- 필수값 누락, 유효하지 않은 닉네임 또는 허용하지 않는 프로필 캐릭터 코드는 공통 `400 INVALID_REQUEST`로 처리한다.
- 유효하지 않거나 만료된 Access Token은 공통 `401 INVALID_ACCESS_TOKEN`으로 처리한다.
- 공통 `500 INTERNAL_SERVER_ERROR` 외 별도의 도메인 오류 응답은 정의하지 않는다.

## 내가 쓴 글 조회

### API 기본 규칙

- 내가 쓴 글 조회는 `GET /api/v1/users/me/posts` 엔드포인트를 사용한다.
- 현재 사용자가 작성한 게시글만 반환한다.
- 게시판 유형 필터와 제목 검색 기능은 제공하지 않는다.
- 조회 결과가 없으면 오류를 반환하지 않고 `posts`를 빈 배열로 반환한다.
- 조회 전용 API이므로 데이터 생성·수정, `commit`, 행 잠금을 수행하지 않는다.

### 인증 및 조회 대상

- 이 API는 인증이 필요한 API다.
- 클라이언트가 전달한 `Authorization: Bearer {accessToken}` 헤더의 JWT를 공통 인증 의존성에서 검증한다.
- 서비스에는 클라이언트가 임의로 전달한 사용자 ID가 아니라, 검증된 JWT의 `sub`에서 얻은 현재 사용자 ID를 전달한다.
- `post.user_id`가 현재 사용자 ID와 같은 게시글만 조회한다.
- `post.status`가 `ACTIVE` 또는 `REPORTED`이고 `post.deleted_at IS NULL`인 게시글을 반환한다.
- `post.status = DELETED`이거나 `post.deleted_at IS NOT NULL`인 게시글은 제외한다.
- 신고 상태인 `REPORTED` 게시글도 작성자인 현재 사용자에게 반환한다.

### 게시글 응답

- 각 게시글에 게시글 id, 게시판 유형, 제목, 내용, 작성자 닉네임, 작성 시각, 좋아요 수, 댓글 수와 현재 사용자의 좋아요 여부를 포함한다.
- `id`는 게시글 상세 화면으로 이동할 때 기존 커뮤니티 상세 조회 API의 `postId`로 사용한다.
- 게시글의 `boardType`은 `FREE` 또는 `CERTIFICATION`을 반환한다.
- 게시글 제목과 내용은 축약하지 않고 저장된 전체 값을 반환하며 화면 표시 길이와 말줄임 처리는 프론트엔드에서 수행한다.
- `authorNickname`은 현재 사용자의 `user.nickname`을 반환하므로 사용자가 닉네임을 변경하면 과거 게시글에도 변경된 닉네임이 표시된다.
- 현재 사용자의 닉네임이 `NULL`이면 `authorNickname`도 `null`로 반환한다.
- 모든 게시글이 현재 사용자 소유이므로 작성자 사용자 id, 프로필 이미지 URL과 `isMine`은 응답에 포함하지 않는다.
- 날짜/시간 값은 한국시간 기준 offset 없는 ISO 8601 형식으로 반환한다.

### 좋아요와 댓글 집계

- `likeCount`는 해당 게시글의 `post_like.is_liked = true`인 항목만 집계한다.
- 좋아요 이력이 없거나 모든 좋아요가 취소된 게시글의 `likeCount`는 0이다.
- `isLiked`는 현재 사용자의 `post_like.is_liked = true`인 데이터가 존재하면 `true`로 반환한다.
- 현재 사용자의 좋아요 데이터가 없거나 `is_liked = false`이면 `isLiked`는 `false`로 반환한다.
- `commentCount`는 해당 게시글의 `comment.status = ACTIVE`이고 `comment.deleted_at IS NULL`인 댓글만 집계한다.
- `REPORTED`, `DELETED` 댓글과 `deleted_at IS NOT NULL`인 댓글은 `commentCount`에 포함하지 않는다.
- 집계 조건을 만족하는 댓글이 없으면 `commentCount`는 0이다.

### 정렬 및 페이지네이션

- 게시글은 `post.created_at` 내림차순으로 정렬한다.
- 작성 시각이 같은 게시글은 `post.id` 내림차순으로 정렬한다.
- 페이지 번호는 0부터 시작하며 `page`를 생략하면 0을 사용한다.
- 페이지 크기는 `size`로 전달받으며 생략하면 20을 사용한다.
- `page < 0` 또는 `size < 1`이면 공통 `400 INVALID_REQUEST`를 반환한다.
- 응답의 `pagination.page`와 `pagination.size`에는 요청에 적용한 값을 반환한다.
- 응답의 `pagination.hasNext`는 다음 페이지 존재 여부를 나타낸다.

### 오류 응답

- 잘못된 `page` 또는 `size`는 공통 `400 INVALID_REQUEST`로 처리한다.
- 유효하지 않거나 만료된 Access Token은 공통 `401 INVALID_ACCESS_TOKEN`으로 처리한다.
- 작성한 게시글이 없는 경우를 포함하여 별도의 도메인 404 오류는 정의하지 않는다.
- 공통 `500 INTERNAL_SERVER_ERROR` 외 별도의 도메인 오류 응답은 정의하지 않는다.

## 댓글 단 글 조회

### API 기본 규칙

- 댓글 단 글 조회는 `GET /api/v1/users/me/commented-posts` 엔드포인트를 사용한다.
- 현재 사용자가 댓글을 작성한 서로 다른 게시글만 반환한다.
- 게시판 유형 필터와 제목 검색 기능은 제공하지 않는다.
- 조회 결과가 없으면 오류를 반환하지 않고 `posts`를 빈 배열로 반환한다.
- 조회 전용 API이므로 데이터 생성·수정, `commit`, 행 잠금을 수행하지 않는다.

### 인증 및 조회 대상

- 이 API는 인증이 필요한 API다.
- 클라이언트가 전달한 `Authorization: Bearer {accessToken}` 헤더의 JWT를 공통 인증 의존성에서 검증한다.
- 서비스에는 클라이언트가 임의로 전달한 사용자 ID가 아니라, 검증된 JWT의 `sub`에서 얻은 현재 사용자 ID를 전달한다.
- `comment.user_id`가 현재 사용자 ID와 같은 댓글을 기준으로 게시글을 조회한다.
- 조회 기준 댓글은 `comment.status`가 `ACTIVE` 또는 `REPORTED`이고 `comment.deleted_at IS NULL`이어야 한다.
- 같은 게시글에 조건을 만족하는 댓글을 여러 개 작성했어도 해당 게시글은 한 번만 반환한다.
- 현재 사용자가 자신이 작성한 게시글에 댓글을 작성한 경우도 조건을 만족하면 포함한다.
- 조회할 게시글은 `post.status`가 `ACTIVE` 또는 `REPORTED`이고 `post.deleted_at IS NULL`이어야 한다.
- `post.status = DELETED`이거나 `post.deleted_at IS NOT NULL`인 게시글은 제외한다.
- 신고 상태인 `REPORTED` 게시글도 조회 결과에 포함한다.

### 게시글 응답

- 응답 구조는 내가 쓴 글 조회와 동일하게 `posts`와 `pagination` 객체로 구분한다.
- 각 게시글에 게시글 id, 게시판 유형, 제목, 내용, 작성자 닉네임, 작성 시각, 좋아요 수, 댓글 수와 현재 사용자의 좋아요 여부를 포함한다.
- `id`는 게시글 상세 화면으로 이동할 때 기존 커뮤니티 상세 조회 API의 `postId`로 사용한다.
- 게시글의 `boardType`은 `FREE` 또는 `CERTIFICATION`을 반환한다.
- 게시글 제목과 내용은 축약하지 않고 저장된 전체 값을 반환하며 화면 표시 길이와 말줄임 처리는 프론트엔드에서 수행한다.
- `authorNickname`은 게시글 작성자의 현재 `user.nickname`을 반환한다.
- 게시글 작성자의 닉네임이 `NULL`이면 `authorNickname`도 `null`로 반환한다.
- 작성자 사용자 id, 프로필 이미지 URL과 `isMine`은 응답에 포함하지 않는다.
- 날짜/시간 값은 한국시간 기준 offset 없는 ISO 8601 형식으로 반환한다.

### 좋아요와 댓글 집계

- `likeCount`는 해당 게시글의 `post_like.is_liked = true`인 항목만 집계한다.
- 좋아요 이력이 없거나 모든 좋아요가 취소된 게시글의 `likeCount`는 0이다.
- `isLiked`는 현재 사용자의 `post_like.is_liked = true`인 데이터가 존재하면 `true`로 반환한다.
- 현재 사용자의 좋아요 데이터가 없거나 `is_liked = false`이면 `isLiked`는 `false`로 반환한다.
- `commentCount`는 해당 게시글에 작성된 전체 댓글 중 `comment.status = ACTIVE`이고 `comment.deleted_at IS NULL`인 댓글만 집계한다.
- `commentCount`는 현재 사용자가 작성한 댓글 수가 아니라 게시글에 달린 전체 유효 댓글 수다.
- `REPORTED`, `DELETED` 댓글과 `deleted_at IS NOT NULL`인 댓글은 `commentCount`에 포함하지 않는다.
- 집계 조건을 만족하는 댓글이 없으면 `commentCount`는 0이다.

### 정렬 및 페이지네이션

- 게시글은 `post.created_at` 내림차순으로 정렬한다.
- 현재 사용자가 댓글을 작성한 시각은 정렬 기준으로 사용하지 않는다.
- 게시글 작성 시각이 같은 경우 `post.id` 내림차순으로 정렬한다.
- 페이지 번호는 0부터 시작하며 `page`를 생략하면 0을 사용한다.
- 페이지 크기는 `size`로 전달받으며 생략하면 20을 사용한다.
- 게시글 중복을 제거한 뒤 정렬과 페이지네이션을 적용한다.
- `page < 0` 또는 `size < 1`이면 공통 `400 INVALID_REQUEST`를 반환한다.
- 응답의 `pagination.page`와 `pagination.size`에는 요청에 적용한 값을 반환한다.
- 응답의 `pagination.hasNext`는 다음 페이지 존재 여부를 나타낸다.

### 오류 응답

- 잘못된 `page` 또는 `size`는 공통 `400 INVALID_REQUEST`로 처리한다.
- 유효하지 않거나 만료된 Access Token은 공통 `401 INVALID_ACCESS_TOKEN`으로 처리한다.
- 댓글을 작성한 게시글이 없는 경우를 포함하여 별도의 도메인 404 오류는 정의하지 않는다.
- 공통 `500 INTERNAL_SERVER_ERROR` 외 별도의 도메인 오류 응답은 정의하지 않는다.
