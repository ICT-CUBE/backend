"""커뮤니티 도메인 API 테스트."""

from collections.abc import Iterator
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.community.models import Comment, CommentLike, Post, PostLike, PostMedia
from app.core.enums import (
    BoardType,
    CommentStatus,
    MissionTargetAction,
    PostStatus,
)
from app.core.tests.conftest import api_client
from app.main import app
from app.user.models import User


@pytest.fixture(autouse=True)
def mission_progress() -> Iterator[Mock]:
    """미션 진행도 로직은 app/mission/tests 에서 검증하고 여기서는 호출만 기록합니다."""
    with patch("app.community.service.increase_mission_progress") as mocked:
        yield mocked

INVALID_REQUEST_RESPONSE = {
    "code": "INVALID_REQUEST",
    "message": "요청값이 올바르지 않습니다.",
}


def read_community_posts_request(
    db: Mock,
    *,
    board_type: str | None = None,
    keyword: str | None = None,
    page: int | str | None = None,
    size: int | str | None = None,
):
    params: dict[str, int | str] = {}
    if board_type is not None:
        params["boardType"] = board_type
    if keyword is not None:
        params["keyword"] = keyword
    if page is not None:
        params["page"] = page
    if size is not None:
        params["size"] = size
    with api_client(db) as client:
        return client.get("/api/v1/community/posts", params=params)


def community_post(
    *,
    post_id: int,
    user_id: int = 1,
    board_type: BoardType = BoardType.FREE,
    title: str = "Ruby 큐브 26번 등록했어요",
    content: str = "앨범 나오자마자 큐브 등록했습니다.",
    created_at: str = "2026-08-28T20:20:00",
) -> Post:
    return Post(
        id=post_id,
        user_id=user_id,
        board_type=board_type,
        title=title,
        content=content,
        status=PostStatus.ACTIVE,
        created_at=datetime.fromisoformat(created_at),
        deleted_at=None,
    )


def community_author(
    *,
    user_id: int = 1,
    nickname: str | None = "블링크",
    profile_character_img_url: str | None = "https://cdn.example.com/profile_002.png",
) -> User:
    return User(
        id=user_id,
        nickname=nickname,
        profile_character_img_url=profile_character_img_url,
    )


def community_comment(
    *,
    comment_id: int,
    post_id: int = 1,
    user_id: int = 1,
    status: CommentStatus = CommentStatus.ACTIVE,
) -> Comment:
    return Comment(
        id=comment_id,
        post_id=post_id,
        user_id=user_id,
        content="큐브 디자인이 정말 예쁘네요.",
        status=status,
        created_at=datetime.fromisoformat("2026-09-20T18:30:00"),
        deleted_at=None,
    )


def community_post_row(
    *,
    post_id: int,
    user_id: int = 1,
    board_type: BoardType = BoardType.FREE,
    created_at: str = "2026-08-28T20:20:00",
    like_count: int = 1,
    comment_count: int = 1,
    is_liked: bool = True,
    nickname: str | None = "블링크",
    profile_character_img_url: str | None = "https://cdn.example.com/profile_002.png",
):
    """조회가 반환하는 (게시글, 작성자, 좋아요 수, 댓글 수, 좋아요 여부) 행을 만듭니다."""
    return (
        community_post(
            post_id=post_id,
            user_id=user_id,
            board_type=board_type,
            created_at=created_at,
        ),
        community_author(
            user_id=user_id,
            nickname=nickname,
            profile_character_img_url=profile_character_img_url,
        ),
        like_count,
        comment_count,
        is_liked,
    )


def set_community_results(db: Mock, *, rows: list | None = None) -> None:
    """서비스가 db.execute 로 조회한 결과를 지정합니다."""
    db.execute.return_value.all.return_value = rows or []


def compiled_query(call) -> str:
    return str(call.args[0].compile(compile_kwargs={"literal_binds": True}))


def test_read_community_posts_returns_posts_with_author_and_counts() -> None:
    db = Mock(spec=Session)
    set_community_results(
        db,
        rows=[
            community_post_row(
                post_id=2,
                board_type=BoardType.CERTIFICATION,
                created_at="2026-08-28T20:30:00",
                like_count=0,
                comment_count=1,
                is_liked=False,
            ),
            community_post_row(post_id=1),
        ],
    )

    response = read_community_posts_request(db)

    assert response.status_code == 200
    assert response.json() == {
        "posts": [
            {
                "id": 2,
                "boardType": "CERTIFICATION",
                "title": "Ruby 큐브 26번 등록했어요",
                "content": "앨범 나오자마자 큐브 등록했습니다.",
                "author": {
                    "id": 1,
                    "nickname": "블링크",
                    "profileImageUrl": "https://cdn.example.com/profile_002.png",
                },
                "createdAt": "2026-08-28T20:30:00",
                "likeCount": 0,
                "commentCount": 1,
                "isLiked": False,
                "isMine": True,
            },
            {
                "id": 1,
                "boardType": "FREE",
                "title": "Ruby 큐브 26번 등록했어요",
                "content": "앨범 나오자마자 큐브 등록했습니다.",
                "author": {
                    "id": 1,
                    "nickname": "블링크",
                    "profileImageUrl": "https://cdn.example.com/profile_002.png",
                },
                "createdAt": "2026-08-28T20:20:00",
                "likeCount": 1,
                "commentCount": 1,
                "isLiked": True,
                "isMine": True,
            },
        ],
        "pagination": {"page": 0, "size": 20, "hasNext": False},
    }
    db.commit.assert_not_called()


def test_read_community_posts_returns_is_mine_false_for_other_user_post() -> None:
    db = Mock(spec=Session)
    set_community_results(db, rows=[community_post_row(post_id=1, user_id=2)])

    response = read_community_posts_request(db)

    assert response.status_code == 200
    assert response.json()["posts"][0]["isMine"] is False


def test_read_community_posts_returns_is_liked_false_when_not_liked() -> None:
    db = Mock(spec=Session)
    set_community_results(
        db,
        rows=[community_post_row(post_id=1, like_count=0, is_liked=False)],
    )

    response = read_community_posts_request(db)

    assert response.status_code == 200
    assert response.json()["posts"][0]["isLiked"] is False
    assert response.json()["posts"][0]["likeCount"] == 0


def test_read_community_posts_returns_null_author_profile_image_url() -> None:
    db = Mock(spec=Session)
    set_community_results(
        db,
        rows=[community_post_row(post_id=1, profile_character_img_url=None)],
    )

    response = read_community_posts_request(db)

    assert response.status_code == 200
    assert response.json()["posts"][0]["author"]["profileImageUrl"] is None


def test_read_community_posts_returns_empty_list_when_no_post() -> None:
    db = Mock(spec=Session)
    set_community_results(db, rows=[])

    response = read_community_posts_request(db)

    assert response.status_code == 200
    assert response.json() == {
        "posts": [],
        "pagination": {"page": 0, "size": 20, "hasNext": False},
    }


def test_read_community_posts_returns_has_next_true_when_more_rows_exist() -> None:
    db = Mock(spec=Session)
    set_community_results(
        db,
        rows=[
            community_post_row(post_id=3),
            community_post_row(post_id=2),
            community_post_row(post_id=1),
        ],
    )

    response = read_community_posts_request(db, page=1, size=2)

    assert response.status_code == 200
    assert [post["id"] for post in response.json()["posts"]] == [3, 2]
    assert response.json()["pagination"] == {"page": 1, "size": 2, "hasNext": True}


def test_read_community_posts_queries_all_board_types_by_default() -> None:
    db = Mock(spec=Session)
    set_community_results(db, rows=[])

    read_community_posts_request(db)

    query = compiled_query(db.execute.call_args)
    assert "post.board_type" not in query.split("WHERE", 1)[1]


def test_read_community_posts_filters_free_board() -> None:
    db = Mock(spec=Session)
    set_community_results(db, rows=[])

    response = read_community_posts_request(db, board_type="FREE")

    assert response.status_code == 200
    assert "post.board_type = 'FREE'" in compiled_query(db.execute.call_args)


def test_read_community_posts_filters_certification_board() -> None:
    db = Mock(spec=Session)
    set_community_results(db, rows=[])

    response = read_community_posts_request(db, board_type="CERTIFICATION")

    assert response.status_code == 200
    assert "post.board_type = 'CERTIFICATION'" in compiled_query(db.execute.call_args)


