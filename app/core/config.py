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

    # Azure Blob Storage 설정입니다. 실제 연결 문자열은 Git에 올리지 않고
    # 로컬/배포 환경 변수로만 주입합니다.
    azure_storage_connection_string: str = Field(default="")
    azure_storage_container_name: str = Field(default="hanium")
    azure_storage_stage_capture_prefix: str = Field(default="stage_capture")
    azure_storage_track_capture_prefix: str = Field(default="track_capture")

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
        return {"ssl": {"ca": "/etc/ssl/certs/ca-certificates.crt"}}


@lru_cache
def get_settings() -> Settings:
    return Settings()
