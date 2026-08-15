"""API 스키마 공통 설정."""

from pydantic import BaseModel, ConfigDict


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


class ApiSchema(BaseModel):
    """내부에서는 snake_case, 요청/응답 JSON에서는 camelCase를 사용합니다."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
