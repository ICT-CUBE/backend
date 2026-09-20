"""마이페이지 도메인 API 응답 스키마."""

from app.core.schemas import ApiSchema


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
