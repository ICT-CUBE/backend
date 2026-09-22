"""마이페이지 도메인 API 테스트."""

from datetime import datetime
from unittest.mock import Mock

from sqlalchemy.orm import Session

from app.community.models import Post
from app.core.enums import BoardType, LoginProvider, PostStatus, UserStatus
from app.core.tests.conftest import api_client
from app.main import app
from app.user.models import User


def read_my_page_request(db: Mock, *, raise_server_exceptions: bool = True):
    with api_client(db, raise_server_exceptions=raise_server_exceptions) as client:
        return client.get("/api/v1/users/me")


def my_page_user(
    *,
    nickname: str | None = "DORI",
    profile_character_img_url: str | None = (
        "https://cdn.example.com/profile_image/profile_001.png"
    ),
) -> User:
    return User(
        id=1,
        email="dodorori@gmail.com",
        login_provider=LoginProvider.EMAIL,
        nickname=nickname,
        profile_character_img_url=profile_character_img_url,
        status=UserStatus.ACTIVE,
        deleted_at=None,
    )


def set_my_page_results(
    db: Mock,
    *,
    user: User | None,
    written_post_count: int | None = 4,
    commented_post_count: int | None = 2,
) -> None:
    """서비스가 db.scalar 를 호출하는 순서대로 결과를 지정합니다."""
    db.scalar.side_effect = [user, written_post_count, commented_post_count]


def compiled_query(call) -> str:
    return str(call.args[0].compile(compile_kwargs={"literal_binds": True}))


def test_read_my_page_returns_profile_and_activity_counts() -> None:
    db = Mock(spec=Session)
    set_my_page_results(db, user=my_page_user())

    response = read_my_page_request(db)

    assert response.status_code == 200
    assert response.json() == {
        "user": {
            "nickname": "DORI",
            "email": "dodorori@gmail.com",
            "profileCharacterImgUrl": (
                "https://cdn.example.com/profile_image/profile_001.png"
            ),
        },
        "activity": {
            "writtenPostCount": 4,
            "commentedPostCount": 2,
        },
    }
    db.commit.assert_not_called()
    db.add.assert_not_called()


def test_read_my_page_returns_null_nickname_and_profile_image() -> None:
    db = Mock(spec=Session)
    set_my_page_results(
        db,
        user=my_page_user(nickname=None, profile_character_img_url=None),
    )

    response = read_my_page_request(db)

    assert response.status_code == 200
    assert response.json()["user"]["nickname"] is None
    assert response.json()["user"]["profileCharacterImgUrl"] is None


def test_read_my_page_returns_zero_counts_when_no_activity() -> None:
    db = Mock(spec=Session)
    set_my_page_results(
        db,
        user=my_page_user(),
        written_post_count=0,
        commented_post_count=0,
    )

    response = read_my_page_request(db)

    assert response.status_code == 200
    assert response.json()["activity"] == {
        "writtenPostCount": 0,
        "commentedPostCount": 0,
    }


def test_read_my_page_returns_zero_counts_when_count_is_none() -> None:
    db = Mock(spec=Session)
    set_my_page_results(
        db,
        user=my_page_user(),
        written_post_count=None,
        commented_post_count=None,
    )

    response = read_my_page_request(db)

    assert response.status_code == 200
    assert response.json()["activity"] == {
        "writtenPostCount": 0,
        "commentedPostCount": 0,
    }


def test_read_my_page_queries_only_current_user_profile() -> None:
    db = Mock(spec=Session)
    set_my_page_results(db, user=my_page_user())

    read_my_page_request(db)

    assert '"user".id = 1' in compiled_query(db.scalar.call_args_list[0])


def test_read_my_page_counts_only_visible_posts_of_current_user() -> None:
    db = Mock(spec=Session)
    set_my_page_results(db, user=my_page_user())

    read_my_page_request(db)

    query = compiled_query(db.scalar.call_args_list[1])
    assert "count(post.id)" in query
    assert "post.user_id = 1" in query
    assert "post.status IN ('ACTIVE', 'REPORTED')" in query
    assert "post.deleted_at IS NULL" in query


