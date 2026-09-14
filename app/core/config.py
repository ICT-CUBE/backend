import ssl
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "hanium-api"
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    api_v1_prefix: str = Field(default="/api/v1")

    mysql_host: str = Field(default="localhost")
    mysql_port: int = Field(default=3306)
    mysql_database: str = Field(default="hanium")
    mysql_user: str = Field(default="hanium")
    mysql_password: str = Field(default="hanium_password")
    mysql_ssl_enabled: bool = Field(default=False)

    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-4.1-mini")

    chroma_host: str = Field(default="localhost")
    chroma_port: int = Field(default=8000)
    chroma_ssl_enabled: bool = Field(default=False)
    chroma_collection_name: str = Field(default="jenny_knowledge")

    # JWT Access Token 설정입니다. 비밀키는 Git에 올리지 않고
    # 로컬/배포 환경 변수로만 주입합니다.
    jwt_secret_key: str = Field(default="")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_days: int = Field(default=365)

    # Azure Blob Storage 설정입니다. 실제 연결 문자열은 Git에 올리지 않고
    # 로컬/배포 환경 변수로만 주입합니다.
    azure_storage_connection_string: str = Field(default="")
    azure_storage_container_name: str = Field(default="hanium")
    azure_storage_stage_capture_prefix: str = Field(default="stage_capture")
    azure_storage_track_capture_prefix: str = Field(default="track_capture")
    azure_storage_avatar_interaction_picture_prefix: str = Field(
        default="avatar_interaction_picture"
    )
    azure_storage_conversation_audio_prefix: str = Field(
        default="conversation_audio"
    )
    azure_storage_community_post_prefix: str = Field(default="community_post")

    # ARZONE Blockchain Server 연동 설정입니다. secret은 Git에 올리지 않고
    # 로컬/배포 환경 변수로만 주입합니다.
    blockchain_base_url: str = Field(default="http://127.0.0.1:3100")
    blockchain_network: str = Field(default="localhost")
    blockchain_hmac_key_id: str = Field(default="")
    blockchain_hmac_key_secret: str = Field(default="")
    blockchain_approval_jwt_secret: str = Field(default="")
    blockchain_approval_jwt_issuer: str = Field(default="arzone-backend")
    blockchain_approval_jwt_audience: str = Field(default="arzone-blockchain-server")
    blockchain_approval_jwt_expire_minutes: int = Field(default=10)
    blockchain_webhook_hmac_key_id: str = Field(default="")
    blockchain_webhook_hmac_key_secret: str = Field(default="")
    blockchain_request_timeout_seconds: int = Field(default=15)
    blockchain_confirmation_timeout_seconds: int = Field(default=120)
    blockchain_confirmation_poll_seconds: float = Field(default=2.0)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            "?charset=utf8mb4"
        )

    @property
    def database_connect_args(self) -> dict[str, object]:
        if not self.mysql_ssl_enabled:
            return {}
        # 운영체제의 기본 CA 저장소를 사용해 Linux 배포 컨테이너와 Windows 관리
        # 스크립트 모두 Azure MySQL 인증서를 검증할 수 있게 합니다.
        return {"ssl": ssl.create_default_context()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
