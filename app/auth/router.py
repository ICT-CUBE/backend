"""인증 도메인 API 라우터."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.schemas import AuthResponse, LoginRequest, SignupRequest
from app.auth.service import login_with_email, signup_with_email
from app.core.database import get_db
from app.core.schemas import ErrorResponse

router = APIRouter()


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="이메일 회원가입",
    description=(
        "이메일 사용자와 기본 알림 설정을 생성하고 365일 동안 사용할 "
        "Access Token을 발급합니다."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "필수 필드가 없거나, 이메일 형식이 아니거나, 비밀번호가 8~64자가 "
                "아니거나, 닉네임이 1~20자가 아니거나, 허용하지 않는 프로필 캐릭터 코드"
            ),
            "content": {
                "application/json": {
                    "example": {
                        "code": "INVALID_REQUEST",
                        "message": "요청값이 올바르지 않습니다.",
                    }
                }
            },
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "같은 이메일을 사용하는 사용자가 이미 존재함",
            "content": {
                "application/json": {
                    "example": {
                        "code": "EMAIL_ALREADY_EXISTS",
                        "message": "이미 사용 중인 이메일입니다.",
                    }
                }
            },
        },
    },
)
def signup(
    body: SignupRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AuthResponse:
    """POST /api/v1/auth/signup"""
    return signup_with_email(
        db=db,
        email=body.email,
        password=body.password,
        nickname=body.nickname,
        profile_character_code=body.profile_character_code,
    )


@router.post(
    "/login/email",
    response_model=AuthResponse,
    summary="이메일 로그인",
    description=(
        "이메일과 비밀번호로 사용자를 확인하고 365일 동안 사용할 Access Token을 "
        "새로 발급합니다."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "필수 필드가 없거나 이메일 형식·길이가 올바르지 않음",
            "content": {
                "application/json": {
                    "example": {
                        "code": "INVALID_REQUEST",
                        "message": "요청값이 올바르지 않습니다.",
                    }
                }
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "로그인할 수 있는 사용자가 없거나 비밀번호가 일치하지 않음",
            "content": {
                "application/json": {
                    "example": {
                        "code": "INVALID_CREDENTIALS",
                        "message": "이메일 또는 비밀번호가 올바르지 않습니다.",
                    }
                }
            },
        },
    },
)
def login(
    body: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AuthResponse:
    """POST /api/v1/auth/login/email"""
    return login_with_email(db=db, email=body.email, password=body.password)
