"""마이페이지 도메인 API 테스트."""

from unittest.mock import Mock

from sqlalchemy.orm import Session

from app.main import app
from app.models.enums import LoginProvider, UserStatus
from app.models.user import User
from tests.conftest import api_client


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
