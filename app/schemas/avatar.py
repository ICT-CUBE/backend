"""아바타 도메인 API 응답 스키마."""

from pydantic import BaseModel


class AvatarInteractionSessionCreateItemResponse(BaseModel):
    id: int


class AvatarInteractionSessionCreateResponse(BaseModel):
    avatarInteractionSession: AvatarInteractionSessionCreateItemResponse


class YezulFrameResponse(BaseModel):
    id: int
    title: str | None
    imageUrl: str


class YezulFramesResponse(BaseModel):
    yezulFrames: list[YezulFrameResponse]
