# 커뮤니티 도메인 테스트 가이드

테스트 파일: `tests/test_community.py`
실행: `.venv\Scripts\python.exe -m pytest tests/test_community.py -q`
최종 실행 결과: 66 passed (2026-08-28)

DB는 `Mock(spec=Session)` 으로 대체하고 `app.dependency_overrides[get_db]` 로 주입합니다.
실제 MySQL에는 접속하지 않습니다.

커뮤니티 조회는 `db.execute` 1회로 (게시글, 작성자, 좋아요 수, 댓글 수, 좋아요 여부) 행을
조회하므로 `set_community_results()` 헬퍼로 결과 행만 지정합니다.
다음 페이지 존재 여부는 `size + 1` 건을 조회해 판단하므로, `hasNext` 검증 테스트는
요청한 `size` 보다 한 건 많은 행을 지정합니다.
`boardType`·`keyword` 조건은 Mock DB가 WHERE를 실행하지 않으므로 생성된 SQL로 검증합니다.

---

## 커뮤니티 조회 — `GET /api/v1/community/posts`

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_read_community_posts_returns_posts_with_author_and_counts | 게시글 2건 (기본 Query) | 200 + 응답 JSON 전체 일치, `pagination={0,20,false}` | PASS |
| 정상 변형 | test_read_community_posts_returns_is_mine_false_for_other_user_post | 작성자가 다른 사용자 | `isMine=false` | PASS |
| 정상 변형 | test_read_community_posts_returns_is_liked_false_when_not_liked | 현재 사용자 좋아요 없음 | `isLiked=false`, `likeCount=0` | PASS |
| 정상 변형 | test_read_community_posts_returns_null_author_profile_image_url | 작성자 프로필 이미지 없음 | `author.profileImageUrl=null` | PASS |
| 정상 변형 | test_read_community_posts_returns_empty_list_when_no_post | 게시글 0건 | 200 + `posts=[]`, `hasNext=false` | PASS |
| 정상 변형 | test_read_community_posts_returns_has_next_true_when_more_rows_exist | `size=2` 요청에 3건 조회 | 앞 2건만 반환, `hasNext=true` | PASS |
| 정상 변형 | test_read_community_posts_queries_all_board_types_by_default | `boardType` 생략 | 게시판 조건 없이 조회 | PASS |
| 정상 변형 | test_read_community_posts_filters_free_board | `boardType=FREE` | `post.board_type = 'FREE'` | PASS |
| 정상 변형 | test_read_community_posts_filters_certification_board | `boardType=CERTIFICATION` | `post.board_type = 'CERTIFICATION'` | PASS |
| 정상 변형 | test_read_community_posts_searches_title_by_keyword | `keyword=큐브` | `post.title LIKE '%큐브%'`, 내용은 검색 조건에서 제외 | PASS |
| 정상 변형 | test_read_community_posts_combines_board_type_and_keyword | `boardType=CERTIFICATION&keyword=큐브` | 두 조건을 AND로 결합 | PASS |
| 정상 변형 | test_read_community_posts_strips_keyword_before_matching | `keyword=(공백)큐브(공백)` | 앞뒤 공백 제거 후 검색 | PASS |
| 정상 변형 | test_read_community_posts_ignores_blank_keyword | `keyword=(공백 3칸)` | 200 + 제목 검색 조건 미적용 | PASS |
| 정상 변형 | test_read_community_posts_ignores_empty_keyword | `keyword=` (빈 문자열) | 200 + 제목 검색 조건 미적용 | PASS |
| 경계값 | test_read_community_posts_allows_single_character_keyword | `keyword=큐` (1글자) | 200 + `LIKE '%큐%'` | PASS |
| 정책 | test_read_community_posts_escapes_like_wildcards_in_keyword | `keyword=50%_` | `LIKE '%50\%\_%' ESCAPE '\'` 로 와일드카드를 일반 문자로 검색 | PASS |
| 정책 | test_read_community_posts_escapes_escape_character_in_keyword | `keyword=A\B` | `LIKE '%A\\B%' ESCAPE '\'` 로 이스케이프 문자 자체도 이스케이프 | PASS |
| 정책 | test_read_community_posts_excludes_deleted_posts | 조회 SQL 검증 | `status IN ('ACTIVE','REPORTED')`, `deleted_at IS NULL`, 작성자 조인 | PASS |
| 정책 | test_read_community_posts_orders_by_created_at_and_id_desc | `page=2&size=5` | `ORDER BY post.created_at DESC, post.id DESC`, `LIMIT 6`, `OFFSET 10` | PASS |
| 정책 | test_read_community_posts_counts_only_liked_rows_and_active_comments | 집계 서브쿼리 검증 | `post_like.is_liked IS true`, `comment.status='ACTIVE'`, `comment.deleted_at IS NULL` | PASS |
| 소유권 | test_read_community_posts_checks_current_user_like_for_is_liked | 좋아요 여부 서브쿼리 | `EXISTS`, `post_like.user_id = 1` | PASS |
| 경계값 | test_read_community_posts_allows_minimum_page_and_size | `page=0&size=1` | 200 + `pagination={0,1,false}` | PASS |
| 경계값 | test_read_community_posts_returns_400_when_page_is_negative | `page=-1` | 400 INVALID_REQUEST, 쿼리 미실행 | PASS |
| 경계값 | test_read_community_posts_returns_400_when_size_is_zero | `size=0` | 400 INVALID_REQUEST, 쿼리 미실행 | PASS |
| 요청 검증 | test_read_community_posts_returns_400_for_unsupported_board_type | `boardType=NOTICE` | 400 INVALID_REQUEST, 쿼리 미실행 | PASS |
| 문서 | test_read_community_posts_swagger_contract | OpenAPI 스키마 | 응답 코드 `{200, 400}`, Query `{boardType, keyword, page, size}`, tag `community` | PASS |

