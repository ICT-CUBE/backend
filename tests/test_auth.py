"""인증 도메인 API 테스트."""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.main import app
from app.models.account import UserSetting
from app.models.enums import LoginProvider, UserStatus
from app.models.user import User
from tests.conftest import api_client

INVALID_REQUEST_RESPONSE = {
    "code": "INVALID_REQUEST",
    "message": "요청값이 올바르지 않습니다.",
}
EMAIL_ALREADY_EXISTS_RESPONSE = {
    "code": "EMAIL_ALREADY_EXISTS",
    "message": "이미 사용 중인 이메일입니다.",
}
PROFILE_IMAGE_URL_PREFIX = (
    "https://haniumstorage.blob.core.windows.net/hanium/profile_image"
)
KOREA_TIMEZONE = timezone(timedelta(hours=9))


def signup_request(
    db: Mock,
    *,
    body: dict[str, str] | None = None,
    raise_server_exceptions: bool = True,
):
    with api_client(db, raise_server_exceptions=raise_server_exceptions) as client:
        return client.post(
            "/api/v1/auth/signup",
            json=body
            if body is not None
            else {
                "email": "user@example.com",
                "password": "password123!",
                "nickname": "아르조니",
                "profileCharacterCode": "profile_001",
            },
        )


def set_signup_results(db: Mock, *, existing_user_id: int | None = None) -> list:
    """이메일 중복 조회 결과를 지정하고 저장된 ORM 객체를 모읍니다."""
    db.scalar.return_value = existing_user_id
    added: list = []
    db.add.side_effect = added.append

    def assign_user_id() -> None:
        added[0].id = 11

    db.flush.side_effect = assign_user_id
    return added


def compiled_query(call) -> str:
    return str(call.args[0].compile(compile_kwargs={"literal_binds": True}))


def test_signup_creates_user_with_default_setting_and_token() -> None:
    db = Mock(spec=Session)
    added = set_signup_results(db)

    response = signup_request(db)

    assert response.status_code == 201
    body = response.json()
    assert body["user"] == {"id": 11}
    assert body["auth"]["tokenType"] == "Bearer"
    assert body["auth"]["expiresIn"] == 31536000
    assert set(body["auth"]) == {
        "accessToken",
        "tokenType",
        "expiresIn",
        "expiresAt",
    }

    user = added[0]
    assert isinstance(user, User)
    assert user.email == "user@example.com"
    assert user.nickname == "아르조니"
    assert user.login_provider == LoginProvider.EMAIL
    assert user.provider_user_id is None
    assert user.status == UserStatus.ACTIVE
    assert user.chat_violation_count == 0
    assert user.deleted_at is None
    assert user.profile_character_img_url == (
        f"{PROFILE_IMAGE_URL_PREFIX}/profile_001.png"
    )
    db.flush.assert_called_once()
    db.commit.assert_called_once()


def test_signup_stores_argon2id_hash_instead_of_raw_password() -> None:
    db = Mock(spec=Session)
    added = set_signup_results(db)

    response = signup_request(db)

    assert response.status_code == 201
    password_hash = added[0].password_hash
    assert password_hash.startswith("$argon2id$")
    assert "password123!" not in password_hash
    assert "password123!" not in response.text


def test_signup_creates_user_setting_with_all_notifications_enabled() -> None:
    db = Mock(spec=Session)
    added = set_signup_results(db)

    signup_request(db)

    setting = added[1]
    assert isinstance(setting, UserSetting)
    assert setting.user_id == 11
    assert setting.push_enabled is True
    assert setting.new_conversation_enabled is True
    assert setting.affinity_change_enabled is True
    assert setting.daily_mission_refresh_enabled is True
    assert setting.trade_completed_enabled is True
    assert setting.trade_offer_enabled is True
    assert setting.community_comment_notice_enabled is True


