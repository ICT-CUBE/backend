"""커뮤니티 도메인 API 요청·응답 스키마."""

from datetime import datetime
from enum import StrEnum

from app.models.enums import BoardType
from app.schemas.base import ApiSchema


class CommunityBoardFilter(StrEnum):
    ALL = "ALL"
    FREE = "FREE"
    CERTIFICATION = "CERTIFICATION"


class CommunityPostAuthorResponse(ApiSchema):
    id: int
    nickname: str | None
    profile_image_url: str | None


class CommunityPostItemResponse(ApiSchema):
    id: int
    board_type: BoardType
    title: str
    content: str
    author: CommunityPostAuthorResponse
    created_at: datetime
    like_count: int
    comment_count: int
    is_liked: bool
    is_mine: bool


class CommunityCommentItemResponse(ApiSchema):
    id: int
    author: CommunityPostAuthorResponse
    content: str
    created_at: datetime
    like_count: int
    is_liked: bool
    is_mine: bool


class CommunityPostDetailItemResponse(ApiSchema):
    id: int
    board_type: BoardType
    author: CommunityPostAuthorResponse
    created_at: datetime
    title: str
    content: str
    image_urls: list[str]
    like_count: int
    is_liked: bool
    comment_count: int
    is_mine: bool
    comments: list[CommunityCommentItemResponse]


class CommunityPostDetailResponse(ApiSchema):
    post: CommunityPostDetailItemResponse


class CommunityPostCreateResponse(ApiSchema):
    post_id: int


class CommunityPaginationResponse(ApiSchema):
    page: int
    size: int
    has_next: bool


class CommunityPostsResponse(ApiSchema):
    posts: list[CommunityPostItemResponse]
    pagination: CommunityPaginationResponse