### 검증하지 않은 항목

- **정렬·페이지네이션의 실제 결과**는 Mock DB가 ORDER BY·LIMIT·OFFSET을 실행하지 않으므로
  생성된 SQL과 `hasNext` 계산 로직으로만 검증했습니다.
- **오류 응답**은 이 API가 정의하는 도메인 오류가 없어 공통 400 외에는 해당 없음입니다.
  `keyword`는 선택값이고 빈 문자열·공백도 400이 아니라 검색 조건 미적용으로 처리합니다.
- **영문 대소문자를 구분하지 않는 제목 검색**은 DB 콜레이션(`utf8mb4_unicode_ci`)이 결정하므로
  Mock DB로는 확인할 수 없어 `LIKE '%keyword%'` 조건이 생성되는지까지만 검증했습니다.
- **상태 전이·예외(rollback)**는 조회 전용이라 해당 없음이며, 정상 케이스에서
  `db.commit.assert_not_called()` 로 확인했습니다.
- **게시글 이미지(`post_media`)** 는 목록 응답에 포함하지 않는다는 규칙이라 조회 대상에서
  제외했고, 응답 스키마에 해당 필드가 없는 것으로 대신 확인했습니다.

---

## 커뮤니티 상세 조회 — `GET /api/v1/community/posts/{postId}`

`db.execute` 로 게시글 행을 조회하고, `db.scalars` 로 이미지 URL을, 다시 `db.execute` 로
댓글 행을 조회하므로 `set_post_detail_results()` 헬퍼로 세 결과를 순서대로 지정합니다.

```text
execute 1) 게시글+작성자+좋아요 수+좋아요 여부   2) 댓글+작성자+좋아요 수+좋아요 여부
scalars 1) 게시글 이미지 URL
```

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_read_community_post_detail_returns_post_images_and_comments | 이미지 1건 + 댓글 2건 | 200 + 응답 JSON 전체 일치 | PASS |
| 정상 변형 | test_read_community_post_detail_returns_empty_images_and_comments | 이미지·댓글 0건 | `imageUrls=[]`, `comments=[]`, `commentCount=0` | PASS |
| 정상 변형 | test_read_community_post_detail_returns_is_mine_false_for_other_user_post | 다른 사용자 게시글 + 본인 댓글 | 게시글 `isMine=false`, 댓글 `isMine=true` | PASS |
| 정상 변형 | test_read_community_post_detail_includes_reported_comment | 댓글 `status=REPORTED` | 결과에 포함, `commentCount=1` | PASS |
| 정상 변형 | test_read_community_post_detail_returns_null_author_fields | 작성자 닉네임·프로필 없음 | 둘 다 `null` | PASS |
| 오류 | test_read_community_post_detail_returns_404_when_post_is_unavailable | 게시글 조회 결과 없음 | 404 POST_NOT_FOUND, 이미지 쿼리 미실행 | PASS |
| 경계값 | test_read_community_post_detail_allows_minimum_post_id | `postId=1` | 200 | PASS |
| 경계값 | test_read_community_post_detail_returns_400_when_post_id_is_zero | `postId=0` | 400 INVALID_REQUEST, 쿼리 미실행 | PASS |
| 요청 검증 | test_read_community_post_detail_returns_400_when_post_id_is_not_a_number | `postId=abc` | 400 INVALID_REQUEST, 쿼리 미실행 | PASS |
| 정책 | test_read_community_post_detail_excludes_deleted_post | 게시글 SQL 검증 | `status IN ('ACTIVE','REPORTED')`, `deleted_at IS NULL`, 좋아요 집계·현재 사용자 조건 | PASS |
| 정책 | test_read_community_post_detail_orders_images_by_id_asc | 이미지 SQL 검증 | `post_media.post_id`, `ORDER BY post_media.id ASC` | PASS |
| 정책 | test_read_community_post_detail_orders_comments_by_created_at_asc | 댓글 SQL 검증 | `status IN ('ACTIVE','REPORTED')`, `deleted_at IS NULL`, `ORDER BY comment.created_at ASC, comment.id ASC` | PASS |
| 정책 | test_read_community_post_detail_counts_only_liked_comment_rows | 댓글 좋아요 서브쿼리 | `count(comment_like.id)`, `is_liked IS true`, `comment_like.user_id = 1` | PASS |
| 문서 | test_read_community_post_detail_swagger_contract | OpenAPI 스키마 | 응답 코드 `{200, 404}`, tag `community` | PASS |

