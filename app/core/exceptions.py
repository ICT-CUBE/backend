"""API에서 공통으로 사용하는 도메인 오류와 응답 처리기."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    """클라이언트에 상태 코드와 오류 코드를 전달하는 예외."""

    def __init__(self, *, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    """도메인 오류를 정해진 JSON 형식으로 변환합니다."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )


async def request_validation_error_handler(
    _: Request, __: RequestValidationError
) -> JSONResponse:
    """잘못된 Path·Query·Body를 프로젝트 공통 400 형식으로 반환합니다."""
    return JSONResponse(
        status_code=400,
        content={
            "code": "INVALID_REQUEST",
            "message": "요청값이 올바르지 않습니다.",
        },
    )
