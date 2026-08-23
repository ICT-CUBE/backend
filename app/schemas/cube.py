"""큐브 도메인 API 요청·응답 스키마."""

from app.schemas.base import ApiSchema


class CubeVerificationRequest(ApiSchema):
    cube_id: int
    ownership_code: str


class CubeVerificationResponse(ApiSchema):
    cube_ownership_id: int
