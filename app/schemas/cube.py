"""큐브 도메인 API 요청·응답 스키마."""

from pydantic import field_validator

from app.schemas.base import ApiSchema

AVATAR_NICKNAME_MAX_LENGTH = 30


class CubeVerificationRequest(ApiSchema):
    cube_id: int
    ownership_code: str


class CubeVerificationResponse(ApiSchema):
    cube_ownership_id: int


class CubeOwnershipAvatarNicknameUpdateRequest(ApiSchema):
    avatar_nickname: str

    @field_validator("avatar_nickname")
    @classmethod
    def validate_avatar_nickname(cls, value: str) -> str:
        # 앞뒤 공백을 제거한 값으로 길이를 검증하고, 그 값을 그대로 저장합니다.
        stripped_value = value.strip()
        if not stripped_value or len(stripped_value) > AVATAR_NICKNAME_MAX_LENGTH:
            raise ValueError("avatarNickname must be 1 to 30 characters")
        return stripped_value