def test_read_community_posts_searches_title_by_keyword() -> None:
    db = Mock(spec=Session)
    set_community_results(db, rows=[community_post_row(post_id=1)])

    response = read_community_posts_request(db, keyword="큐브")

    assert response.status_code == 200
    query = compiled_query(db.execute.call_args)
    assert "post.title LIKE '%큐브%'" in query
    assert "post.content" not in query.split("WHERE", 1)[1]


def test_read_community_posts_combines_board_type_and_keyword() -> None:
    db = Mock(spec=Session)
    set_community_results(db, rows=[])

    response = read_community_posts_request(
        db,
        board_type="CERTIFICATION",
        keyword="큐브",
    )

    assert response.status_code == 200
    query = compiled_query(db.execute.call_args)
    assert "post.board_type = 'CERTIFICATION'" in query
    assert "post.title LIKE '%큐브%'" in query


def test_read_community_posts_strips_keyword_before_matching() -> None:
    db = Mock(spec=Session)
    set_community_results(db, rows=[])

    read_community_posts_request(db, keyword="  큐브  ")

    assert "post.title LIKE '%큐브%'" in compiled_query(db.execute.call_args)


def test_read_community_posts_ignores_blank_keyword() -> None:
    db = Mock(spec=Session)
    set_community_results(db, rows=[])

    response = read_community_posts_request(db, keyword="   ")

    assert response.status_code == 200
    assert "post.title LIKE" not in compiled_query(db.execute.call_args)


def test_read_community_posts_ignores_empty_keyword() -> None:
    db = Mock(spec=Session)
    set_community_results(db, rows=[])

    response = read_community_posts_request(db, keyword="")

    assert response.status_code == 200
    assert "post.title LIKE" not in compiled_query(db.execute.call_args)


def test_read_community_posts_escapes_like_wildcards_in_keyword() -> None:
    db = Mock(spec=Session)
    set_community_results(db, rows=[])

    response = read_community_posts_request(db, keyword="50%_")

    assert response.status_code == 200
    query = compiled_query(db.execute.call_args)
    assert "post.title LIKE '%50\\%\\_%' ESCAPE '\\'" in query


def test_read_community_posts_escapes_escape_character_in_keyword() -> None:
    db = Mock(spec=Session)
    set_community_results(db, rows=[])

    response = read_community_posts_request(db, keyword="A\\B")

    assert response.status_code == 200
    query = compiled_query(db.execute.call_args)
    assert "post.title LIKE '%A\\\\B%' ESCAPE '\\'" in query


def test_read_community_posts_allows_single_character_keyword() -> None:
    db = Mock(spec=Session)
    set_community_results(db, rows=[])

    response = read_community_posts_request(db, keyword="큐")

    assert response.status_code == 200
    assert "post.title LIKE '%큐%'" in compiled_query(db.execute.call_args)


def test_read_community_posts_excludes_deleted_posts() -> None:
    db = Mock(spec=Session)
    set_community_results(db, rows=[])

    read_community_posts_request(db)

    query = compiled_query(db.execute.call_args)
    assert "post.status IN ('ACTIVE', 'REPORTED')" in query
    assert "post.deleted_at IS NULL" in query
    assert '"user".id = post.user_id' in query


def test_read_community_posts_orders_by_created_at_and_id_desc() -> None:
    db = Mock(spec=Session)
    set_community_results(db, rows=[])

    read_community_posts_request(db, page=2, size=5)

    query = compiled_query(db.execute.call_args)
    assert "ORDER BY post.created_at DESC, post.id DESC" in query
    assert "LIMIT 6" in query
    assert "OFFSET 10" in query


def test_read_community_posts_counts_only_liked_rows_and_active_comments() -> None:
    db = Mock(spec=Session)
    set_community_results(db, rows=[])

    read_community_posts_request(db)

    query = compiled_query(db.execute.call_args)
    assert "count(post_like.id)" in query
    assert "post_like.is_liked IS true" in query
    assert "count(comment.id)" in query
    assert "comment.status = 'ACTIVE'" in query
    assert "comment.deleted_at IS NULL" in query


def test_read_community_posts_checks_current_user_like_for_is_liked() -> None:
    db = Mock(spec=Session)
    set_community_results(db, rows=[])

    read_community_posts_request(db)

    query = compiled_query(db.execute.call_args)
    assert "EXISTS (SELECT" in query
    assert "post_like.user_id = 1" in query


def test_read_community_posts_allows_minimum_page_and_size() -> None:
    db = Mock(spec=Session)
    set_community_results(db, rows=[])

    response = read_community_posts_request(db, page=0, size=1)

    assert response.status_code == 200
    assert response.json()["pagination"] == {"page": 0, "size": 1, "hasNext": False}


def test_read_community_posts_returns_400_when_page_is_negative() -> None:
    db = Mock(spec=Session)

    response = read_community_posts_request(db, page=-1)

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.execute.assert_not_called()


def test_read_community_posts_returns_400_when_size_is_zero() -> None:
    db = Mock(spec=Session)

    response = read_community_posts_request(db, size=0)

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.execute.assert_not_called()


def test_read_community_posts_returns_400_for_unsupported_board_type() -> None:
    db = Mock(spec=Session)

    response = read_community_posts_request(db, board_type="NOTICE")

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.execute.assert_not_called()


def test_read_community_posts_swagger_contract() -> None:
    operation = app.openapi()["paths"]["/api/v1/community/posts"]["get"]

    assert set(operation["responses"]) == {"200", "400"}
    assert {parameter["name"] for parameter in operation["parameters"]} == {
        "boardType",
        "keyword",
        "page",
        "size",
    }
    assert operation["tags"] == ["community"]
    assert operation["security"] == [{"HTTPBearer": []}]
# --- 커뮤니티 상세 조회: GET /api/v1/community/posts/{postId} ---

POST_NOT_FOUND_RESPONSE = {
    "code": "POST_NOT_FOUND",
    "message": "게시글을 찾을 수 없습니다.",
}

COMMENT_NOT_FOUND_RESPONSE = {
    "code": "COMMENT_NOT_FOUND",
    "message": "댓글을 찾을 수 없습니다.",
}


def read_community_post_detail_request(db: Mock, *, post_id: int | str = 1):
    with api_client(db) as client:
        return client.get(f"/api/v1/community/posts/{post_id}")


def community_comment_row(
    *,
    comment_id: int,
    user_id: int = 2,
    content: str = "축하해요! 26번 큐브 정말 부럽네요.",
    created_at: str = "2026-08-28T09:20:00",
    like_count: int = 2,
    is_liked: bool = False,
    status: CommentStatus = CommentStatus.ACTIVE,
):
    """댓글 조회가 반환하는 (댓글, 작성자, 좋아요 수, 좋아요 여부) 행을 만듭니다."""
    comment = Comment(
        id=comment_id,
        post_id=1,
        user_id=user_id,
        content=content,
        status=status,
        created_at=datetime.fromisoformat(created_at),
        deleted_at=None,
    )
    return (
        comment,
        community_author(user_id=user_id, nickname="지드래곤짱"),
        like_count,
        is_liked,
    )


def set_post_detail_results(
    db: Mock,
    *,
    post_row: tuple | None,
    image_urls: list[str] | None = None,
    comment_rows: list | None = None,
) -> None:
    """서비스가 호출하는 db.execute / db.scalars 결과를 순서대로 지정합니다."""
    db.execute.side_effect = [
        Mock(first=Mock(return_value=post_row)),
        Mock(all=Mock(return_value=comment_rows or [])),
    ]
    db.scalars.return_value = image_urls or []


def post_detail_row(
    *,
    post_id: int = 1,
    user_id: int = 1,
    like_count: int = 4,
    is_liked: bool = True,
):
    """게시글 조회가 반환하는 (게시글, 작성자, 좋아요 수, 좋아요 여부) 행을 만듭니다."""
    return (
        community_post(
            post_id=post_id,
            user_id=user_id,
            created_at="2026-08-28T09:10:00",
        ),
        community_author(user_id=user_id),
        like_count,
        is_liked,
    )