### 검증하지 않은 항목

- **소유권**은 이 API의 접근 제한 조건이 아니므로(본인·타인 게시글 모두 조회 가능) 404 케이스
  없이 `isMine` 분기만 확인했습니다.
- **상태 전이·예외(rollback)**는 조회 전용이라 해당 없음이며, 정상 케이스에서
  `db.commit.assert_not_called()` 로 확인했습니다.
- **`commentCount` 가 실제 반환 댓글 수와 같다**는 규칙은 서비스가 조회한 댓글 목록의 길이를
  그대로 쓰므로 응답값 비교로 확인했습니다. 목록 조회의 `commentCount` 는 `ACTIVE` 만 세는
  별도 규칙이라 값이 다를 수 있습니다.
- **정렬 결과**는 Mock DB가 ORDER BY를 실행하지 않으므로 생성된 SQL로 검증했습니다.

---

## 커뮤니티 게시글 작성 — `POST /api/v1/community/posts`

Azure 업로드는 `patch("app.services.community.upload_community_post_image")` 로 대체합니다.
`collect_added_rows()` 헬퍼가 `db.add` 로 저장한 ORM 객체를 순서대로 모으고,
`db.flush` 시점에 게시글 id를 1로 부여해 이미지 Blob 경로 인자를 검증할 수 있게 합니다.

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_create_post_saves_post_without_image | 이미지 없이 FREE 게시글 | 201 + `{"postId": 1}`, `status=ACTIVE`·`deleted_at=None` 저장, 업로드 미호출, commit 1회 | PASS |
| 정상 변형 | test_create_post_uploads_images_in_request_order | 이미지 2장 | 요청 순서대로 업로드하고 `post_media` 2건 생성, Blob URL 저장 | PASS |
| 정상 변형 | test_create_post_saves_certification_board_type | `boardType=CERTIFICATION` | 해당 게시판으로 저장 | PASS |
| 정상 변형 | test_create_post_strips_title_and_content | 앞뒤 공백 포함 제목·내용 | 공백 제거한 값으로 저장 | PASS |
| 경계값 | test_create_post_allows_maximum_title_length | 제목 150자 | 201 | PASS |
| 경계값 | test_create_post_allows_title_that_fits_after_strip | 공백 포함 154자, 제거 후 150자 | 201 + 150자로 저장 | PASS |
| 경계값 | test_create_post_returns_400_when_title_is_too_long | 제목 151자 | 400 INVALID_REQUEST, 저장 없음 | PASS |
| 경계값 | test_create_post_allows_maximum_image_count | 이미지 5장 | 201 + 업로드 5회, `post_media` 5건 | PASS |
| 경계값 | test_create_post_returns_400_when_image_count_exceeds_limit | 이미지 6장 | 400 INVALID_REQUEST, 업로드·저장 없음 | PASS |
| 요청 검증 | test_create_post_returns_400_when_title_is_blank | 제목이 공백뿐 | 400 INVALID_REQUEST | PASS |
| 요청 검증 | test_create_post_returns_400_when_content_is_blank | 내용이 공백뿐 | 400 INVALID_REQUEST | PASS |
| 요청 검증 | test_create_post_returns_400_when_required_form_field_is_missing | `content` 필드 누락 | 400 INVALID_REQUEST | PASS |
| 요청 검증 | test_create_post_returns_400_for_unsupported_board_type | `boardType=NOTICE` | 400 INVALID_REQUEST | PASS |
| 요청 검증 | test_create_post_returns_400_for_unsupported_image_content_type | `image/gif` 업로드 | 400 INVALID_REQUEST, 업로드·저장 없음 | PASS |
| 예외 | test_create_post_rolls_back_when_image_upload_fails | Azure 업로드 실패 | 500 INTERNAL_SERVER_ERROR + rollback 1회, commit 없음 | PASS |
| 예외 | test_create_post_rolls_back_when_commit_fails | commit이 예외 발생 | 500 + rollback 1회 | PASS |
| 문서 | test_create_post_swagger_contract | OpenAPI 스키마 | 응답 코드 `{201, 400}`, `multipart/form-data`, 응답 `{postId}` | PASS |

