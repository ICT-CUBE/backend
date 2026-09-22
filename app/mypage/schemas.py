"""마이페이지 도메인 API 요청·응답 스키마."""

from datetime import datetime

from pydantic import field_validator

from app.core.enums import BoardType
from app.core.schemas import ApiSchema
from app.user.profile import ProfileCharacterCode, normalize_nickname


class MyPageUserResponse(ApiSchema):
    nickname: str | None
    email: str
    profile_character_img_url: str | None


class MyPageActivityResponse(ApiSchema):
    written_post_count: int
    commented_post_count: int


class MyPageResponse(ApiSchema):
    user: MyPageUserResponse
    activity: MyPageActivityResponse


class MyPageProfileUpdateRequest(ApiSchema):
    nickname: str
    profile_character_code: ProfileCharacterCode

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, value: str) -> str:
        return normalize_nickname(value)


class MyPagePostItemResponse(ApiSchema):
    id: int
    board_type: BoardType
    title: str
    content: str
    author_nickname: str | None
    created_at: datetime
    like_count: int
    comment_count: int
    is_liked: bool


class MyPagePaginationResponse(ApiSchema):
    page: int
    size: int
    has_next: bool


class MyPagePostsResponse(ApiSchema):
    posts: list[MyPagePostItemResponse]
    pagination: MyPagePaginationResponse