def test_read_community_post_detail_returns_post_images_and_comments() -> None:
    db = Mock(spec=Session)
    set_post_detail_results(
        db,
        post_row=post_detail_row(),
        image_urls=["https://cdn.example.com/post/1/1.jpg"],
        comment_rows=[
            community_comment_row(comment_id=1),
            community_comment_row(
                comment_id=2,
                content="AR 무대가 생생하더라고요.",
                created_at="2026-08-28T09:30:00",
                like_count=1,
                is_liked=True,
            ),
        ],
    )

    response = read_community_post_detail_request(db)

    assert response.status_code == 200
    assert response.json() == {
        "post": {
            "id": 1,
            "boardType": "FREE",
            "author": {
                "id": 1,
                "nickname": "블링크",
                "profileImageUrl": "https://cdn.example.com/profile_002.png",
            },
            "createdAt": "2026-08-28T09:10:00",
            "title": "Ruby 큐브 26번 등록했어요",
            "content": "앨범 나오자마자 큐브 등록했습니다.",
            "imageUrls": ["https://cdn.example.com/post/1/1.jpg"],
            "likeCount": 4,
            "isLiked": True,
            "commentCount": 2,
            "isMine": True,
            "comments": [
                {
                    "id": 1,
                    "author": {
                        "id": 2,
                        "nickname": "지드래곤짱",
                        "profileImageUrl": "https://cdn.example.com/profile_002.png",
                    },
                    "content": "축하해요! 26번 큐브 정말 부럽네요.",
                    "createdAt": "2026-08-28T09:20:00",
                    "likeCount": 2,
                    "isLiked": False,
                    "isMine": False,
                },
                {
                    "id": 2,
                    "author": {
                        "id": 2,
                        "nickname": "지드래곤짱",
                        "profileImageUrl": "https://cdn.example.com/profile_002.png",
                    },
                    "content": "AR 무대가 생생하더라고요.",
                    "createdAt": "2026-08-28T09:30:00",
                    "likeCount": 1,
                    "isLiked": True,
                    "isMine": False,
                },
            ],
        }
    }
    db.commit.assert_not_called()


def test_read_community_post_detail_returns_empty_images_and_comments() -> None:
    db = Mock(spec=Session)
    set_post_detail_results(
        db,
        post_row=post_detail_row(),
        image_urls=[],
        comment_rows=[],
    )

    response = read_community_post_detail_request(db)

    assert response.status_code == 200
    assert response.json()["post"]["imageUrls"] == []
    assert response.json()["post"]["comments"] == []
    assert response.json()["post"]["commentCount"] == 0


def test_read_community_post_detail_returns_is_mine_false_for_other_user_post() -> None:
    db = Mock(spec=Session)
    set_post_detail_results(
        db,
        post_row=post_detail_row(user_id=2, is_liked=False, like_count=0),
        comment_rows=[community_comment_row(comment_id=1, user_id=1)],
    )

    response = read_community_post_detail_request(db)

    assert response.status_code == 200
    assert response.json()["post"]["isMine"] is False
    assert response.json()["post"]["isLiked"] is False
    assert response.json()["post"]["comments"][0]["isMine"] is True


def test_read_community_post_detail_includes_reported_comment() -> None:
    db = Mock(spec=Session)
    set_post_detail_results(
        db,
        post_row=post_detail_row(),
        comment_rows=[
            community_comment_row(comment_id=1, status=CommentStatus.REPORTED),
        ],
    )

    response = read_community_post_detail_request(db)

    assert response.status_code == 200
    assert [comment["id"] for comment in response.json()["post"]["comments"]] == [1]
    assert response.json()["post"]["commentCount"] == 1


def test_read_community_post_detail_returns_null_author_fields() -> None:
    db = Mock(spec=Session)
    post = community_post(post_id=1, created_at="2026-08-28T09:10:00")
    author = community_author(nickname=None, profile_character_img_url=None)
    set_post_detail_results(db, post_row=(post, author, 0, False))

    response = read_community_post_detail_request(db)

    assert response.status_code == 200
    assert response.json()["post"]["author"]["nickname"] is None
    assert response.json()["post"]["author"]["profileImageUrl"] is None


def test_read_community_post_detail_returns_404_when_post_is_unavailable() -> None:
    db = Mock(spec=Session)
    set_post_detail_results(db, post_row=None)

    response = read_community_post_detail_request(db)

    assert response.status_code == 404
    assert response.json() == POST_NOT_FOUND_RESPONSE
    db.scalars.assert_not_called()


def test_read_community_post_detail_allows_minimum_post_id() -> None:
    db = Mock(spec=Session)
    set_post_detail_results(db, post_row=post_detail_row())

    response = read_community_post_detail_request(db, post_id=1)

    assert response.status_code == 200


def test_read_community_post_detail_returns_400_when_post_id_is_zero() -> None:
    db = Mock(spec=Session)

    response = read_community_post_detail_request(db, post_id=0)

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.execute.assert_not_called()


def test_read_community_post_detail_returns_400_when_post_id_is_not_a_number() -> None:
    db = Mock(spec=Session)

    response = read_community_post_detail_request(db, post_id="abc")

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.execute.assert_not_called()


def test_read_community_post_detail_excludes_deleted_post() -> None:
    db = Mock(spec=Session)
    set_post_detail_results(db, post_row=post_detail_row())

    read_community_post_detail_request(db, post_id=7)

    query = compiled_query(db.execute.call_args_list[0])
    assert "post.id = 7" in query
    assert "post.status IN ('ACTIVE', 'REPORTED')" in query
    assert "post.deleted_at IS NULL" in query
    assert "count(post_like.id)" in query
    assert "post_like.user_id = 1" in query


def test_read_community_post_detail_orders_images_by_id_asc() -> None:
    db = Mock(spec=Session)
    set_post_detail_results(db, post_row=post_detail_row())

    read_community_post_detail_request(db)

    query = compiled_query(db.scalars.call_args)
    assert "post_media.post_image_url" in query
    assert "post_media.post_id = 1" in query
    assert "ORDER BY post_media.id ASC" in query


def test_read_community_post_detail_orders_comments_by_created_at_asc() -> None:
    db = Mock(spec=Session)
    set_post_detail_results(db, post_row=post_detail_row())

    read_community_post_detail_request(db)

    query = compiled_query(db.execute.call_args_list[1])
    assert "comment.post_id = 1" in query
    assert "comment.status IN ('ACTIVE', 'REPORTED')" in query
    assert "comment.deleted_at IS NULL" in query
    assert "ORDER BY comment.created_at ASC, comment.id ASC" in query


def test_read_community_post_detail_counts_only_liked_comment_rows() -> None:
    db = Mock(spec=Session)
    set_post_detail_results(db, post_row=post_detail_row())

    read_community_post_detail_request(db)

    query = compiled_query(db.execute.call_args_list[1])
    assert "count(comment_like.id)" in query
    assert "comment_like.is_liked IS true" in query
    assert "comment_like.user_id = 1" in query


def test_read_community_post_detail_swagger_contract() -> None:
    operation = app.openapi()["paths"]["/api/v1/community/posts/{postId}"]["get"]

    assert set(operation["responses"]) == {"200", "404"}
    assert operation["tags"] == ["community"]
    assert operation["security"] == [{"HTTPBearer": []}]
# --- 커뮤니티 게시글 작성: POST /api/v1/community/posts ---

BLOB_URL = "https://haniumstorage.blob.core.windows.net/hanium/community_post/1/1"


def create_post_request(
    db: Mock,
    *,
    data: dict[str, str] | None = None,
    files: list[tuple[str, tuple[str, bytes, str]]] | None = None,
    raise_server_exceptions: bool = True,
):
    with api_client(db, raise_server_exceptions=raise_server_exceptions) as client:
        return client.post(
            "/api/v1/community/posts",
            data=data
            if data is not None
            else {
                "boardType": "FREE",
                "title": "Ruby 큐브 26번 등록했어요",
                "content": "앨범 나오자마자 큐브 등록했습니다.",
            },
            files=files,
        )


def post_images(count: int, *, content_type: str = "image/png"):
    """multipart로 보낼 images 필드를 count 장 만듭니다."""
    return [
        ("images", (f"post{index}.png", b"fake-image", content_type))
        for index in range(count)
    ]