def test_read_my_page_counts_distinct_posts_of_current_user_comments() -> None:
    db = Mock(spec=Session)
    set_my_page_results(db, user=my_page_user())

    read_my_page_request(db)

    query = compiled_query(db.scalar.call_args_list[2])
    assert "count(DISTINCT comment.post_id)" in query
    assert "JOIN post ON post.id = comment.post_id" in query
    assert "comment.user_id = 1" in query
    assert "comment.status IN ('ACTIVE', 'REPORTED')" in query
    assert "comment.deleted_at IS NULL" in query
    assert "post.status IN ('ACTIVE', 'REPORTED')" in query
    assert "post.deleted_at IS NULL" in query


def test_read_my_page_returns_500_when_user_row_is_missing() -> None:
    db = Mock(spec=Session)
    set_my_page_results(db, user=None)

    response = read_my_page_request(db, raise_server_exceptions=False)

    assert response.status_code == 500
    assert response.json() == {
        "code": "INTERNAL_SERVER_ERROR",
        "message": "서버 내부 오류가 발생했습니다.",
    }


def test_read_my_page_swagger_contract() -> None:
    operation = app.openapi()["paths"]["/api/v1/users/me"]["get"]

    assert set(operation["responses"]) == {"200"}
    assert operation["tags"] == ["mypage"]
    assert operation["security"] == [{"HTTPBearer": []}]


# --- 사용자 프로필 수정: PATCH /api/v1/users/me/profile ---

INVALID_REQUEST_RESPONSE = {
    "code": "INVALID_REQUEST",
    "message": "요청값이 올바르지 않습니다.",
}
PROFILE_IMAGE_URL_PREFIX = (
    "https://haniumstorage.blob.core.windows.net/hanium/profile_image"
)


def update_profile_request(
    db: Mock,
    *,
    body: dict | None = None,
    raise_server_exceptions: bool = True,
):
    with api_client(db, raise_server_exceptions=raise_server_exceptions) as client:
        return client.patch(
            "/api/v1/users/me/profile",
            json=(
                body
                if body is not None
                else {"nickname": "DORI", "profileCharacterCode": "profile_001"}
            ),
        )


def test_update_profile_saves_nickname_and_profile_image_url() -> None:
    db = Mock(spec=Session)
    user = my_page_user(
        nickname="블링크",
        profile_character_img_url=f"{PROFILE_IMAGE_URL_PREFIX}/profile_003.png",
    )
    db.scalar.return_value = user

    response = update_profile_request(
        db,
        body={"nickname": "DORI", "profileCharacterCode": "profile_001"},
    )

    assert response.status_code == 204
    assert response.content == b""
    assert user.nickname == "DORI"
    assert user.profile_character_img_url == (
        f"{PROFILE_IMAGE_URL_PREFIX}/profile_001.png"
    )
    db.add.assert_not_called()
    db.commit.assert_called_once()


def test_update_profile_saves_profile_002_image_url() -> None:
    db = Mock(spec=Session)
    user = my_page_user()
    db.scalar.return_value = user

    response = update_profile_request(
        db,
        body={"nickname": "DORI", "profileCharacterCode": "profile_002"},
    )

    assert response.status_code == 204
    assert user.profile_character_img_url == (
        f"{PROFILE_IMAGE_URL_PREFIX}/profile_002.png"
    )


def test_update_profile_saves_profile_003_image_url() -> None:
    db = Mock(spec=Session)
    user = my_page_user()
    db.scalar.return_value = user

    response = update_profile_request(
        db,
        body={"nickname": "DORI", "profileCharacterCode": "profile_003"},
    )

    assert response.status_code == 204
    assert user.profile_character_img_url == (
        f"{PROFILE_IMAGE_URL_PREFIX}/profile_003.png"
    )


def test_update_profile_strips_nickname_before_saving() -> None:
    db = Mock(spec=Session)
    user = my_page_user()
    db.scalar.return_value = user

    response = update_profile_request(
        db,
        body={"nickname": "  도리 DORI!  ", "profileCharacterCode": "profile_001"},
    )

    assert response.status_code == 204
    assert user.nickname == "도리 DORI!"


