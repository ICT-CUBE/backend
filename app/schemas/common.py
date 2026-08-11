"""여러 API에서 공통으로 사용하는 응답 스키마."""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    code: str
    message: str
