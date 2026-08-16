"""인증 의존성.

실제 인증 구현 전까지는 고정 사용자 ID 1을 반환합니다.
"""


def get_current_user_id() -> int:
    return 1