def test_update_profile_accepts_same_values_as_current_profile() -> None:
    db = Mock(spec=Session)
    user = my_page_user(
        nickname="DORI",
        profile_character_img_url=f"{PROFILE_IMAGE_URL_PREFIX}/profile_001.png",
    )
    db.scalar.return_value = user

    response = update_profile_request(db)

    assert response.status_code == 204
    assert user.nickname == "DORI"
    db.commit.assert_called_once()


def test_update_profile_saves_values_when_profile_was_null() -> None:
    db = Mock(spec=Session)
    user = my_page_user(nickname=None, profile_character_img_url=None)
    db.scalar.return_value = user

    response = update_profile_request(db)

    assert response.status_code == 204
    assert user.nickname == "DORI"
    assert user.profile_character_img_url == (
        f"{PROFILE_IMAGE_URL_PREFIX}/profile_001.png"
    )


def test_update_profile_queries_only_current_user() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = my_page_user()

    update_profile_request(db)

    query = compiled_query(db.scalar.call_args)
    assert '"user".id = 1' in query
    # 닉네임 중복을 허용하므로 다른 사용자의 닉네임을 조회하지 않습니다.
    assert "nickname" not in query.split("WHERE", 1)[1]
    assert db.scalar.call_count == 1


def test_update_profile_allows_minimum_nickname_length() -> None:
    db = Mock(spec=Session)
    user = my_page_user()
    db.scalar.return_value = user

    response = update_profile_request(
        db,
        body={"nickname": "도", "profileCharacterCode": "profile_001"},
    )

    assert response.status_code == 204
    assert user.nickname == "도"


def test_update_profile_allows_maximum_nickname_length() -> None:
    db = Mock(spec=Session)
    user = my_page_user()
    db.scalar.return_value = user

    response = update_profile_request(
        db,
        body={"nickname": "가" * 20, "profileCharacterCode": "profile_001"},
    )

    assert response.status_code == 204
    assert user.nickname == "가" * 20


def test_update_profile_allows_nickname_that_fits_after_strip() -> None:
    db = Mock(spec=Session)
    user = my_page_user()
    db.scalar.return_value = user
    nickname = "가" * 20

    response = update_profile_request(
        db,
        body={"nickname": f"  {nickname}  ", "profileCharacterCode": "profile_001"},
    )

    assert response.status_code == 204
    assert user.nickname == nickname


def test_update_profile_returns_400_when_nickname_is_too_long() -> None:
    db = Mock(spec=Session)

    response = update_profile_request(
        db,
        body={"nickname": "가" * 21, "profileCharacterCode": "profile_001"},
    )

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()
    db.commit.assert_not_called()


def test_update_profile_returns_400_when_nickname_is_blank() -> None:
    db = Mock(spec=Session)

    response = update_profile_request(
        db,
        body={"nickname": "   ", "profileCharacterCode": "profile_001"},
    )

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_update_profile_returns_400_when_nickname_is_empty() -> None:
    db = Mock(spec=Session)

    response = update_profile_request(
        db,
        body={"nickname": "", "profileCharacterCode": "profile_001"},
    )

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_update_profile_returns_400_when_nickname_is_missing() -> None:
    db = Mock(spec=Session)

    response = update_profile_request(
        db,
        body={"profileCharacterCode": "profile_001"},
    )

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_update_profile_returns_400_when_profile_character_code_is_missing() -> None:
    db = Mock(spec=Session)

    response = update_profile_request(db, body={"nickname": "DORI"})

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_update_profile_returns_400_for_unsupported_profile_character_code() -> None:
    db = Mock(spec=Session)

    response = update_profile_request(
        db,
        body={"nickname": "DORI", "profileCharacterCode": "profile_004"},
    )

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_update_profile_returns_400_when_nickname_is_not_string() -> None:
    db = Mock(spec=Session)

    response = update_profile_request(
        db,
        body={"nickname": 1234, "profileCharacterCode": "profile_001"},
    )

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_update_profile_returns_500_when_user_row_is_missing() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = update_profile_request(db, raise_server_exceptions=False)

    assert response.status_code == 500
    assert response.json() == {
        "code": "INTERNAL_SERVER_ERROR",
        "message": "서버 내부 오류가 발생했습니다.",
    }
    db.commit.assert_not_called()


