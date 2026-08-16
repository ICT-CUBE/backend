"""FastAPI가 자동 생성하는 OpenAPI 문서를 프로젝트 규칙에 맞춥니다."""

from collections.abc import Callable
from typing import Any

from fastapi import FastAPI


def configure_openapi(app: FastAPI) -> None:
    """런타임에서 400으로 처리하는 자동 422 응답을 Swagger에서도 제거합니다."""
    original_openapi: Callable[[], dict[str, Any]] = app.openapi

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema is not None:
            return app.openapi_schema

        schema = original_openapi()
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
                )
                if validation_schema.get("$ref") == (
                    "#/components/schemas/HTTPValidationError"
                ):
                    responses.pop("422", None)

        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi  # type: ignore[method-assign]