def collect_added_rows(db: Mock) -> list:
    """db.add 로 저장한 ORM 객체를 순서대로 모으고 flush 시 게시글 id를 부여합니다."""
    added: list = []
    db.add.side_effect = added.append

    def assign_post_id() -> None:
        added[0].id = 1

    db.flush.side_effect = assign_post_id
    return added


def test_create_post_saves_post_without_image() -> None:
    db = Mock(spec=Session)
    added = collect_added_rows(db)

    with patch("app.community.service.upload_community_post_image") as upload:
        response = create_post_request(db)

    assert response.status_code == 201
    assert response.json() == {"postId": 1}
    upload.assert_not_called()
    assert len(added) == 1
    post = added[0]
    assert isinstance(post, Post)
    assert post.user_id == 1
    assert post.board_type == BoardType.FREE
    assert post.title == "Ruby 큐브 26번 등록했어요"
    assert post.content == "앨범 나오자마자 큐브 등록했습니다."
    assert post.status == PostStatus.ACTIVE
    assert post.deleted_at is None
    db.flush.assert_called_once()
    db.commit.assert_called_once()


def test_create_post_uploads_images_in_request_order() -> None:
    db = Mock(spec=Session)
    added = collect_added_rows(db)

    with patch(
        "app.community.service.upload_community_post_image",
        side_effect=[f"{BLOB_URL}/first.png", f"{BLOB_URL}/second.png"],
    ) as upload:
        response = create_post_request(db, files=post_images(2))

    assert response.status_code == 201
    assert response.json() == {"postId": 1}
    assert upload.call_count == 2
    assert upload.call_args_list[0].kwargs["user_id"] == 1
    assert upload.call_args_list[0].kwargs["post_id"] == 1
    assert upload.call_args_list[0].kwargs["content_type"] == "image/png"
    media = added[1:]
    assert [type(row) for row in media] == [PostMedia, PostMedia]
    assert [row.post_id for row in media] == [1, 1]
    assert [row.post_image_url for row in media] == [
        f"{BLOB_URL}/first.png",
        f"{BLOB_URL}/second.png",
    ]
    db.commit.assert_called_once()


def test_create_post_saves_certification_board_type() -> None:
    db = Mock(spec=Session)
    added = collect_added_rows(db)

    with patch("app.community.service.upload_community_post_image"):
        response = create_post_request(
            db,
            data={
                "boardType": "CERTIFICATION",
                "title": "큐브 인증 완료",
                "content": "발매일에 바로 인증 성공했습니다.",
            },
        )

    assert response.status_code == 201
    assert added[0].board_type == BoardType.CERTIFICATION


def test_create_post_strips_title_and_content() -> None:
    db = Mock(spec=Session)
    added = collect_added_rows(db)

    with patch("app.community.service.upload_community_post_image"):
        response = create_post_request(
            db,
            data={
                "boardType": "FREE",
                "title": "  제목  ",
                "content": "  내용  ",
            },
        )

    assert response.status_code == 201
    assert added[0].title == "제목"
    assert added[0].content == "내용"


def test_create_post_allows_maximum_title_length() -> None:
    db = Mock(spec=Session)
    added = collect_added_rows(db)

    with patch("app.community.service.upload_community_post_image"):
        response = create_post_request(
            db,
            data={
                "boardType": "FREE",
                "title": "가" * 150,
                "content": "내용",
            },
        )

    assert response.status_code == 201
    assert added[0].title == "가" * 150


def test_create_post_allows_title_that_fits_after_strip() -> None:
    db = Mock(spec=Session)
    added = collect_added_rows(db)

    with patch("app.community.service.upload_community_post_image"):
        response = create_post_request(
            db,
            data={
                "boardType": "FREE",
                "title": "  " + "가" * 150 + "  ",
                "content": "내용",
            },
        )

    assert response.status_code == 201
    assert added[0].title == "가" * 150


def test_create_post_returns_400_when_title_is_too_long() -> None:
    db = Mock(spec=Session)

    response = create_post_request(
        db,
        data={
            "boardType": "FREE",
            "title": "가" * 151,
            "content": "내용",
        },
    )

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.add.assert_not_called()


def test_create_post_allows_maximum_image_count() -> None:
    db = Mock(spec=Session)
    added = collect_added_rows(db)

    with patch(
        "app.community.service.upload_community_post_image",
        return_value=f"{BLOB_URL}/image.png",
    ) as upload:
        response = create_post_request(db, files=post_images(5))

    assert response.status_code == 201
    assert upload.call_count == 5
    assert len(added) == 6


def test_create_post_returns_400_when_image_count_exceeds_limit() -> None:
    db = Mock(spec=Session)

    with patch("app.community.service.upload_community_post_image") as upload:
        response = create_post_request(db, files=post_images(6))

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    upload.assert_not_called()
    db.add.assert_not_called()


def test_create_post_returns_400_when_title_is_blank() -> None:
    db = Mock(spec=Session)

    response = create_post_request(
        db,
        data={"boardType": "FREE", "title": "   ", "content": "내용"},
    )

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.add.assert_not_called()


def test_create_post_returns_400_when_content_is_blank() -> None:
    db = Mock(spec=Session)

    response = create_post_request(
        db,
        data={"boardType": "FREE", "title": "제목", "content": "   "},
    )

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.add.assert_not_called()


def test_create_post_returns_400_when_required_form_field_is_missing() -> None:
    db = Mock(spec=Session)

    response = create_post_request(db, data={"boardType": "FREE", "title": "제목"})

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.add.assert_not_called()


def test_create_post_returns_400_for_unsupported_board_type() -> None:
    db = Mock(spec=Session)

    response = create_post_request(
        db,
        data={"boardType": "NOTICE", "title": "제목", "content": "내용"},
    )

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.add.assert_not_called()


def test_create_post_returns_400_for_unsupported_image_content_type() -> None:
    db = Mock(spec=Session)

    with patch("app.community.service.upload_community_post_image") as upload:
        response = create_post_request(
            db,
            files=post_images(1, content_type="image/gif"),
        )

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    upload.assert_not_called()
    db.add.assert_not_called()


def test_create_post_rolls_back_when_image_upload_fails() -> None:
    db = Mock(spec=Session)
    collect_added_rows(db)

    with patch(
        "app.community.service.upload_community_post_image",
        side_effect=RuntimeError("azure failed"),
    ):
        response = create_post_request(
            db,
            files=post_images(1),
            raise_server_exceptions=False,
        )

    assert response.status_code == 500
    assert response.json() == {
        "code": "INTERNAL_SERVER_ERROR",
        "message": "서버 내부 오류가 발생했습니다.",
    }
    db.rollback.assert_called_once()
    db.commit.assert_not_called()


def test_create_post_rolls_back_when_commit_fails() -> None:
    db = Mock(spec=Session)
    collect_added_rows(db)
    db.commit.side_effect = RuntimeError("db failed")

    with patch("app.community.service.upload_community_post_image"):
        response = create_post_request(db, raise_server_exceptions=False)

    assert response.status_code == 500
    db.rollback.assert_called_once()


def test_create_post_swagger_contract() -> None:
    openapi_schema = app.openapi()
    operation = openapi_schema["paths"]["/api/v1/community/posts"]["post"]

    assert set(operation["responses"]) == {"201", "400"}
    assert set(operation["requestBody"]["content"]) == {"multipart/form-data"}
    response_ref = operation["responses"]["201"]["content"]["application/json"][
        "schema"
    ]["$ref"]
    response_schema = openapi_schema["components"]["schemas"][
        response_ref.rsplit("/", 1)[-1]
    ]
    assert set(response_schema["properties"]) == {"postId"}
    assert operation["tags"] == ["community"]
    assert operation["security"] == [{"HTTPBearer": []}]
# --- 커뮤니티 게시글 삭제: DELETE /api/v1/community/posts/{postId} ---


def delete_post_request(
    db: Mock,
    *,
    post_id: int | str = 1,
    raise_server_exceptions: bool = True,
):
    with api_client(db, raise_server_exceptions=raise_server_exceptions) as client:
        return client.delete(f"/api/v1/community/posts/{post_id}")