def test_update_profile_rolls_back_when_commit_fails() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = my_page_user()
    db.commit.side_effect = RuntimeError("db failed")

    response = update_profile_request(db, raise_server_exceptions=False)

    assert response.status_code == 500
    db.rollback.assert_called_once()


def test_update_profile_swagger_contract() -> None:
    operation = app.openapi()["paths"]["/api/v1/users/me/profile"]["patch"]

    assert set(operation["responses"]) == {"204", "400"}
    assert "requestBody" in operation
    assert operation["tags"] == ["mypage"]
    assert operation["security"] == [{"HTTPBearer": []}]


# --- 내가 쓴 글 조회: GET /api/v1/users/me/posts ---


def read_my_posts_request(db: Mock, *, params: dict | None = None):
    with api_client(db) as client:
        return client.get("/api/v1/users/me/posts", params=params)


def my_post(
    *,
    post_id: int,
    user_id: int = 1,
    board_type: BoardType = BoardType.FREE,
    status: PostStatus = PostStatus.ACTIVE,
    created_at: str = "2026-09-22T09:30:00",
) -> Post:
    return Post(
        id=post_id,
        user_id=user_id,
        board_type=board_type,
        title=f"게시글 {post_id}",
        content=f"게시글 {post_id} 전체 내용입니다.",
        status=status,
        created_at=datetime.fromisoformat(created_at),
        deleted_at=None,
    )


def my_post_row(
    post: Post,
    *,
    author_nickname: str | None = "dodoriruru7",
    like_count: int = 0,
    comment_count: int = 0,
    is_liked: bool = False,
) -> tuple:
    return (post, author_nickname, like_count, comment_count, is_liked)


def set_my_posts_results(db: Mock, *, rows: list | None = None) -> None:
    db.execute.return_value.all.return_value = rows or []


def test_read_my_posts_returns_posts_with_counts() -> None:
    db = Mock(spec=Session)
    set_my_posts_results(
        db,
        rows=[
            my_post_row(
                my_post(post_id=15),
                like_count=2111,
                comment_count=34,
                is_liked=False,
            ),
            my_post_row(
                my_post(
                    post_id=12,
                    board_type=BoardType.CERTIFICATION,
                    created_at="2026-09-21T21:10:00",
                ),
                like_count=1523,
                comment_count=20,
                is_liked=True,
            ),
        ],
    )

    response = read_my_posts_request(db)

    assert response.status_code == 200
    assert response.json() == {
        "posts": [
            {
                "id": 15,
                "boardType": "FREE",
                "title": "게시글 15",
                "content": "게시글 15 전체 내용입니다.",
                "authorNickname": "dodoriruru7",
                "createdAt": "2026-09-22T09:30:00",
                "likeCount": 2111,
                "commentCount": 34,
                "isLiked": False,
            },
            {
                "id": 12,
                "boardType": "CERTIFICATION",
                "title": "게시글 12",
                "content": "게시글 12 전체 내용입니다.",
                "authorNickname": "dodoriruru7",
                "createdAt": "2026-09-21T21:10:00",
                "likeCount": 1523,
                "commentCount": 20,
                "isLiked": True,
            },
        ],
        "pagination": {"page": 0, "size": 20, "hasNext": False},
    }
    db.commit.assert_not_called()
    db.add.assert_not_called()


def test_read_my_posts_returns_empty_list_when_no_post() -> None:
    db = Mock(spec=Session)
    set_my_posts_results(db, rows=[])

    response = read_my_posts_request(db)

    assert response.status_code == 200
    assert response.json() == {
        "posts": [],
        "pagination": {"page": 0, "size": 20, "hasNext": False},
    }


