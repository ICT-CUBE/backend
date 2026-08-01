"""OpenAI API 클라이언트 생성 헬퍼."""

from openai import AsyncOpenAI

from app.core.config import get_settings


def get_openai_client() -> AsyncOpenAI:
    """키가 설정된 경우에만 클라이언트를 만듭니다.

    실제 기능의 서비스 계층에서 호출하세요. 키가 없는 로컬 개발에서도 서버 자체는
    정상 기동되도록 애플리케이션 시작 시에는 클라이언트를 만들지 않습니다.
    """
    api_key = get_settings().openai_api_key
    if api_key is None or not api_key.get_secret_value():
        raise RuntimeError("OPENAI_API_KEY is not configured")
    return AsyncOpenAI(api_key=api_key.get_secret_value())

