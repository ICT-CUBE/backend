"""DB 없이 확인 가능한 기본 생존 API 테스트."""

from fastapi.testclient import TestClient

from app.main import app


def test_liveness() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

