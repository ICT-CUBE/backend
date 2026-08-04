"""홈 정보 조회 API의 정상 응답과 소유권 없음 응답 테스트."""

from collections.abc import AsyncIterator
from datetime import datetime
from unittest.mock import AsyncMock, Mock

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user_id
from app.db.session import get_db_session
from app.main import app
from app.models.cube import Affinity, Cube, CubeOwnership
from app.models.enums import CubeStatus, LevelName, LoginProvider, OwnershipStatus, UserStatus
from app.models.reward import Level
from app.models.user import User


def make_home_row() -> tuple[User, CubeOwnership, Cube, Affinity, Level]:
    """정상 응답 예시와 같은 가짜 DB 조회 결과(ORM 객체 묶음)를 만듭니다."""
    # 1. 가짜 사용자 데이터 (User)
    user = User(
        id=1,
        email="user@example.com",
        login_provider=LoginProvider.EMAIL,
        status=UserStatus.ACTIVE,
        profile_character_img_code="PROFILE_01",
    )
    # 2. 가짜 큐브 소유권 데이터 (CubeOwnership)
    ownership = CubeOwnership(
        id=12,
        user_id=1,
        cube_id=15,
        avatar_nickname="젠득이",
        ownership_status=OwnershipStatus.ACTIVE,
        is_last_accessed=True,
        acquired_at=datetime(2026, 3, 19, 10, 30),
    )
    # 3. 가짜 큐브 데이터 (Cube)
    cube = Cube(
        id=15,
        serial_number="TEST-CUBE-001",
        product_name="JENNIE CUBE",
        ownership_code_hash="not-used-in-this-test",
        artist_name="JENNIE",
        status=CubeStatus.OWNED,
    )
    # 4. 가짜 친밀도 데이터 (Affinity)
    affinity = Affinity(id=7, cube_ownership_id=12, level_id=3, current_xp=1245)
    # 5. 가짜 레벨 정보 (Level)
    level = Level(
        id=3,
        reward_item_id=1,
        level=3,
        level_xp=2000,
        level_name=LevelName.CLOSE,
    )
    return user, ownership, cube, affinity, level


def make_session_returning(row: object | None) -> AsyncMock:
    """실제 DB에 접속하는 대신 테스트용 가짜 DB 세션(Mock Session)을 생성합니다.

    `session.execute(statement).one_or_none()` 실행 시 넘겨받은 `row` 값을
    그대로 반환하도록 연기합니다.
    """
    result = Mock()
    result.one_or_none.return_value = row
    session = AsyncMock(spec=AsyncSession)
    session.execute.return_value = result
    return session


def test_get_home_returns_expected_response_shape() -> None:
    """활성화된 큐브가 있을 때 홈 정보를 200 OK로 반환하는지 테스트합니다."""
    # 가짜 DB 데이터 묶음을 리턴하는 가짜 세션 생성
    session = make_session_returning(make_home_row())

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    # 실제 DB 연결과 현재 사용자 ID 의존성을 테스트용으로 교체합니다.
    app.dependency_overrides[get_db_session] = override_db_session
    app.dependency_overrides[get_current_user_id] = lambda: 1
    try:
        # FastAPI 가상 클라이언트로 GET /api/v1/users/me/home 요청 전송
        with TestClient(app) as client:
            response = client.get("/api/v1/users/me/home")
    finally:
        # 테스트 종료 후 주입했던 가짜 설정들 원복
        app.dependency_overrides.clear()

    # 검증 1: HTTP 응답 코드가 200 OK 인가?
    assert response.status_code == 200
    # 검증 2: API 응답 JSON 구조가 정의된 응답 형식과 완전히 동일한가?
    assert response.json() == {
        "user": {"id": 1, "profileCharacterImgCode": "PROFILE_01"},
        "cubeOwnership": {
            "id": 12,
            "avatarNickname": "젠득이",
            "acquiredAt": "2026-03-19T10:30:00",
        },
        "cube": {"id": 15, "artistName": "JENNIE"},
        "affinity": {
            "id": 7,
            "currentXp": 1245,
            "level": {
                "id": 3,
                "level": 3,
                "levelName": "Close",
                "levelXp": 2000,
            },
        },
    }
    # 검증 3: DB 쿼리가 실제로 1회 호출되었는가?
    session.execute.assert_awaited_once()


def test_get_home_returns_404_without_active_ownership() -> None:
    """큐브 소유권이 없을 때 404 오류를 반환하는지 테스트합니다."""
    # DB 결과가 None(데이터 없음)을 리턴하도록 설정된 가짜 세션 생성
    session = make_session_returning(None)

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db_session] = override_db_session
    app.dependency_overrides[get_current_user_id] = lambda: 1
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/users/me/home")
    finally:
        app.dependency_overrides.clear()

    # 검증 1: HTTP 응답 코드가 404 NOT FOUND 인가?
    assert response.status_code == 404
    # 검증 2: CUBE_OWNERSHIP_NOT_FOUND 에러 구조로 반환되었는가?
    assert response.json() == {
        "code": "CUBE_OWNERSHIP_NOT_FOUND",
        "message": "큐브 소유권 정보를 찾을 수 없습니다.",
    }
