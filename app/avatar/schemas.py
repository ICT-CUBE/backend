"""아바타 도메인 API 응답 스키마."""

from app.core.schemas import ApiSchema


class AvatarInteractionSessionCreateItemResponse(ApiSchema):
    id: int


class AvatarInteractionSessionCreateResponse(ApiSchema):
    avatar_interaction_session: AvatarInteractionSessionCreateItemResponse


class YezulFrameResponse(ApiSchema):
    id: int
    title: str | None
    image_url: str


class YezulFramesResponse(ApiSchema):
    yezul_frames: list[YezulFrameResponse]
