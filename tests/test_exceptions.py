"""공통 예외 처리기 테스트."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_unhandled_exception_returns_common_500_response() -> None:
    # debug가 켜져 있으면 Starlette이 공통 핸들러 대신 HTML 트레이스백을 반환하므로,
    # 배포 환경과 같은 debug=false 설정으로 앱을 만들어 검증합니다.
    with patch("app.main.get_settings", return_value=Settings(debug=False)):
        app = create_app()

    @app.get("/boom")
    def boom() -> None:
        raise RuntimeError("unexpected")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/boom")

    assert response.status_code == 500
    assert response.json() == {
        "code": "INTERNAL_SERVER_ERROR",
        "message": "서버 내부 오류가 발생했습니다.",
    }