def test_read_my_posts_returns_has_next_true_when_more_rows_exist() -> None:
    db = Mock(spec=Session)
    set_my_posts_results(
        db,
        rows=[my_post_row(my_post(post_id=post_id)) for post_id in (3, 2, 1)],
    )

    response = read_my_posts_request(db, params={"page": 1, "size": 2})

    assert response.status_code == 200
    body = response.json()
    assert [post["id"] for post in body["posts"]] == [3, 2]
    assert body["pagination"] == {"page": 1, "size": 2, "hasNext": True}


def test_read_my_posts_returns_null_author_nickname() -> None:
    db = Mock(spec=Session)
    set_my_posts_results(
        db,
        rows=[my_post_row(my_post(post_id=1), author_nickname=None)],
    )

    response = read_my_posts_request(db)

    assert response.status_code == 200
    assert response.json()["posts"][0]["authorNickname"] is None


def test_read_my_posts_includes_reported_post() -> None:
    db = Mock(spec=Session)
    set_my_posts_results(
        db,
        rows=[my_post_row(my_post(post_id=1, status=PostStatus.REPORTED))],
    )

    response = read_my_posts_request(db)

    assert response.status_code == 200
    assert [post["id"] for post in response.json()["posts"]] == [1]


def test_read_my_posts_returns_full_content_without_truncation() -> None:
    db = Mock(spec=Session)
    post = my_post(post_id=1)
    post.content = "가" * 3000
    set_my_posts_results(db, rows=[my_post_row(post)])

    response = read_my_posts_request(db)

    assert response.status_code == 200
    assert response.json()["posts"][0]["content"] == "가" * 3000


def test_read_my_posts_queries_only_visible_posts_of_current_user() -> None:
    db = Mock(spec=Session)
    set_my_posts_results(db)

    read_my_posts_request(db)

    query = compiled_query(db.execute.call_args)
    where_clause = query.rsplit("WHERE", 1)[1]
    assert "post.user_id = 1" in where_clause
    assert "post.status IN ('ACTIVE', 'REPORTED')" in where_clause
    assert "post.deleted_at IS NULL" in where_clause
    # 게시판 필터와 검색을 제공하지 않습니다.
    assert "post.board_type" not in where_clause
    assert "LIKE" not in query


def test_read_my_posts_counts_liked_rows_and_active_comments() -> None:
    db = Mock(spec=Session)
    set_my_posts_results(db)

    read_my_posts_request(db)

    query = compiled_query(db.execute.call_args)
    assert "count(post_like.id)" in query
    assert "post_like.is_liked IS true" in query
    assert "post_like.user_id = 1" in query
    assert "count(comment.id)" in query
    assert "comment.status = 'ACTIVE'" in query
    assert "comment.deleted_at IS NULL" in query


def test_read_my_posts_orders_by_created_at_and_id_desc() -> None:
    db = Mock(spec=Session)
    set_my_posts_results(db)

    read_my_posts_request(db, params={"page": 2, "size": 5})

    query = compiled_query(db.execute.call_args)
    assert "ORDER BY post.created_at DESC, post.id DESC" in query
    assert "LIMIT 6" in query
    assert "OFFSET 10" in query


def test_read_my_posts_allows_minimum_page_and_size() -> None:
    db = Mock(spec=Session)
    set_my_posts_results(db)

    response = read_my_posts_request(db, params={"page": 0, "size": 1})

    assert response.status_code == 200
    assert response.json()["pagination"] == {
        "page": 0,
        "size": 1,
        "hasNext": False,
    }


def test_read_my_posts_returns_400_when_page_is_negative() -> None:
    db = Mock(spec=Session)

    response = read_my_posts_request(db, params={"page": -1})

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.execute.assert_not_called()


def test_read_my_posts_returns_400_when_size_is_zero() -> None:
    db = Mock(spec=Session)

    response = read_my_posts_request(db, params={"size": 0})

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.execute.assert_not_called()


def test_read_my_posts_returns_400_when_page_is_not_number() -> None:
    db = Mock(spec=Session)

    response = read_my_posts_request(db, params={"page": "abc"})

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.execute.assert_not_called()


