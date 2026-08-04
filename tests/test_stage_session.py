"""스테이지 재생 세션 생성 API 테스트."""

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user_id
from app.db.session import get_db_session
from app.main import app
from app.models.album import StageSession
from app.models.enums import PlaybackStatus, ViewMode


def make_session_with_scalar_results(*values: int | None) -> AsyncMock:
    session = AsyncMock(spec=AsyncSession)
    session.scalar.side_effect = values

    def assign_created_id(model: object) -> None:
        if isinstance(model, StageSession):
            model.id = 501

    session.add.side_effect = assign_created_id
    return session


def request_stage_session(
    session: AsyncMock,
    *,
    stage_id: int = 1,
    body: dict[str, str] | None = None,
):
    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db_session] = override_db_session
    app.dependency_overrides[get_current_user_id] = lambda: 1
    try:
        with TestClient(app) as client:
            return client.post(
                f"/api/v1/stages/{stage_id}/sessions",
                json=body if body is not None else {"viewMode": "AR"},
            )
    finally:
        app.dependency_overrides.clear()


def test_create_stage_session_saves_enum_values() -> None:
    session = make_session_with_scalar_results(1, 12)

    response = request_stage_session(session)

    assert response.status_code == 201
    assert response.json() == {
        "stageSession": {
            "id": 501,
            "viewMode": "AR",
        }
    }
    saved_session = session.add.call_args.args[0]
    assert isinstance(saved_session, StageSession)
    assert saved_session.stage_id == 1
    assert saved_session.cube_ownership_id == 12
    assert saved_session.view_mode is ViewMode.AR
    assert saved_session.status is PlaybackStatus.PLAYING
    session.flush.assert_awaited_once()
    session.commit.assert_awaited_once()


def test_create_stage_session_returns_404_when_stage_is_missing() -> None:
    response = request_stage_session(make_session_with_scalar_results(None))

    assert response.status_code == 404
    assert response.json() == {
        "code": "STAGE_NOT_FOUND",
        "message": "스테이지 영상을 찾을 수 없습니다.",
    }


def test_create_stage_session_returns_404_without_active_ownership() -> None:
    response = request_stage_session(make_session_with_scalar_results(1, None))

    assert response.status_code == 404
    assert response.json() == {
        "code": "ACTIVE_CUBE_OWNERSHIP_NOT_FOUND",
        "message": "활성화된 큐브 소유권을 찾을 수 없습니다.",
    }


def test_create_stage_session_returns_400_for_invalid_view_mode() -> None:
    response = request_stage_session(
        make_session_with_scalar_results(),
        body={"viewMode": "INVALID"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_REQUEST",
        "message": "요청값이 올바르지 않습니다.",
    }


def test_stage_session_swagger_has_no_automatic_422() -> None:
    responses = app.openapi()["paths"]["/api/v1/stages/{stageId}/sessions"]["post"][
        "responses"
    ]

    assert "400" in responses
    assert "404" in responses
    assert "500" in responses
    assert "422" not in responses
