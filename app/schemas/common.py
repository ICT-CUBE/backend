"""여러 API가 공통으로 사용하는 응답 schema."""

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """도메인 API 공통 오류 응답."""

    code: str = Field(examples=["RESOURCE_NOT_FOUND"])
    message: str = Field(examples=["요청한 정보를 찾을 수 없습니다."])