def test_read_my_posts_swagger_contract() -> None:
    operation = app.openapi()["paths"]["/api/v1/users/me/posts"]["get"]

    assert set(operation["responses"]) == {"200", "400"}
    assert {parameter["name"] for parameter in operation["parameters"]} == {
        "page",
        "size",
    }
    assert operation["tags"] == ["mypage"]
    assert operation["security"] == [{"HTTPBearer": []}]


# --- 댓글 단 글 조회: GET /api/v1/users/me/commented-posts ---


def read_my_commented_posts_request(db: Mock, *, params: dict | None = None):
    with api_client(db) as client:
        return client.get("/api/v1/users/me/commented-posts", params=params)


def test_read_my_commented_posts_returns_posts_with_counts() -> None:
    db = Mock(spec=Session)
    set_my_posts_results(
        db,
        rows=[
            my_post_row(
                my_post(post_id=21, user_id=2, created_at="2026-09-22T10:15:00"),
                author_nickname="fandomlove_12",
                like_count=987,
                comment_count=15,
                is_liked=True,
            ),
            my_post_row(
                my_post(
                    post_id=18,
                    user_id=3,
                    board_type=BoardType.CERTIFICATION,
                    created_at="2026-09-21T18:20:00",
                ),
                author_nickname="blink_02",
                like_count=152,
                comment_count=8,
                is_liked=False,
            ),
        ],
    )

    response = read_my_commented_posts_request(db)

    assert response.status_code == 200
    assert response.json() == {
        "posts": [
            {
                "id": 21,
                "boardType": "FREE",
                "title": "게시글 21",
                "content": "게시글 21 전체 내용입니다.",
                "authorNickname": "fandomlove_12",
                "createdAt": "2026-09-22T10:15:00",
                "likeCount": 987,
                "commentCount": 15,
                "isLiked": True,
            },
            {
                "id": 18,
                "boardType": "CERTIFICATION",
                "title": "게시글 18",
                "content": "게시글 18 전체 내용입니다.",
                "authorNickname": "blink_02",
                "createdAt": "2026-09-21T18:20:00",
                "likeCount": 152,
                "commentCount": 8,
                "isLiked": False,
            },
        ],
        "pagination": {"page": 0, "size": 20, "hasNext": False},
    }
    db.commit.assert_not_called()
    db.add.assert_not_called()


def test_read_my_commented_posts_returns_empty_list_when_no_comment() -> None:
    db = Mock(spec=Session)
    set_my_posts_results(db, rows=[])

    response = read_my_commented_posts_request(db)

    assert response.status_code == 200
    assert response.json() == {
        "posts": [],
        "pagination": {"page": 0, "size": 20, "hasNext": False},
    }


def test_read_my_commented_posts_returns_has_next_true_when_more_rows_exist() -> None:
    db = Mock(spec=Session)
    set_my_posts_results(
        db,
        rows=[
            my_post_row(my_post(post_id=post_id, user_id=2))
            for post_id in (3, 2, 1)
        ],
    )

    response = read_my_commented_posts_request(db, params={"page": 1, "size": 2})

    assert response.status_code == 200
    body = response.json()
    assert [post["id"] for post in body["posts"]] == [3, 2]
    assert body["pagination"] == {"page": 1, "size": 2, "hasNext": True}


def test_read_my_commented_posts_includes_own_and_reported_posts() -> None:
    db = Mock(spec=Session)
    set_my_posts_results(
        db,
        rows=[
            my_post_row(my_post(post_id=2, user_id=1)),
            my_post_row(my_post(post_id=1, user_id=2, status=PostStatus.REPORTED)),
        ],
    )

    response = read_my_commented_posts_request(db)

    assert response.status_code == 200
    assert [post["id"] for post in response.json()["posts"]] == [2, 1]


