"""클라이언트에 일관된 형태로 전달하는 API 예외."""

from fastapi import Request
from fastapi.responses import JSONResponse


class ApiError(Exception):
    """API 명세의 code/message 오류 응답을 만들기 위한 예외입니다."""

    def __init__(self, *, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    """FastAPI 기본 detail 래퍼 없이 명세 그대로 오류 JSON을 반환합니다."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )
