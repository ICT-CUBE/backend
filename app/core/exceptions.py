"""API 오류를 일관된 JSON 형식으로 반환하는 예외 처리기."""

import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ApiError(Exception):
    """클라이언트에 code와 message를 전달하는 도메인 예외."""

    def __init__(self, *, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    """도메인 예외를 공통 오류 응답으로 변환합니다."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )


async def request_validation_error_handler(
    _: Request, __: RequestValidationError
) -> JSONResponse:
    """잘못된 Path·Query·Body 입력을 프로젝트 공통 400 응답으로 변환합니다."""
    return JSONResponse(
        status_code=400,
        content={
            "code": "INVALID_REQUEST",
            "message": "요청값이 올바르지 않습니다.",
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """예상하지 못한 오류의 상세 내용을 숨기고 공통 500 응답을 반환합니다."""
    logger.exception("Unhandled API error: path=%s", request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_SERVER_ERROR",
            "message": "서버 오류가 발생했습니다.",
        },
    )
