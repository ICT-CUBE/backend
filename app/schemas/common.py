"""여러 API에서 공통으로 사용하는 응답 스키마."""

from app.schemas.base import ApiSchema


class ErrorResponse(ApiSchema):
    code: str
    message: str