def test_delete_post_soft_deletes_current_user_post() -> None:
    db = Mock(spec=Session)
    post = community_post(post_id=1)
    db.scalar.return_value = post

    response = delete_post_request(db)

    assert response.status_code == 204
    assert response.content == b""
    assert post.status == PostStatus.DELETED
    assert post.deleted_at is not None
    assert post.deleted_at.tzinfo is None
    db.commit.assert_called_once()
    db.add.assert_not_called()


def test_delete_post_deletes_reported_post() -> None:
    db = Mock(spec=Session)
    post = community_post(post_id=1)
    post.status = PostStatus.REPORTED
    db.scalar.return_value = post

    response = delete_post_request(db)

    assert response.status_code == 204
    assert post.status == PostStatus.DELETED
    db.commit.assert_called_once()


def test_delete_post_returns_404_when_post_is_unavailable() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = delete_post_request(db)

    assert response.status_code == 404
    assert response.json() == POST_NOT_FOUND_RESPONSE
    db.commit.assert_not_called()


def test_delete_post_locks_only_current_user_visible_post() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = community_post(post_id=1)

    delete_post_request(db, post_id=7)

    query = compiled_query(db.scalar.call_args)
    assert "post.id = 7" in query
    assert "post.user_id = 1" in query
    assert "post.status IN ('ACTIVE', 'REPORTED')" in query
    assert "post.deleted_at IS NULL" in query
    assert "FOR UPDATE" in query


def test_delete_post_allows_minimum_post_id() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = community_post(post_id=1)

    response = delete_post_request(db, post_id=1)

    assert response.status_code == 204


def test_delete_post_returns_400_when_post_id_is_zero() -> None:
    db = Mock(spec=Session)

    response = delete_post_request(db, post_id=0)

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_delete_post_returns_400_when_post_id_is_not_a_number() -> None:
    db = Mock(spec=Session)

    response = delete_post_request(db, post_id="abc")

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_delete_post_rolls_back_when_commit_fails() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = community_post(post_id=1)
    db.commit.side_effect = RuntimeError("db failed")

    response = delete_post_request(db, raise_server_exceptions=False)

    assert response.status_code == 500
    db.rollback.assert_called_once()


def test_delete_post_swagger_contract() -> None:
    operation = app.openapi()["paths"]["/api/v1/community/posts/{postId}"]["delete"]

    assert set(operation["responses"]) == {"204", "404"}
    assert "requestBody" not in operation
    assert operation["tags"] == ["community"]
    assert operation["security"] == [{"HTTPBearer": []}]


# --- 커뮤니티 게시글 좋아요 토글: PATCH /api/v1/community/posts/{postId}/like ---


def toggle_post_like_request(
    db: Mock,
    *,
    post_id: int | str = 1,
    raise_server_exceptions: bool = True,
):
    with api_client(db, raise_server_exceptions=raise_server_exceptions) as client:
        return client.patch(f"/api/v1/community/posts/{post_id}/like")


def community_post_like(*, post_id: int = 1, user_id: int = 1, is_liked: bool = True):
    return PostLike(id=1, post_id=post_id, user_id=user_id, is_liked=is_liked)


def set_post_like_results(
    db: Mock,
    *,
    post=None,
    post_like=None,
    like_count: int = 0,
) -> list:
    """서비스가 조회하는 순서대로 게시글, 좋아요 행, 좋아요 수를 지정합니다."""
    db.scalar.side_effect = [post, post_like, like_count]
    added: list = []
    db.add.side_effect = added.append
    return added


def test_toggle_post_like_creates_liked_row_when_no_history() -> None:
    db = Mock(spec=Session)
    added = set_post_like_results(
        db,
        post=community_post(post_id=1),
        post_like=None,
        like_count=6,
    )

    response = toggle_post_like_request(db)

    assert response.status_code == 200
    assert response.json() == {"isLiked": True, "likeCount": 6}
    assert len(added) == 1
    assert added[0].post_id == 1
    assert added[0].user_id == 1
    assert added[0].is_liked is True
    db.commit.assert_called_once()


def test_toggle_post_like_cancels_existing_like() -> None:
    db = Mock(spec=Session)
    post_like = community_post_like(is_liked=True)
    added = set_post_like_results(
        db,
        post=community_post(post_id=1),
        post_like=post_like,
        like_count=5,
    )

    response = toggle_post_like_request(db)

    assert response.status_code == 200
    assert response.json() == {"isLiked": False, "likeCount": 5}
    assert post_like.is_liked is False
    assert added == []
    db.delete.assert_not_called()
    db.commit.assert_called_once()


def test_toggle_post_like_relikes_cancelled_like() -> None:
    db = Mock(spec=Session)
    post_like = community_post_like(is_liked=False)
    added = set_post_like_results(
        db,
        post=community_post(post_id=1),
        post_like=post_like,
        like_count=6,
    )

    response = toggle_post_like_request(db)

    assert response.status_code == 200
    assert response.json() == {"isLiked": True, "likeCount": 6}
    assert post_like.is_liked is True
    assert added == []
    db.commit.assert_called_once()


def test_toggle_post_like_allows_liking_own_post() -> None:
    db = Mock(spec=Session)
    set_post_like_results(
        db,
        post=community_post(post_id=1, user_id=1),
        post_like=None,
        like_count=1,
    )

    response = toggle_post_like_request(db)

    assert response.status_code == 200
    assert response.json() == {"isLiked": True, "likeCount": 1}


def test_toggle_post_like_returns_zero_like_count_when_all_cancelled() -> None:
    db = Mock(spec=Session)
    set_post_like_results(
        db,
        post=community_post(post_id=1),
        post_like=community_post_like(is_liked=True),
        like_count=0,
    )

    response = toggle_post_like_request(db)

    assert response.status_code == 200
    assert response.json() == {"isLiked": False, "likeCount": 0}


def test_toggle_post_like_toggles_reported_post() -> None:
    db = Mock(spec=Session)
    post = community_post(post_id=1)
    post.status = PostStatus.REPORTED
    set_post_like_results(db, post=post, post_like=None, like_count=1)

    response = toggle_post_like_request(db)

    assert response.status_code == 200
    assert response.json() == {"isLiked": True, "likeCount": 1}


def test_toggle_post_like_returns_404_when_post_not_found() -> None:
    db = Mock(spec=Session)
    set_post_like_results(db, post=None)

    response = toggle_post_like_request(db)

    assert response.status_code == 404
    assert response.json() == POST_NOT_FOUND_RESPONSE
    assert db.scalar.call_count == 1
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_toggle_post_like_locks_visible_post_only() -> None:
    db = Mock(spec=Session)
    set_post_like_results(
        db,
        post=community_post(post_id=1),
        post_like=None,
        like_count=1,
    )

    toggle_post_like_request(db, post_id=1)

    query = compiled_query(db.scalar.call_args_list[0])
    assert "post.id = 1" in query
    assert "post.status IN ('ACTIVE', 'REPORTED')" in query
    assert "post.deleted_at IS NULL" in query
    assert "FOR UPDATE" in query
    # 삭제와 달리 작성자 조건으로 거르지 않아 남의 게시글에도 좋아요를 누를 수 있습니다.
    assert "post.user_id" not in query.split("WHERE", 1)[1]


def test_toggle_post_like_queries_like_row_of_current_user() -> None:
    db = Mock(spec=Session)
    set_post_like_results(
        db,
        post=community_post(post_id=1),
        post_like=None,
        like_count=1,
    )

    toggle_post_like_request(db, post_id=1)

    query = compiled_query(db.scalar.call_args_list[1])
    assert "post_like.post_id = 1" in query
    assert "post_like.user_id = 1" in query


def test_toggle_post_like_counts_only_liked_rows_after_flush() -> None:
    db = Mock(spec=Session)
    set_post_like_results(
        db,
        post=community_post(post_id=1),
        post_like=None,
        like_count=1,
    )

    toggle_post_like_request(db, post_id=1)

    query = compiled_query(db.scalar.call_args_list[2])
    assert "count(post_like.id)" in query
    assert "post_like.post_id = 1" in query
    assert "post_like.is_liked IS true" in query
    db.flush.assert_called_once()