### 검증하지 않은 항목

- **오류 응답**은 이 API가 정의하는 도메인 오류가 없어 공통 400·500 외에는 해당 없음입니다.
  소유권·상태 전이도 새로 만드는 리소스라 해당 없음입니다.
- **Blob 저장 경로(`community_post/{userId}/{postId}/{uuid}.{ext}`)와 UUID 파일명 생성**은
  `blob_storage.upload_community_post_image()` 의 책임이라 서비스 테스트에서는 호출 인자
  (`user_id`, `post_id`, `content_type`)까지만 확인했습니다.
- **파일의 실제 바이트 형식**은 규칙대로 검사하지 않으므로 테스트도 Content-Type만 다룹니다.
- **롤백 후 Blob 정리**는 규칙상 하지 않으므로 삭제 호출을 검증하지 않습니다.
- **`COMMUNITY_POST` 미션 진행도**는 이 API에서 증가시키지 않으므로 관련 검증이 없습니다.

---

## 커뮤니티 게시글 삭제 — `DELETE /api/v1/community/posts/{postId}`

`db.scalar` 로 잠금 조회한 게시글 객체의 상태 변화와 `db.commit` 호출만 확인합니다.

| 분류 | 테스트 함수 | 조건 | 기대 결과 | 결과 |
|---|---|---|---|---|
| 정상 | test_delete_post_soft_deletes_current_user_post | 본인 ACTIVE 게시글 | 204 + Body 없음, `status=DELETED`·`deleted_at` 설정(naive), commit 1회, 추가 저장 없음 | PASS |
| 정상 변형 | test_delete_post_deletes_reported_post | 본인 REPORTED 게시글 | 204 + `status=DELETED` | PASS |
| 오류 | test_delete_post_returns_404_when_post_is_unavailable | 조회 결과 없음 | 404 POST_NOT_FOUND, commit 없음 | PASS |
| 소유권 | test_delete_post_locks_only_current_user_visible_post | 조회 SQL 검증 | `post.user_id = 1`, `status IN ('ACTIVE','REPORTED')`, `deleted_at IS NULL`, `FOR UPDATE` | PASS |
| 경계값 | test_delete_post_allows_minimum_post_id | `postId=1` | 204 | PASS |
| 경계값 | test_delete_post_returns_400_when_post_id_is_zero | `postId=0` | 400 INVALID_REQUEST, 쿼리 미실행 | PASS |
| 요청 검증 | test_delete_post_returns_400_when_post_id_is_not_a_number | `postId=abc` | 400 INVALID_REQUEST, 쿼리 미실행 | PASS |
| 예외 | test_delete_post_rolls_back_when_commit_fails | commit이 예외 발생 | 500 + rollback 1회 | PASS |
| 문서 | test_delete_post_swagger_contract | OpenAPI 스키마 | 응답 코드 `{204, 404}`, 요청 Body 없음 | PASS |

### 검증하지 않은 항목

- **없는 게시글 / 남의 게시글 / 이미 삭제된 게시글**은 Mock DB로 구분할 수 없어 모두 같은 404로
  처리되는 것만 확인하고, 조회 조건은 생성된 SQL로 검증했습니다.
- **동시 삭제 요청 중 하나만 성공**하는 동작은 실제 트랜잭션이 필요해 검증할 수 없고,
  `FOR UPDATE` 가 SQL에 포함되는지만 확인했습니다.
- **`post_media`·`comment`·`post_like`·`comment_like` 와 Blob을 건드리지 않는다**는 규칙은
  서비스가 이들을 조회·수정하지 않으므로 `db.add` 미호출로 대신 확인했습니다.
- **`updated_at` 갱신**은 ORM의 `onupdate=func.now()` 가 DB에서 처리하므로 검증 대상에서
  제외했습니다.
