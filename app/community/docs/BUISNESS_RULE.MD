# 커뮤니티 도메인 비즈니스 룰

## 커뮤니티 조회

- 커뮤니티 조회는 사용자 개인 리소스가 아니므로 `/api/v1/community/posts` 엔드포인트를 사용한다.
- `boardType` Query는 `ALL`, `FREE`, `CERTIFICATION` 중 하나를 사용하며, 생략하면 `ALL`을 기본값으로 사용한다.
- `ALL`은 자유게시판과 인증게시판 게시글을 모두 조회한다.
- `FREE`는 `post.board_type = FREE`인 게시글만 조회한다.
- `CERTIFICATION`은 `post.board_type = CERTIFICATION`인 게시글만 조회한다.
- `keyword`는 선택값이며, 전달되면 앞뒤 공백을 제거한 값을 검색에 사용한다.
- `keyword`가 전달되지 않았거나 공백 제거 결과가 빈 문자열이면 제목 검색 조건을 적용하지 않는다.
- 검색 대상은 `post.title`만 사용하고 `post.content`는 검색하지 않는다.
- 제목은 키워드가 포함된 게시글을 찾는 부분 일치 방식으로 검색한다.
- 제목 검색은 `post.title LIKE %keyword%` 조건을 사용한다.
- `keyword`에 LIKE 와일드카드(`%`, `_`)나 이스케이프 문자(`\`)가 들어오면 일반 문자로 검색되도록 이스케이프한다.
- 문자열 비교는 DB의 `utf8mb4_unicode_ci` 규칙을 따르므로 영문 검색어는 대소문자를 구분하지 않는다.
- `boardType`과 `keyword`가 함께 전달되면 게시판 유형 조건과 제목 검색 조건을 AND로 결합한다.
- 게시판 유형과 제목 검색 조건을 모두 적용한 뒤 페이지네이션을 수행한다.
- `post.status`가 `ACTIVE` 또는 `REPORTED`이고 `post.deleted_at IS NULL`인 게시글을 반환한다.
- `post.status = DELETED`이거나 `post.deleted_at IS NOT NULL`인 게시글은 제외한다.
- 게시글은 `post.created_at` 내림차순으로 정렬한다.
- 작성 시각이 같은 게시글은 `post.id` 내림차순으로 정렬한다.
- 작성자 정보에는 사용자 id, 닉네임과 프로필 이미지 URL을 포함한다.
- 작성자 프로필 이미지가 없으면 `profileImageUrl`은 `null`로 반환한다.
- 게시글 내용은 축약하지 않고 저장된 전체 내용을 반환하며 화면 표시 길이는 프론트에서 처리한다.
- 커뮤니티 목록 응답에는 게시글 이미지와 `post_media` 정보를 포함하지 않는다.
- 좋아요 수는 해당 게시글의 `post_like.is_liked = true`인 항목만 집계한다.
- 좋아요 이력이 없거나 모든 좋아요가 취소된 게시글의 좋아요 수는 0이다.
- `isLiked`는 현재 사용자의 `post_like.is_liked = true`인 데이터가 존재하면 `true`로 반환한다.
- 현재 사용자의 좋아요 데이터가 없거나 `is_liked = false`이면 `isLiked`는 `false`로 반환한다.
- `isMine`은 게시글의 `user_id`와 현재 사용자 id가 같으면 `true`, 다르면 `false`로 반환한다.
- 로그인 구현 전에는 `isLiked`와 `isMine`을 사용자 id 1을 기준으로 계산한다.
- 댓글 수는 `comment.status = ACTIVE`이고 `comment.deleted_at IS NULL`인 댓글만 집계한다.
- 페이지 번호는 0부터 시작하며, `page`를 생략하면 0을 사용한다.
- 페이지 크기는 `size`로 전달받으며, 생략하면 20을 사용한다.
- 응답의 `hasNext`는 다음 페이지 존재 여부를 나타낸다.
- 조회 결과가 없으면 오류를 반환하지 않고 `posts`를 빈 배열로 반환한다.
- 날짜/시간 값은 한국시간 기준 offset 없는 ISO 8601 형식으로 반환한다.
- 잘못된 `boardType`, `page < 0`, `size < 1`은 공통 `400 INVALID_REQUEST`로 처리한다.
- 공통 오류를 제외한 별도 오류 응답은 정의하지 않는다.

## 커뮤니티 상세 조회

- 커뮤니티 상세 조회는 `/api/v1/community/posts/{postId}` 엔드포인트를 사용한다.
- Path로 전달받은 `postId`를 기준으로 게시글을 조회한다.
- `post.status`가 `ACTIVE` 또는 `REPORTED`이고 `post.deleted_at IS NULL`인 게시글을 조회할 수 있다.
- `post.status = DELETED`, `post.deleted_at IS NOT NULL` 또는 존재하지 않는 게시글이면 `404 POST_NOT_FOUND`를 반환한다.
- 게시글 제목과 내용은 축약하지 않고 저장된 전체 값을 반환한다.
- 게시글 작성자 정보에는 사용자 id, 닉네임과 프로필 이미지 URL을 포함한다.
- 작성자의 닉네임이나 프로필 이미지 URL이 `NULL`이면 응답에서도 `null`로 반환한다.
- 게시글에 연결된 `post_media`의 이미지 URL을 모두 반환한다.
- 게시글 이미지는 `post_media.id` 오름차순으로 정렬한다.
- 게시글에 연결된 이미지가 없으면 `imageUrls`를 빈 배열로 반환한다.
- 댓글은 `comment.status`가 `ACTIVE` 또는 `REPORTED`이고 `comment.deleted_at IS NULL`인 항목을 모두 반환한다.
- `comment.status = DELETED`이거나 `comment.deleted_at IS NOT NULL`인 댓글은 반환하지 않는다.
- 댓글에는 별도 페이지네이션을 적용하지 않는다.
- 댓글은 `comment.created_at` 오름차순으로 정렬하고, 작성 시각이 같으면 `comment.id` 오름차순으로 정렬한다.
- 반환할 댓글이 없으면 `comments`를 빈 배열로 반환한다.
- `commentCount`는 상세 응답의 `comments`에 실제로 포함되는 댓글 수와 동일하게 계산한다.
- 게시글 좋아요 수는 해당 게시글의 `post_like.is_liked = true`인 항목만 집계한다.
- 게시글의 `isLiked`는 현재 사용자의 `post_like.is_liked = true`인 데이터가 존재하면 `true`로 반환한다.
- 게시글 좋아요 데이터가 없거나 현재 사용자의 `is_liked = false`이면 `isLiked`는 `false`로 반환한다.
- 댓글 좋아요 수는 해당 댓글의 `comment_like.is_liked = true`인 항목만 집계한다.
- 댓글의 `isLiked`는 현재 사용자의 `comment_like.is_liked = true`인 데이터가 존재하면 `true`로 반환한다.
- 댓글 좋아요 데이터가 없거나 현재 사용자의 `is_liked = false`이면 댓글의 `isLiked`는 `false`로 반환한다.
- 게시글과 댓글의 `isMine`은 각각 작성자 `user_id`와 현재 사용자 id가 같으면 `true`, 다르면 `false`로 반환한다.
- 로그인 구현 전에는 게시글과 댓글의 `isLiked`, `isMine`을 사용자 id 1을 기준으로 계산한다.
- 날짜/시간 값은 한국시간 기준 offset 없는 ISO 8601 형식으로 반환한다.
- 공통 `400 INVALID_REQUEST`, `500 INTERNAL_SERVER_ERROR`를 제외한 이 API의 오류 응답은 `404 POST_NOT_FOUND`만 사용한다.

## 커뮤니티 게시글 좋아요 토글

- 게시글 좋아요는 현재 로그인한 사용자와 게시글의 조합을 기준으로 관리한다.
- 큐브 소유권은 게시글 좋아요 처리 권한에 영향을 주지 않는다.
- 삭제되지 않은 `ACTIVE` 또는 `REPORTED` 게시글에만 좋아요를 설정하거나 취소할 수 있다.
- 사용자는 자신이 작성한 게시글에도 좋아요를 누를 수 있다.
- 좋아요 이력이 없으면 `is_liked = true`인 행을 생성하고, 이력이 있으면 기존 `is_liked` 값을 반전한다.
- 좋아요 취소 시 행을 삭제하지 않고 `is_liked = false`로 변경한다.
- `(post_id, user_id)` 조합의 좋아요 행은 최대 하나만 존재한다.
- 게시글을 잠근 뒤 좋아요 상태를 변경하여 게시글 삭제와 좋아요 요청이 동시에 처리되지 않도록 한다.
- 응답의 좋아요 수는 상태 변경 이후 `is_liked = true`인 행만 집계한다.
- 상태 변경과 좋아요 수 계산을 하나의 트랜잭션에서 처리한다.
- 토글 요청은 호출할 때마다 상태를 반전하므로 멱등성을 보장하지 않는다.
- 게시글 좋아요와 댓글 좋아요는 서로 독립된 기능으로 관리한다.

## 커뮤니티 댓글 작성

- 댓글은 현재 로그인한 사용자를 작성자로 저장한다.
- 큐브 소유권은 댓글 작성 권한에 영향을 주지 않는다.
- 삭제되지 않은 `ACTIVE` 또는 `REPORTED` 게시글에만 댓글을 작성할 수 있다.
- 사용자는 자신이 작성한 게시글에도 댓글을 작성할 수 있다.
- 댓글 내용은 앞뒤 공백을 제거한 후 1자 이상 1,000자 이하인 경우에만 저장한다.
- 댓글 내용 내부의 줄바꿈은 허용한다.
- 새 댓글의 상태는 `ACTIVE`이고 `deleted_at`은 `null`이다.
- 커뮤니티 댓글은 대댓글과 이미지 첨부를 지원하지 않는다.
- 게시글을 잠근 뒤 댓글을 생성하여 게시글 삭제와 댓글 작성이 동시에 처리되지 않도록 한다.
- 새 댓글은 좋아요 이력이 없으므로 좋아요 수 0, 현재 사용자 좋아요 여부 false로 취급한다.
- 새 댓글의 작성자는 현재 사용자이므로 현재 사용자 작성 여부를 true로 반환한다.
- 댓글 작성 시각은 DB 세션의 KST 현재 시각을 사용하고 API에서는 offset 없는 ISO 8601 형식으로 반환한다.
- 게시글의 댓글 수는 별도 컬럼에 저장하지 않고 조회 시 유효한 댓글을 집계한다.
- 댓글 작성은 멱등성을 보장하지 않으며 동일 요청을 반복하면 별도의 댓글이 생성된다.
- 댓글 작성으로 인한 알림 생성은 별도 정책이 확정되기 전까지 처리하지 않는다.

## 커뮤니티 게시글 작성

- 커뮤니티 게시글 작성은 `POST /api/v1/community/posts` 엔드포인트를 사용한다.
- 요청은 게시글 정보와 이미지 파일을 함께 받을 수 있도록 `multipart/form-data` 형식을 사용한다.
- 로그인 구현 전에는 게시글 작성자를 사용자 id 1로 처리한다.
- `boardType`은 `BoardType` ENUM의 `FREE` 또는 `CERTIFICATION`만 허용한다.
- `boardType`이 누락되거나 허용되지 않은 값이면 공통 `400 INVALID_REQUEST`를 반환한다.
- `title`과 `content`는 필수값이며, 각각 앞뒤 공백을 제거한 값을 검증하고 저장한다.
- 공백 제거 결과 `title` 또는 `content`가 빈 문자열이면 공통 `400 INVALID_REQUEST`를 반환한다.
- `title`은 DB의 `post.title VARCHAR(150)`에 맞춰 최대 150자까지 허용한다.
- `title`이 150자를 초과하면 DB 저장 전에 공통 `400 INVALID_REQUEST`를 반환한다.
- `content`에는 별도의 최대 길이 검증을 적용하지 않는다.
- `images`는 선택값이며 전달되지 않으면 첨부 이미지가 없는 게시글을 생성한다.
- 이미지는 최대 5장까지 허용하고, 6장 이상이면 공통 `400 INVALID_REQUEST`를 반환한다.
- 이미지 파일 크기는 별도로 제한하지 않는다.
- 이미지 형식은 기존 이미지 API와 동일하게 전달된 Content-Type을 기준으로 검증한다.
- 허용하는 Content-Type은 `image/jpeg`, `image/jpg`, `image/png`, `image/webp`이다.
- 허용하지 않는 Content-Type이면 공통 `400 INVALID_REQUEST`를 반환한다.
- 이미지 파일의 실제 바이트 형식은 별도로 검사하지 않는다.
- 원본 파일명은 저장에 사용하지 않고 UUID로 새 파일명을 생성한다.
- 저장 확장자는 Content-Type에 따라 `jpg`, `png`, `webp` 중 하나로 결정한다.
- Blob은 `community_post/{userId}/{postId}/{uuid}.{extension}` 경로에 저장한다.
- Blob 경로의 최상위 prefix는 `AZURE_STORAGE_COMMUNITY_POST_PREFIX` 환경변수로 설정하며 기본값은 `community_post`이다.
- 게시글을 먼저 `post`에 추가하고 flush하여 `post.id`를 발급받은 후 이미지를 업로드한다.
- 새 게시글은 `status = ACTIVE`, `deleted_at = NULL`로 저장한다.
- `created_at`과 `updated_at`은 DB 기본값을 사용한다.
- 이미지 한 장마다 `post_media` 행을 하나씩 생성하고 Blob URL을 `post_image_url`에 저장한다.
- 이미지가 여러 장이면 요청으로 전달된 순서대로 업로드하고 `post_media`를 생성한다.
- 이미지 업로드 또는 DB 처리 중 오류가 발생하면 DB 트랜잭션은 롤백한다.
- DB 롤백 전에 Blob에 업로드된 이미지가 있더라도 해당 Blob은 별도로 삭제하지 않는다.
- 게시글 생성 성공 시 `201 Created`와 생성된 `postId`를 반환한다.
- 게시글 작성 시 `COMMUNITY_POST` 미션 진행도는 증가시키지 않으며 미션 연동에서 별도로 처리한다.
- 공통 `400 INVALID_REQUEST`, `500 INTERNAL_SERVER_ERROR` 외 별도 오류 응답은 정의하지 않는다.

## 커뮤니티 게시글 삭제

- 커뮤니티 게시글 삭제는 `DELETE /api/v1/community/posts/{postId}` 엔드포인트를 사용한다.
- `postId`는 1 이상의 정수만 허용하고, 올바르지 않은 값은 공통 `400 INVALID_REQUEST`로 처리한다.
- 로그인 구현 전에는 현재 사용자를 사용자 id 1로 처리한다.
- 게시글은 `post.id = postId`, `post.user_id = 현재 사용자 id`, `post.deleted_at IS NULL` 조건으로 조회한다.
- `post.status`가 `ACTIVE` 또는 `REPORTED`인 본인 게시글만 삭제할 수 있다.
- 다른 사용자가 작성한 게시글은 존재 여부를 노출하지 않고 `404 POST_NOT_FOUND`를 반환한다.
- 게시글이 존재하지 않거나 `status = DELETED`이거나 `deleted_at IS NOT NULL`이면 `404 POST_NOT_FOUND`를 반환한다.
- 삭제 대상 게시글은 `SELECT ... FOR UPDATE` 방식으로 잠가 동시에 들어온 삭제 요청 중 하나만 성공하게 한다.
- 삭제 시 게시글을 실제로 제거하지 않고 `post.status = DELETED`로 변경한다.
- `post.deleted_at`에는 삭제 시점의 한국시간 기준 offset 없는 datetime을 저장한다.
- `post.updated_at`은 ORM의 `onupdate=func.now()` 설정을 통해 갱신한다.
- 게시글과 연결된 `post_media`, `comment`, `post_like`, `comment_like` 데이터는 삭제하거나 변경하지 않는다.
- 게시글 이미지가 저장된 Azure Blob도 삭제하지 않는다.
- 처리 도중 오류가 발생하면 DB 트랜잭션을 롤백한다.
- 삭제 성공 시 `204 No Content`를 반환하고 응답 Body는 보내지 않는다.
- 공통 `400 INVALID_REQUEST`, `500 INTERNAL_SERVER_ERROR`를 제외한 이 API의 오류 응답은 `404 POST_NOT_FOUND`만 사용한다.