def test_toggle_post_like_allows_minimum_post_id() -> None:
    db = Mock(spec=Session)
    set_post_like_results(
        db,
        post=community_post(post_id=1),
        post_like=None,
        like_count=1,
    )

    response = toggle_post_like_request(db, post_id=1)

    assert response.status_code == 200


def test_toggle_post_like_returns_400_when_post_id_is_zero() -> None:
    db = Mock(spec=Session)

    response = toggle_post_like_request(db, post_id=0)

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_toggle_post_like_returns_400_when_post_id_is_not_number() -> None:
    db = Mock(spec=Session)

    response = toggle_post_like_request(db, post_id="abc")

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_toggle_post_like_rolls_back_when_commit_fails() -> None:
    db = Mock(spec=Session)
    set_post_like_results(
        db,
        post=community_post(post_id=1),
        post_like=None,
        like_count=1,
    )
    db.commit.side_effect = RuntimeError("db failed")

    response = toggle_post_like_request(db, raise_server_exceptions=False)

    assert response.status_code == 500
    db.rollback.assert_called_once()


def test_toggle_post_like_swagger_contract() -> None:
    operation = app.openapi()["paths"]["/api/v1/community/posts/{postId}/like"]["patch"]

    assert set(operation["responses"]) == {"200", "404"}
    assert "requestBody" not in operation
    assert operation["tags"] == ["community"]
    assert operation["security"] == [{"HTTPBearer": []}]


# --- 커뮤니티 댓글 작성: POST /api/v1/community/posts/{postId}/comments ---

COMMENT_CREATED_AT = "2026-09-20T18:30:00"


DEFAULT_COMMENT_CONTENT = "큐브 디자인이 정말 예쁘네요."


def create_comment_request(
    db: Mock,
    *,
    post_id: int | str = 1,
    body: dict | None = None,
    raise_server_exceptions: bool = True,
):
    with api_client(db, raise_server_exceptions=raise_server_exceptions) as client:
        return client.post(
            f"/api/v1/community/posts/{post_id}/comments",
            json=body if body is not None else {"content": DEFAULT_COMMENT_CONTENT},
        )


def set_comment_results(
    db: Mock,
    *,
    post=None,
    author=None,
    comment_id: int = 46,
    created_at: str = COMMENT_CREATED_AT,
) -> list:
    """게시글·작성자 조회 결과를 지정하고, flush 시 댓글 id와 작성 시각을 부여합니다."""
    db.scalar.side_effect = [post, author]
    added: list = []
    db.add.side_effect = added.append

    def assign_server_defaults() -> None:
        added[0].id = comment_id
        added[0].created_at = datetime.fromisoformat(created_at)

    db.flush.side_effect = assign_server_defaults
    return added


def test_create_comment_saves_comment_and_returns_it() -> None:
    db = Mock(spec=Session)
    added = set_comment_results(
        db,
        post=community_post(post_id=1, user_id=2),
        author=community_author(),
    )

    response = create_comment_request(db)

    assert response.status_code == 201
    assert response.json() == {
        "comment": {
            "id": 46,
            "author": {
                "id": 1,
                "nickname": "블링크",
                "profileImageUrl": "https://cdn.example.com/profile_002.png",
            },
            "content": "큐브 디자인이 정말 예쁘네요.",
            "createdAt": COMMENT_CREATED_AT,
            "likeCount": 0,
            "isLiked": False,
            "isMine": True,
        }
    }
    assert len(added) == 1
    assert added[0].post_id == 1
    assert added[0].user_id == 1
    assert added[0].content == "큐브 디자인이 정말 예쁘네요."
    assert added[0].status == CommentStatus.ACTIVE
    assert added[0].deleted_at is None
    db.commit.assert_called_once()


def test_create_comment_strips_content() -> None:
    db = Mock(spec=Session)
    added = set_comment_results(
        db,
        post=community_post(post_id=1),
        author=community_author(),
    )

    response = create_comment_request(db, body={"content": "  댓글 내용  "})

    assert response.status_code == 201
    assert added[0].content == "댓글 내용"
    assert response.json()["comment"]["content"] == "댓글 내용"


def test_create_comment_keeps_newlines_in_content() -> None:
    db = Mock(spec=Session)
    added = set_comment_results(
        db,
        post=community_post(post_id=1),
        author=community_author(),
    )

    response = create_comment_request(db, body={"content": "첫 줄\n둘째 줄"})

    assert response.status_code == 201
    assert added[0].content == "첫 줄\n둘째 줄"


def test_create_comment_allows_comment_on_own_post() -> None:
    db = Mock(spec=Session)
    set_comment_results(
        db,
        post=community_post(post_id=1, user_id=1),
        author=community_author(),
    )

    response = create_comment_request(db)

    assert response.status_code == 201
    assert response.json()["comment"]["isMine"] is True


def test_create_comment_allows_comment_on_reported_post() -> None:
    db = Mock(spec=Session)
    post = community_post(post_id=1)
    post.status = PostStatus.REPORTED
    set_comment_results(db, post=post, author=community_author())

    response = create_comment_request(db)

    assert response.status_code == 201


def test_create_comment_returns_null_author_profile_fields() -> None:
    db = Mock(spec=Session)
    set_comment_results(
        db,
        post=community_post(post_id=1),
        author=community_author(nickname=None, profile_character_img_url=None),
    )

    response = create_comment_request(db)

    assert response.status_code == 201
    assert response.json()["comment"]["author"] == {
        "id": 1,
        "nickname": None,
        "profileImageUrl": None,
    }


def test_create_comment_returns_404_when_post_not_found() -> None:
    db = Mock(spec=Session)
    set_comment_results(db, post=None)

    response = create_comment_request(db)

    assert response.status_code == 404
    assert response.json() == POST_NOT_FOUND_RESPONSE
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_create_comment_locks_visible_post_only() -> None:
    db = Mock(spec=Session)
    set_comment_results(
        db,
        post=community_post(post_id=1),
        author=community_author(),
    )

    create_comment_request(db, post_id=1)

    query = compiled_query(db.scalar.call_args_list[0])
    assert "post.id = 1" in query
    assert "post.status IN ('ACTIVE', 'REPORTED')" in query
    assert "post.deleted_at IS NULL" in query
    assert "FOR UPDATE" in query
    # 게시글 삭제와 달리 작성자 조건으로 거르지 않습니다.
    assert "post.user_id" not in query.split("WHERE", 1)[1]


def test_create_comment_allows_maximum_content_length() -> None:
    db = Mock(spec=Session)
    added = set_comment_results(
        db,
        post=community_post(post_id=1),
        author=community_author(),
    )

    response = create_comment_request(db, body={"content": "가" * 1000})

    assert response.status_code == 201
    assert len(added[0].content) == 1000


def test_create_comment_allows_content_that_fits_after_strip() -> None:
    db = Mock(spec=Session)
    added = set_comment_results(
        db,
        post=community_post(post_id=1),
        author=community_author(),
    )

    response = create_comment_request(db, body={"content": "  " + "가" * 1000 + "  "})

    assert response.status_code == 201
    assert len(added[0].content) == 1000


def test_create_comment_returns_400_when_content_is_too_long() -> None:
    db = Mock(spec=Session)

    response = create_comment_request(db, body={"content": "가" * 1001})

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()
    db.add.assert_not_called()


def test_create_comment_allows_single_character_content() -> None:
    db = Mock(spec=Session)
    added = set_comment_results(
        db,
        post=community_post(post_id=1),
        author=community_author(),
    )

    response = create_comment_request(db, body={"content": "굿"})

    assert response.status_code == 201
    assert added[0].content == "굿"


def test_create_comment_returns_400_when_content_is_blank() -> None:
    db = Mock(spec=Session)

    response = create_comment_request(db, body={"content": "   "})

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_create_comment_returns_400_when_content_is_empty() -> None:
    db = Mock(spec=Session)

    response = create_comment_request(db, body={"content": ""})

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_create_comment_returns_400_when_content_is_missing() -> None:
    db = Mock(spec=Session)

    response = create_comment_request(db, body={})

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_create_comment_returns_400_when_content_is_not_string() -> None:
    db = Mock(spec=Session)

    response = create_comment_request(db, body={"content": 123})

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_create_comment_returns_400_when_post_id_is_zero() -> None:
    db = Mock(spec=Session)

    response = create_comment_request(db, post_id=0)

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_create_comment_returns_400_when_post_id_is_not_number() -> None:
    db = Mock(spec=Session)

    response = create_comment_request(db, post_id="abc")

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_create_comment_rolls_back_when_commit_fails() -> None:
    db = Mock(spec=Session)
    set_comment_results(
        db,
        post=community_post(post_id=1),
        author=community_author(),
    )
    db.commit.side_effect = RuntimeError("db failed")

    response = create_comment_request(db, raise_server_exceptions=False)

    assert response.status_code == 500
    db.rollback.assert_called_once()


