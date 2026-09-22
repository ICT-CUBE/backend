"""인증 도메인 API 요청·응답 스키마."""

from datetime import datetime

from pydantic import EmailStr, Field, field_validator

from app.core.schemas import ApiSchema
from app.user.profile import ProfileCharacterCode, normalize_nickname


class SignupRequest(ApiSchema):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=64)
    nickname: str
    profile_character_code: ProfileCharacterCode

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        # 형식 검증 전에 앞뒤 공백을 제거하고 소문자로 통일합니다.
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, value: str) -> str:
        return normalize_nickname(value)


class LoginRequest(ApiSchema):
    email: EmailStr = Field(max_length=255)
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        # 조회 전에 앞뒤 공백을 제거하고 소문자로 통일합니다.
        if isinstance(value, str):
            return value.strip().lower()
        return value


class AuthUserResponse(ApiSchema):
    id: int


class AuthTokenResponse(ApiSchema):
    access_token: str
    token_type: str
    expires_in: int
    expires_at: datetime


class AuthResponse(ApiSchema):
    """회원가입과 로그인이 함께 쓰는 사용자·토큰 응답입니다."""

    user: AuthUserResponse
    auth: AuthTokenResponse
