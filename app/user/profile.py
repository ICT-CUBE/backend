"""회원가입과 프로필 수정이 함께 쓰는 닉네임·프로필 캐릭터 규칙."""

from enum import StrEnum

NICKNAME_MAX_LENGTH = 20
PROFILE_IMAGE_URL_FORMAT = (
    "https://haniumstorage.blob.core.windows.net/hanium/profile_image/{code}.png"
)


class ProfileCharacterCode(StrEnum):
    PROFILE_001 = "profile_001"
    PROFILE_002 = "profile_002"
    PROFILE_003 = "profile_003"


def normalize_nickname(value: str) -> str:
    """앞뒤 공백을 제거한 닉네임을 검증해 반환합니다."""
    # 앞뒤 공백을 제거한 값으로 길이를 검증하고, 그 값을 그대로 저장합니다.
    stripped_value = value.strip()
    if not stripped_value or len(stripped_value) > NICKNAME_MAX_LENGTH:
        raise ValueError("nickname must be 1 to 20 characters")
    return stripped_value


def to_profile_image_url(code: ProfileCharacterCode) -> str:
    """프로필 캐릭터 코드를 저장할 이미지 절대 URL로 변환합니다."""
    return PROFILE_IMAGE_URL_FORMAT.format(code=code.value)