def test_create_comment_swagger_contract() -> None:
    openapi_schema = app.openapi()
    operation = openapi_schema["paths"]["/api/v1/community/posts/{postId}/comments"][
        "post"
    ]

    assert set(operation["responses"]) == {"201", "400", "404"}
    assert set(operation["requestBody"]["content"]) == {"application/json"}
    response_ref = operation["responses"]["201"]["content"]["application/json"][
        "schema"
    ]["$ref"]
    response_schema = openapi_schema["components"]["schemas"][
        response_ref.rsplit("/", 1)[-1]
    ]
    assert set(response_schema["properties"]) == {"comment"}
    assert operation["tags"] == ["community"]
    assert operation["security"] == [{"HTTPBearer": []}]


# --- 커뮤니티 댓글 삭제: DELETE /api/v1/community/posts/{postId}/comments/{commentId} ---


def delete_comment_request(
    db: Mock,
    *,
    post_id: int | str = 1,
    comment_id: int | str = 1,
    raise_server_exceptions: bool = True,
):
    with api_client(db, raise_server_exceptions=raise_server_exceptions) as client:
        return client.delete(
            f"/api/v1/community/posts/{post_id}/comments/{comment_id}"
        )


def set_delete_comment_results(
    db: Mock,
    *,
    post: Post | None,
    comment: Comment | None = None,
) -> None:
    db.scalar.side_effect = [post] if post is None else [post, comment]


def test_delete_comment_soft_deletes_current_user_comment() -> None:
    db = Mock(spec=Session)
    comment = community_comment(comment_id=1)
    set_delete_comment_results(
        db,
        post=community_post(post_id=1),
        comment=comment,
    )

    response = delete_comment_request(db)

    assert response.status_code == 204
    assert response.content == b""
    assert comment.status == CommentStatus.DELETED
    assert comment.deleted_at is not None
    assert comment.deleted_at.tzinfo is None
    db.commit.assert_called_once()
    db.add.assert_not_called()


def test_delete_comment_deletes_reported_comment() -> None:
    db = Mock(spec=Session)
    comment = community_comment(
        comment_id=1,
        status=CommentStatus.REPORTED,
    )
    set_delete_comment_results(
        db,
        post=community_post(post_id=1),
        comment=comment,
    )

    response = delete_comment_request(db)

    assert response.status_code == 204
    assert comment.status == CommentStatus.DELETED


def test_delete_comment_returns_404_when_post_is_unavailable() -> None:
    db = Mock(spec=Session)
    set_delete_comment_results(db, post=None)

    response = delete_comment_request(db)

    assert response.status_code == 404
    assert response.json() == POST_NOT_FOUND_RESPONSE
    assert db.scalar.call_count == 1
    db.commit.assert_not_called()


def test_delete_comment_returns_404_when_comment_is_unavailable() -> None:
    db = Mock(spec=Session)
    set_delete_comment_results(
        db,
        post=community_post(post_id=1),
        comment=None,
    )

    response = delete_comment_request(db)

    assert response.status_code == 404
    assert response.json() == COMMENT_NOT_FOUND_RESPONSE
    db.commit.assert_not_called()


def test_delete_comment_locks_visible_post_and_owned_comment() -> None:
    db = Mock(spec=Session)
    set_delete_comment_results(
        db,
        post=community_post(post_id=7),
        comment=community_comment(comment_id=9, post_id=7),
    )

    delete_comment_request(db, post_id=7, comment_id=9)

    post_query = compiled_query(db.scalar.call_args_list[0])
    assert "post.id = 7" in post_query
    assert "post.status IN ('ACTIVE', 'REPORTED')" in post_query
    assert "post.deleted_at IS NULL" in post_query
    assert "FOR UPDATE" in post_query

    comment_query = compiled_query(db.scalar.call_args_list[1])
    assert "comment.id = 9" in comment_query
    assert "comment.post_id = 7" in comment_query
    assert "comment.user_id = 1" in comment_query
    assert "comment.status IN ('ACTIVE', 'REPORTED')" in comment_query
    assert "comment.deleted_at IS NULL" in comment_query
    assert "FOR UPDATE" in comment_query


def test_delete_comment_allows_minimum_path_ids() -> None:
    db = Mock(spec=Session)
    set_delete_comment_results(
        db,
        post=community_post(post_id=1),
        comment=community_comment(comment_id=1),
    )

    response = delete_comment_request(db, post_id=1, comment_id=1)

    assert response.status_code == 204


def test_delete_comment_returns_400_when_post_id_is_zero() -> None:
    db = Mock(spec=Session)

    response = delete_comment_request(db, post_id=0)

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_delete_comment_returns_400_when_comment_id_is_zero() -> None:
    db = Mock(spec=Session)

    response = delete_comment_request(db, comment_id=0)

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_delete_comment_returns_400_when_comment_id_is_not_a_number() -> None:
    db = Mock(spec=Session)

    response = delete_comment_request(db, comment_id="abc")

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_delete_comment_rolls_back_when_commit_fails() -> None:
    db = Mock(spec=Session)
    set_delete_comment_results(
        db,
        post=community_post(post_id=1),
        comment=community_comment(comment_id=1),
    )
    db.commit.side_effect = RuntimeError("db failed")

    response = delete_comment_request(db, raise_server_exceptions=False)

    assert response.status_code == 500
    db.rollback.assert_called_once()


def test_delete_comment_swagger_contract() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/community/posts/{postId}/comments/{commentId}"
    ]["delete"]

    assert set(operation["responses"]) == {"204", "404"}
    assert {parameter["name"] for parameter in operation["parameters"]} == {
        "postId",
        "commentId",
    }
    assert "requestBody" not in operation
    assert operation["tags"] == ["community"]
    assert operation["security"] == [{"HTTPBearer": []}]


# --- 커뮤니티 댓글 좋아요 토글 ---
# PATCH /api/v1/community/posts/{postId}/comments/{commentId}/like


def toggle_comment_like_request(
    db: Mock,
    *,
    post_id: int | str = 1,
    comment_id: int | str = 1,
    raise_server_exceptions: bool = True,
):
    with api_client(db, raise_server_exceptions=raise_server_exceptions) as client:
        return client.patch(
            f"/api/v1/community/posts/{post_id}/comments/{comment_id}/like"
        )


def community_comment_like(
    *,
    comment_id: int = 1,
    user_id: int = 1,
    is_liked: bool = True,
) -> CommentLike:
    return CommentLike(id=1, comment_id=comment_id, user_id=user_id, is_liked=is_liked)


def set_comment_like_results(
    db: Mock,
    *,
    post: Post | None,
    comment: Comment | None = None,
    comment_like: CommentLike | None = None,
    like_count: int = 0,
) -> list:
    """서비스가 조회하는 순서대로 게시글, 댓글, 좋아요 행, 좋아요 수를 지정합니다."""
    db.scalar.side_effect = [post, comment, comment_like, like_count]
    added: list = []
    db.add.side_effect = added.append
    return added


def test_toggle_comment_like_creates_liked_row_when_no_history() -> None:
    db = Mock(spec=Session)
    added = set_comment_like_results(
        db,
        post=community_post(post_id=1),
        comment=community_comment(comment_id=4, user_id=2),
        comment_like=None,
        like_count=3,
    )

    response = toggle_comment_like_request(db, post_id=1, comment_id=4)

    assert response.status_code == 200
    assert response.json() == {"isLiked": True, "likeCount": 3}
    assert len(added) == 1
    assert added[0].comment_id == 4
    assert added[0].user_id == 1
    assert added[0].is_liked is True
    db.commit.assert_called_once()


