"""실제 API 오류 처리와 Swagger 문서를 일치시키는 설정."""

from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def configure_openapi(app: FastAPI) -> None:
    """자동 생성되는 422 문서를 제거하고 공통 400 응답 문서를 사용합니다."""

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema is not None:
            return app.openapi_schema

        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        for path_item in schema.get("paths", {}).values():
            for operation in path_item.values():
                if not isinstance(operation, dict):
                    continue
                responses = operation.get("responses", {})
                validation_response = responses.get("422", {})
                validation_schema = (
                    validation_response.get("content", {})
                    .get("application/json", {})
                    .get("schema", {})
                    .get("$ref")
                )
                if validation_schema == "#/components/schemas/HTTPValidationError":
                    responses.pop("422", None)

        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi  # type: ignore[method-assign]