def test_read_my_commented_posts_returns_null_author_nickname() -> None:
    db = Mock(spec=Session)
    set_my_posts_results(
        db,
        rows=[my_post_row(my_post(post_id=1, user_id=2), author_nickname=None)],
    )

    response = read_my_commented_posts_request(db)

    assert response.status_code == 200
    assert response.json()["posts"][0]["authorNickname"] is None


def test_read_my_commented_posts_filters_by_my_visible_comments_with_exists() -> None:
    db = Mock(spec=Session)
    set_my_posts_results(db)

    read_my_commented_posts_request(db)

    query = compiled_query(db.execute.call_args)
    # SELECT 목록의 집계 서브쿼리를 빼고 바깥 FROM·WHERE 절만 확인합니다.
    where_clause = query.split('FROM post JOIN "user"', 1)[1]
    assert "post.status IN ('ACTIVE', 'REPORTED')" in where_clause
    assert "post.deleted_at IS NULL" in where_clause
    assert "EXISTS (SELECT comment.id" in where_clause
    assert "comment.user_id = 1" in where_clause
    assert "comment.status IN ('ACTIVE', 'REPORTED')" in where_clause
    assert "comment.deleted_at IS NULL" in where_clause
    # 남의 게시글도 포함하므로 게시글 작성자로 거르지 않습니다.
    assert "post.user_id = 1" not in where_clause
    # 댓글을 JOIN하면 게시글이 중복되므로 EXISTS로만 거릅니다.
    assert "JOIN comment" not in query
    assert "post.board_type" not in where_clause
    assert "LIKE" not in query


def test_read_my_commented_posts_counts_all_active_comments_of_post() -> None:
    db = Mock(spec=Session)
    set_my_posts_results(db)

    read_my_commented_posts_request(db)

    query = compiled_query(db.execute.call_args)
    select_clause = query.split('FROM post JOIN "user"', 1)[0]
    assert "count(post_like.id)" in select_clause
    assert "post_like.is_liked IS true" in select_clause
    assert "post_like.user_id = 1" in select_clause
    assert "count(comment.id)" in select_clause
    assert "comment.status = 'ACTIVE'" in select_clause
    # 댓글 수는 내 댓글이 아니라 게시글 전체 유효 댓글 수입니다.
    assert "comment.user_id" not in select_clause


def test_read_my_commented_posts_orders_by_post_created_at_and_id_desc() -> None:
    db = Mock(spec=Session)
    set_my_posts_results(db)

    read_my_commented_posts_request(db, params={"page": 2, "size": 5})

    query = compiled_query(db.execute.call_args)
    assert "ORDER BY post.created_at DESC, post.id DESC" in query
    assert "comment.created_at" not in query
    assert "LIMIT 6" in query
    assert "OFFSET 10" in query


def test_read_my_commented_posts_allows_minimum_page_and_size() -> None:
    db = Mock(spec=Session)
    set_my_posts_results(db)

    response = read_my_commented_posts_request(db, params={"page": 0, "size": 1})

    assert response.status_code == 200
    assert response.json()["pagination"] == {
        "page": 0,
        "size": 1,
        "hasNext": False,
    }


def test_read_my_commented_posts_returns_400_when_page_is_negative() -> None:
    db = Mock(spec=Session)

    response = read_my_commented_posts_request(db, params={"page": -1})

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.execute.assert_not_called()


def test_read_my_commented_posts_returns_400_when_size_is_zero() -> None:
    db = Mock(spec=Session)

    response = read_my_commented_posts_request(db, params={"size": 0})

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.execute.assert_not_called()


def test_read_my_commented_posts_returns_400_when_size_is_not_number() -> None:
    db = Mock(spec=Session)

    response = read_my_commented_posts_request(db, params={"size": "abc"})

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.execute.assert_not_called()


def test_read_my_commented_posts_swagger_contract() -> None:
    operation = app.openapi()["paths"]["/api/v1/users/me/commented-posts"]["get"]

    assert set(operation["responses"]) == {"200", "400"}
    assert {parameter["name"] for parameter in operation["parameters"]} == {
        "page",
        "size",
    }
    assert operation["tags"] == ["mypage"]
    assert operation["security"] == [{"HTTPBearer": []}]