def test_toggle_comment_like_cancels_existing_like() -> None:
    db = Mock(spec=Session)
    comment_like = community_comment_like(is_liked=True)
    added = set_comment_like_results(
        db,
        post=community_post(post_id=1),
        comment=community_comment(comment_id=1),
        comment_like=comment_like,
        like_count=2,
    )

    response = toggle_comment_like_request(db)

    assert response.status_code == 200
    assert response.json() == {"isLiked": False, "likeCount": 2}
    assert comment_like.is_liked is False
    assert added == []
    db.delete.assert_not_called()
    db.commit.assert_called_once()


def test_toggle_comment_like_relikes_cancelled_like() -> None:
    db = Mock(spec=Session)
    comment_like = community_comment_like(is_liked=False)
    added = set_comment_like_results(
        db,
        post=community_post(post_id=1),
        comment=community_comment(comment_id=1),
        comment_like=comment_like,
        like_count=3,
    )

    response = toggle_comment_like_request(db)

    assert response.status_code == 200
    assert response.json() == {"isLiked": True, "likeCount": 3}
    assert comment_like.is_liked is True
    assert added == []
    db.commit.assert_called_once()


def test_toggle_comment_like_allows_liking_own_comment() -> None:
    db = Mock(spec=Session)
    set_comment_like_results(
        db,
        post=community_post(post_id=1),
        comment=community_comment(comment_id=1, user_id=1),
        comment_like=None,
        like_count=1,
    )

    response = toggle_comment_like_request(db)

    assert response.status_code == 200
    assert response.json() == {"isLiked": True, "likeCount": 1}


def test_toggle_comment_like_returns_zero_like_count_when_all_cancelled() -> None:
    db = Mock(spec=Session)
    set_comment_like_results(
        db,
        post=community_post(post_id=1),
        comment=community_comment(comment_id=1),
        comment_like=community_comment_like(is_liked=True),
        like_count=0,
    )

    response = toggle_comment_like_request(db)

    assert response.status_code == 200
    assert response.json() == {"isLiked": False, "likeCount": 0}


def test_toggle_comment_like_toggles_reported_post_and_comment() -> None:
    db = Mock(spec=Session)
    post = community_post(post_id=1)
    post.status = PostStatus.REPORTED
    set_comment_like_results(
        db,
        post=post,
        comment=community_comment(comment_id=1, status=CommentStatus.REPORTED),
        comment_like=None,
        like_count=1,
    )

    response = toggle_comment_like_request(db)

    assert response.status_code == 200
    assert response.json() == {"isLiked": True, "likeCount": 1}


def test_toggle_comment_like_returns_404_when_post_not_found() -> None:
    db = Mock(spec=Session)
    set_comment_like_results(db, post=None)

    response = toggle_comment_like_request(db)

    assert response.status_code == 404
    assert response.json() == POST_NOT_FOUND_RESPONSE
    assert db.scalar.call_count == 1
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_toggle_comment_like_returns_404_when_comment_not_found() -> None:
    db = Mock(spec=Session)
    set_comment_like_results(db, post=community_post(post_id=1), comment=None)

    response = toggle_comment_like_request(db)

    assert response.status_code == 404
    assert response.json() == COMMENT_NOT_FOUND_RESPONSE
    assert db.scalar.call_count == 2
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_toggle_comment_like_locks_visible_post_and_comment_of_post() -> None:
    db = Mock(spec=Session)
    set_comment_like_results(
        db,
        post=community_post(post_id=7),
        comment=community_comment(comment_id=9, post_id=7),
        comment_like=None,
        like_count=1,
    )

    toggle_comment_like_request(db, post_id=7, comment_id=9)

    post_query = compiled_query(db.scalar.call_args_list[0])
    assert "post.id = 7" in post_query
    assert "post.status IN ('ACTIVE', 'REPORTED')" in post_query
    assert "post.deleted_at IS NULL" in post_query
    assert "FOR UPDATE" in post_query
    assert "post.user_id" not in post_query.split("WHERE", 1)[1]

    comment_query = compiled_query(db.scalar.call_args_list[1])
    assert "comment.id = 9" in comment_query
    assert "comment.post_id = 7" in comment_query
    assert "comment.status IN ('ACTIVE', 'REPORTED')" in comment_query
    assert "comment.deleted_at IS NULL" in comment_query
    assert "FOR UPDATE" in comment_query
    # 삭제와 달리 작성자 조건으로 거르지 않아 남의 댓글에도 좋아요를 누를 수 있습니다.
    assert "comment.user_id" not in comment_query.split("WHERE", 1)[1]


def test_toggle_comment_like_queries_like_row_of_current_user() -> None:
    db = Mock(spec=Session)
    set_comment_like_results(
        db,
        post=community_post(post_id=1),
        comment=community_comment(comment_id=9),
        comment_like=None,
        like_count=1,
    )

    toggle_comment_like_request(db, comment_id=9)

    query = compiled_query(db.scalar.call_args_list[2])
    assert "comment_like.comment_id = 9" in query
    assert "comment_like.user_id = 1" in query


def test_toggle_comment_like_counts_only_liked_rows_after_flush() -> None:
    db = Mock(spec=Session)
    set_comment_like_results(
        db,
        post=community_post(post_id=1),
        comment=community_comment(comment_id=9),
        comment_like=None,
        like_count=1,
    )

    toggle_comment_like_request(db, comment_id=9)

    query = compiled_query(db.scalar.call_args_list[3])
    assert "count(comment_like.id)" in query
    assert "comment_like.comment_id = 9" in query
    assert "comment_like.is_liked IS true" in query
    db.flush.assert_called_once()


def test_toggle_comment_like_allows_minimum_path_ids() -> None:
    db = Mock(spec=Session)
    set_comment_like_results(
        db,
        post=community_post(post_id=1),
        comment=community_comment(comment_id=1),
        comment_like=None,
        like_count=1,
    )

    response = toggle_comment_like_request(db, post_id=1, comment_id=1)

    assert response.status_code == 200


def test_toggle_comment_like_returns_400_when_post_id_is_zero() -> None:
    db = Mock(spec=Session)

    response = toggle_comment_like_request(db, post_id=0)

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_toggle_comment_like_returns_400_when_comment_id_is_zero() -> None:
    db = Mock(spec=Session)

    response = toggle_comment_like_request(db, comment_id=0)

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_toggle_comment_like_returns_400_when_comment_id_is_not_number() -> None:
    db = Mock(spec=Session)

    response = toggle_comment_like_request(db, comment_id="abc")

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_toggle_comment_like_rolls_back_when_commit_fails() -> None:
    db = Mock(spec=Session)
    set_comment_like_results(
        db,
        post=community_post(post_id=1),
        comment=community_comment(comment_id=1),
        comment_like=None,
        like_count=1,
    )
    db.commit.side_effect = RuntimeError("db failed")

    response = toggle_comment_like_request(db, raise_server_exceptions=False)

    assert response.status_code == 500
    db.rollback.assert_called_once()


def test_toggle_comment_like_swagger_contract() -> None:
    operation = app.openapi()["paths"][
        "/api/v1/community/posts/{postId}/comments/{commentId}/like"
    ]["patch"]

    assert set(operation["responses"]) == {"200", "404"}
    assert {parameter["name"] for parameter in operation["parameters"]} == {
        "postId",
        "commentId",
    }
    assert "requestBody" not in operation
    assert operation["tags"] == ["community"]
    assert operation["security"] == [{"HTTPBearer": []}]


# --- 미션 진행도 반영: POST /api/v1/community/posts ---


def test_create_post_increases_community_post_mission_progress(
    mission_progress: Mock,
) -> None:
    db = Mock(spec=Session)
    collect_added_rows(db)

    with patch("app.community.service.upload_community_post_image"):
        response = create_post_request(db)

    assert response.status_code == 201
    mission_progress.assert_called_once_with(
        db=db,
        current_user_id=1,
        target_action=MissionTargetAction.COMMUNITY_POST,
    )


def test_create_post_does_not_increase_progress_when_request_is_invalid(
    mission_progress: Mock,
) -> None:
    db = Mock(spec=Session)

    response = create_post_request(
        db,
        data={"boardType": "FREE", "title": "   ", "content": "내용"},
    )

    assert response.status_code == 400
    mission_progress.assert_not_called()
