"""
==============================================================================
환경 변수 및 애플리케이션 중앙 설정 파일 (app/core/config.py)

[역할]
.env 파일이나 운영 서버(Azure)의 환경 변수 값들을 파이썬 코드로 불러와서
타입 검증(Pydantic)을 거쳐 안전하게 백엔드 전체에서 쓸 수 있도록 관리하는 "설정 센터"입니다.

[주요 기능]
1. .env 파일 자동 로딩 (Pydantic BaseSettings 사용)
2. DB 접속 URL (database_url) 자동 생성 (특수문자 인코딩 포함)
3. get_settings() 함수를 통해 백엔드 어디서든 동일한 설정을 빠르게 참조 (캐싱 적용)
==============================================================================
"""

from functools import lru_cache
from typing import Literal
from urllib.parse import quote_plus

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """로컬 `.env`와 Azure Container Apps 환경 변수를 동일하게 읽습니다."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "hanium-api"
    environment: Literal["local", "development", "staging", "production"] = "local"
    debug: bool = False
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "hanium"
    db_user: str = "hanium"
    db_password: SecretStr = SecretStr("CHANGE_ME_LOCAL_DB_PASSWORD")
    db_ssl: bool = False

    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-4.1-mini"

    @property
    def database_url(self) -> str:
        """특수문자가 포함된 계정 정보도 안전하게 SQLAlchemy URL로 변환합니다."""
        user = quote_plus(self.db_user)
        password = quote_plus(self.db_password.get_secret_value())
        database = quote_plus(self.db_name)
        return f"mysql+asyncmy://{user}:{password}@{self.db_host}:{self.db_port}/{database}"


@lru_cache
def get_settings() -> Settings:
    """요청마다 환경 변수를 다시 파싱하지 않도록 설정 객체를 캐시합니다."""
    return Settings()

