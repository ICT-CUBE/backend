"""블록체인 연동 중 발생하는 오류."""


class BlockchainError(Exception):
    """블록체인 서버 호출·응답 처리에 실패했을 때 발생합니다.

    `code`는 블록체인 서버가 준 오류 코드이거나 우리 쪽에서 붙인 코드입니다.
    이 예외를 API 응답으로 바꾸는 방식은 각 도메인 서비스가 정합니다.
    """

    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)