def test_signup_issues_access_token_signed_with_configured_secret() -> None:
    db = Mock(spec=Session)
    set_signup_results(db)

    response = signup_request(db)

    body = response.json()
    settings = get_settings()
    payload = jwt.decode(
        body["auth"]["accessToken"],
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
    assert payload["sub"] == "11"
    assert payload["exp"] - payload["iat"] == 31536000
    expires_at = datetime.fromtimestamp(payload["exp"], tz=KOREA_TIMEZONE)
    assert body["auth"]["expiresAt"] == expires_at.replace(tzinfo=None).isoformat()


def test_signup_normalizes_email_before_saving() -> None:
    db = Mock(spec=Session)
    added = set_signup_results(db)

    response = signup_request(
        db,
        body={
            "email": "  User@Example.COM  ",
            "password": "password123!",
            "nickname": "아르조니",
            "profileCharacterCode": "profile_001",
        },
    )

    assert response.status_code == 201
    assert added[0].email == "user@example.com"
    assert (
        "\"user\".email = 'user@example.com'" in compiled_query(db.scalar.call_args)
    )


def test_signup_strips_nickname_before_saving() -> None:
    db = Mock(spec=Session)
    added = set_signup_results(db)

    response = signup_request(
        db,
        body={
            "email": "user@example.com",
            "password": "password123!",
            "nickname": "  아르조니  ",
            "profileCharacterCode": "profile_001",
        },
    )

    assert response.status_code == 201
    assert added[0].nickname == "아르조니"


def test_signup_builds_profile_image_url_from_character_code() -> None:
    db = Mock(spec=Session)
    added = set_signup_results(db)

    response = signup_request(
        db,
        body={
            "email": "user@example.com",
            "password": "password123!",
            "nickname": "아르조니",
            "profileCharacterCode": "profile_003",
        },
    )

    assert response.status_code == 201
    assert added[0].profile_character_img_url == (
        f"{PROFILE_IMAGE_URL_PREFIX}/profile_003.png"
    )


def test_signup_allows_minimum_password_and_nickname_length() -> None:
    db = Mock(spec=Session)
    added = set_signup_results(db)

    response = signup_request(
        db,
        body={
            "email": "user@example.com",
            "password": "12345678",
            "nickname": "가",
            "profileCharacterCode": "profile_001",
        },
    )

    assert response.status_code == 201
    assert added[0].nickname == "가"


def test_signup_allows_maximum_password_and_nickname_length() -> None:
    db = Mock(spec=Session)
    added = set_signup_results(db)

    response = signup_request(
        db,
        body={
            "email": "user@example.com",
            "password": "a" * 64,
            "nickname": "가" * 20,
            "profileCharacterCode": "profile_001",
        },
    )

    assert response.status_code == 201
    assert added[0].nickname == "가" * 20


def test_signup_returns_400_when_password_is_too_short() -> None:
    db = Mock(spec=Session)

    response = signup_request(
        db,
        body={
            "email": "user@example.com",
            "password": "1234567",
            "nickname": "아르조니",
            "profileCharacterCode": "profile_001",
        },
    )

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.add.assert_not_called()


def test_signup_returns_400_when_password_is_too_long() -> None:
    db = Mock(spec=Session)

    response = signup_request(
        db,
        body={
            "email": "user@example.com",
            "password": "a" * 65,
            "nickname": "아르조니",
            "profileCharacterCode": "profile_001",
        },
    )

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.add.assert_not_called()


def test_signup_returns_400_when_nickname_is_blank() -> None:
    db = Mock(spec=Session)

    response = signup_request(
        db,
        body={
            "email": "user@example.com",
            "password": "password123!",
            "nickname": "   ",
            "profileCharacterCode": "profile_001",
        },
    )

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.add.assert_not_called()


def test_signup_returns_400_when_nickname_is_too_long() -> None:
    db = Mock(spec=Session)

    response = signup_request(
        db,
        body={
            "email": "user@example.com",
            "password": "password123!",
            "nickname": "가" * 21,
            "profileCharacterCode": "profile_001",
        },
    )

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.add.assert_not_called()


def test_signup_returns_400_for_invalid_email_format() -> None:
    db = Mock(spec=Session)

    response = signup_request(
        db,
        body={
            "email": "user-example.com",
            "password": "password123!",
            "nickname": "아르조니",
            "profileCharacterCode": "profile_001",
        },
    )

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.add.assert_not_called()


def test_signup_returns_400_when_email_exceeds_max_length() -> None:
    db = Mock(spec=Session)
    long_email = f"{'a' * 250}@example.com"

    response = signup_request(
        db,
        body={
            "email": long_email,
            "password": "password123!",
            "nickname": "아르조니",
            "profileCharacterCode": "profile_001",
        },
    )

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.add.assert_not_called()


def test_signup_returns_400_for_unsupported_profile_character_code() -> None:
    db = Mock(spec=Session)

    response = signup_request(
        db,
        body={
            "email": "user@example.com",
            "password": "password123!",
            "nickname": "아르조니",
            "profileCharacterCode": "profile_009",
        },
    )

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.add.assert_not_called()


def test_signup_returns_400_when_required_field_is_missing() -> None:
    db = Mock(spec=Session)

    response = signup_request(
        db,
        body={
            "email": "user@example.com",
            "password": "password123!",
            "nickname": "아르조니",
        },
    )

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.add.assert_not_called()


def test_signup_returns_409_when_email_is_already_used() -> None:
    db = Mock(spec=Session)
    set_signup_results(db, existing_user_id=1)

    response = signup_request(db)

    assert response.status_code == 409
    assert response.json() == EMAIL_ALREADY_EXISTS_RESPONSE
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_signup_returns_409_when_unique_constraint_is_violated() -> None:
    db = Mock(spec=Session)
    set_signup_results(db)
    db.commit.side_effect = IntegrityError(
        "INSERT INTO user",
        {},
        Exception("Duplicate entry for key 'uk_user_email'"),
    )

    response = signup_request(db)

    assert response.status_code == 409
    assert response.json() == EMAIL_ALREADY_EXISTS_RESPONSE
    db.rollback.assert_called_once()


def test_signup_rolls_back_when_commit_fails() -> None:
    db = Mock(spec=Session)
    set_signup_results(db)
    db.commit.side_effect = RuntimeError("db failed")

    response = signup_request(db, raise_server_exceptions=False)

    assert response.status_code == 500
    db.rollback.assert_called_once()


def test_signup_swagger_contract() -> None:
    openapi_schema = app.openapi()
    operation = openapi_schema["paths"]["/api/v1/auth/signup"]["post"]

    assert set(operation["responses"]) == {"201", "400", "409"}
    request_ref = operation["requestBody"]["content"]["application/json"]["schema"][
        "$ref"
    ]
    request_schema = openapi_schema["components"]["schemas"][
        request_ref.rsplit("/", 1)[-1]
    ]
    assert set(request_schema["properties"]) == {
        "email",
        "password",
        "nickname",
        "profileCharacterCode",
    }
    assert operation["tags"] == ["auth"]
    assert "security" not in operation
# --- 이메일 로그인: POST /api/v1/auth/login/email ---

INVALID_CREDENTIALS_RESPONSE = {
    "code": "INVALID_CREDENTIALS",
    "message": "이메일 또는 비밀번호가 올바르지 않습니다.",
}
LOGIN_PASSWORD = "12345678"


def login_request(
    db: Mock,
    *,
    body: dict[str, str] | None = None,
    raise_server_exceptions: bool = True,
):
    with api_client(db, raise_server_exceptions=raise_server_exceptions) as client:
        return client.post(
            "/api/v1/auth/login/email",
            json=body
            if body is not None
            else {"email": "user@example.com", "password": LOGIN_PASSWORD},
        )


def login_user(*, user_id: int = 1, password: str = LOGIN_PASSWORD) -> User:
    """저장된 Argon2id 해시를 가진 로그인 가능한 사용자를 만듭니다."""
    return User(
        id=user_id,
        email="user@example.com",
        password_hash=hash_password(password),
        login_provider=LoginProvider.EMAIL,
        nickname="블링크",
        status=UserStatus.ACTIVE,
        deleted_at=None,
    )


def test_login_returns_user_id_and_new_access_token() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = login_user(user_id=3)

    response = login_request(db)

    assert response.status_code == 200
    body = response.json()
    assert body["user"] == {"id": 3}
    assert body["auth"]["tokenType"] == "Bearer"
    assert body["auth"]["expiresIn"] == 31536000
    settings = get_settings()
    payload = jwt.decode(
        body["auth"]["accessToken"],
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
    assert payload["sub"] == "3"
    expires_at = datetime.fromtimestamp(payload["exp"], tz=KOREA_TIMEZONE)
    assert body["auth"]["expiresAt"] == expires_at.replace(tzinfo=None).isoformat()


def test_login_does_not_change_stored_data() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = login_user()

    response = login_request(db)

    assert response.status_code == 200
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_login_normalizes_email_before_lookup() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = login_user()

    response = login_request(
        db,
        body={"email": "  User@Example.COM  ", "password": LOGIN_PASSWORD},
    )

    assert response.status_code == 200
    assert (
        "\"user\".email = 'user@example.com'" in compiled_query(db.scalar.call_args)
    )


def test_login_queries_only_active_email_user_with_password() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = login_user()

    login_request(db)

    query = compiled_query(db.scalar.call_args)
    assert "\"user\".login_provider = 'EMAIL'" in query
    assert '"user".password_hash IS NOT NULL' in query
    assert "\"user\".status = 'ACTIVE'" in query
    assert '"user".deleted_at IS NULL' in query


def test_login_returns_401_when_user_is_not_found() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = login_request(db)

    assert response.status_code == 401
    assert response.json() == INVALID_CREDENTIALS_RESPONSE


def test_login_returns_401_when_password_does_not_match() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = login_user()

    response = login_request(
        db,
        body={"email": "user@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json() == INVALID_CREDENTIALS_RESPONSE


def test_login_returns_401_for_empty_password_without_request_error() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = login_user()

    response = login_request(db, body={"email": "user@example.com", "password": ""})

    assert response.status_code == 401
    assert response.json() == INVALID_CREDENTIALS_RESPONSE


def test_login_allows_password_shorter_than_signup_minimum() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = login_user(password="1234")

    response = login_request(
        db,
        body={"email": "user@example.com", "password": "1234"},
    )

    assert response.status_code == 200


def test_login_returns_400_when_required_field_is_missing() -> None:
    db = Mock(spec=Session)

    response = login_request(db, body={"email": "user@example.com"})

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_login_returns_400_for_invalid_email_format() -> None:
    db = Mock(spec=Session)

    response = login_request(
        db,
        body={"email": "user-example.com", "password": LOGIN_PASSWORD},
    )

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_login_returns_400_when_email_exceeds_max_length() -> None:
    db = Mock(spec=Session)

    response = login_request(
        db,
        body={
            "email": f"{'a' * 250}@example.com",
            "password": LOGIN_PASSWORD,
        },
    )

    assert response.status_code == 400
    assert response.json() == INVALID_REQUEST_RESPONSE
    db.scalar.assert_not_called()


def test_login_returns_500_when_stored_hash_is_broken() -> None:
    db = Mock(spec=Session)
    user = login_user()
    user.password_hash = "not-an-argon2id-hash"
    db.scalar.return_value = user

    response = login_request(db, raise_server_exceptions=False)

    assert response.status_code == 500


def test_login_swagger_contract() -> None:
    openapi_schema = app.openapi()
    operation = openapi_schema["paths"]["/api/v1/auth/login/email"]["post"]

    assert set(operation["responses"]) == {"200", "400", "401"}
    request_ref = operation["requestBody"]["content"]["application/json"]["schema"][
        "$ref"
    ]
    request_schema = openapi_schema["components"]["schemas"][
        request_ref.rsplit("/", 1)[-1]
    ]
    assert set(request_schema["properties"]) == {"email", "password"}
    assert operation["tags"] == ["auth"]
    assert "security" not in operation


# --- Access Token 인증 의존성: Authorization: Bearer {accessToken} ---

INVALID_ACCESS_TOKEN_RESPONSE = {
    "code": "INVALID_ACCESS_TOKEN",
    "message": "유효하지 않거나 만료된 액세스 토큰입니다.",
}
# 인증 의존성만 확인하기 위해 db.execute 만 쓰는 조회 API를 사용합니다.
AUTHENTICATED_PATH = "/api/v1/users/me/sellable-cubes"


def issue_token(
    *,
    user_id: int | str = 7,
    expires_in_seconds: int = 3600,
    secret_key: str | None = None,
    include_subject: bool = True,
) -> str:
    """테스트용 Access Token을 만듭니다."""
    settings = get_settings()
    issued_at = datetime.now(timezone.utc)
    payload: dict[str, object] = {
        "iat": issued_at,
        "exp": issued_at + timedelta(seconds=expires_in_seconds),
    }
    if include_subject:
        payload["sub"] = str(user_id)
    return jwt.encode(
        payload,
        secret_key if secret_key is not None else settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def authenticated_request(db: Mock, *, headers: dict[str, str] | None = None):
    with api_client(db, authenticate=False) as client:
        return client.get(AUTHENTICATED_PATH, headers=headers)


def test_authentication_passes_user_id_from_token_to_service() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = 7
    db.execute.return_value.all.return_value = []

    response = authenticated_request(
        db,
        headers={"Authorization": f"Bearer {issue_token(user_id=7)}"},
    )

    assert response.status_code == 200
    assert "cube_ownership.user_id = 7" in compiled_query(db.execute.call_args)


def test_authentication_queries_only_active_user() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = 7
    db.execute.return_value.all.return_value = []

    authenticated_request(
        db,
        headers={"Authorization": f"Bearer {issue_token(user_id=7)}"},
    )

    query = compiled_query(db.scalar.call_args)
    assert '"user".id = 7' in query
    assert "\"user\".status = 'ACTIVE'" in query
    assert '"user".deleted_at IS NULL' in query


def test_authentication_returns_401_without_authorization_header() -> None:
    db = Mock(spec=Session)

    response = authenticated_request(db)

    assert response.status_code == 401
    assert response.json() == INVALID_ACCESS_TOKEN_RESPONSE
    db.scalar.assert_not_called()


def test_authentication_returns_401_for_non_bearer_scheme() -> None:
    db = Mock(spec=Session)

    response = authenticated_request(db, headers={"Authorization": "Basic abcdef"})

    assert response.status_code == 401
    assert response.json() == INVALID_ACCESS_TOKEN_RESPONSE
    db.scalar.assert_not_called()


def test_authentication_returns_401_for_malformed_token() -> None:
    db = Mock(spec=Session)

    response = authenticated_request(db, headers={"Authorization": "Bearer not.a.jwt"})

    assert response.status_code == 401
    assert response.json() == INVALID_ACCESS_TOKEN_RESPONSE
    db.scalar.assert_not_called()


def test_authentication_returns_401_for_token_signed_with_other_secret() -> None:
    db = Mock(spec=Session)
    token = issue_token(secret_key="another-secret-key-for-test")

    response = authenticated_request(db, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json() == INVALID_ACCESS_TOKEN_RESPONSE
    db.scalar.assert_not_called()


def test_authentication_returns_401_for_expired_token() -> None:
    db = Mock(spec=Session)
    token = issue_token(expires_in_seconds=-1)

    response = authenticated_request(db, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json() == INVALID_ACCESS_TOKEN_RESPONSE
    db.scalar.assert_not_called()


def test_authentication_returns_401_when_subject_is_missing() -> None:
    db = Mock(spec=Session)
    token = issue_token(include_subject=False)

    response = authenticated_request(db, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json() == INVALID_ACCESS_TOKEN_RESPONSE
    db.scalar.assert_not_called()


def test_authentication_returns_401_when_subject_is_not_a_number() -> None:
    db = Mock(spec=Session)
    token = issue_token(user_id="abc")

    response = authenticated_request(db, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json() == INVALID_ACCESS_TOKEN_RESPONSE
    db.scalar.assert_not_called()


def test_authentication_returns_401_when_user_is_missing_or_inactive() -> None:
    db = Mock(spec=Session)
    db.scalar.return_value = None

    response = authenticated_request(
        db,
        headers={"Authorization": f"Bearer {issue_token()}"},
    )

    assert response.status_code == 401
    assert response.json() == INVALID_ACCESS_TOKEN_RESPONSE
    db.execute.assert_not_called()


def test_authenticated_endpoint_declares_bearer_security_scheme() -> None:
    openapi_schema = app.openapi()

    assert openapi_schema["components"]["securitySchemes"]["HTTPBearer"] == {
        "type": "http",
        "scheme": "bearer",
    }
    operation = openapi_schema["paths"][AUTHENTICATED_PATH]["get"]
    assert operation["security"] == [{"HTTPBearer": []}]
