from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from scripts import setup_database


def database_settings(name: str) -> setup_database.DatabaseSettings:
    return setup_database.DatabaseSettings.model_validate(
        {
            "MYSQL_HOST": "mysql.example.com",
            "MYSQL_PORT": 3306,
            "MYSQL_DATABASE": name,
            "MYSQL_USER": "user",
            "MYSQL_PASSWORD": "password",
            "MYSQL_SSL_ENABLED": True,
        }
    )


def test_parse_blockchain_database_settings_decodes_url_values() -> None:
    settings = setup_database.parse_blockchain_database_settings(
        {
            "DATABASE_URL": "mysql://user:p%40ss@mysql.example.com:3307/cube_nft",
            "DATABASE_SSL_ENABLED": "true",
        }
    )

    assert settings.mysql_host == "mysql.example.com"
    assert settings.mysql_port == 3307
    assert settings.mysql_database == "cube_nft"
    assert settings.mysql_password.get_secret_value() == "p@ss"
    assert settings.mysql_ssl_enabled is True


def test_main_runs_demo_reset_in_required_order() -> None:
    args = Namespace(
        yes=True,
        resource_group="hanium-rg",
        backend_app="hanium",
        blockchain_app="hanium-blockchain",
    )
    backend_database = database_settings("hanium")
    blockchain_database = database_settings("cube_nft")
    events: list[str] = []

    with (
        patch.object(setup_database, "parse_args", return_value=args),
        patch.object(setup_database, "validate_sql_files"),
        patch.object(
            setup_database,
            "load_webapp_settings",
            side_effect=[{"APP": "backend"}, {"APP": "blockchain"}],
        ),
        patch.object(
            setup_database,
            "parse_backend_database_settings",
            return_value=backend_database,
        ),
        patch.object(
            setup_database,
            "parse_blockchain_database_settings",
            return_value=blockchain_database,
        ),
        patch.object(setup_database, "confirm_reset"),
        patch.object(
            setup_database,
            "set_webapp_state",
            side_effect=lambda **kwargs: events.append(
                f"{kwargs['action']}:{kwargs['app_name']}"
            ),
        ),
        patch.object(
            setup_database,
            "reset_backend_database",
            side_effect=lambda _: events.append("reset:backend"),
        ),
        patch.object(
            setup_database,
            "reset_blockchain_database",
            side_effect=lambda _: events.append("reset:blockchain"),
        ),
        patch.object(
            setup_database,
            "wait_for_endpoint",
            side_effect=lambda **kwargs: events.append(f"ready:{kwargs['label']}"),
        ),
        patch.object(
            setup_database,
            "inject_process_environment",
            side_effect=lambda _: events.append("inject:backend-settings"),
        ),
        patch.object(
            setup_database,
            "run_backfill",
            side_effect=lambda: events.append("backfill"),
        ),
    ):
        setup_database.main()

    assert events == [
        "stop:hanium-blockchain",
        "stop:hanium",
        "reset:backend",
        "reset:blockchain",
        "start:hanium",
        "ready:Backend",
        "start:hanium-blockchain",
        "ready:Blockchain Server",
        "inject:backend-settings",
        "backfill",
    ]


def test_main_restarts_apps_when_database_reset_fails() -> None:
    args = Namespace(
        yes=True,
        resource_group="hanium-rg",
        backend_app="hanium",
        blockchain_app="hanium-blockchain",
    )
    backend_database = database_settings("hanium")
    blockchain_database = database_settings("cube_nft")
    states = Mock()

    with (
        patch.object(setup_database, "parse_args", return_value=args),
        patch.object(setup_database, "validate_sql_files"),
        patch.object(
            setup_database,
            "load_webapp_settings",
            side_effect=[{"APP": "backend"}, {"APP": "blockchain"}],
        ),
        patch.object(
            setup_database,
            "parse_backend_database_settings",
            return_value=backend_database,
        ),
        patch.object(
            setup_database,
            "parse_blockchain_database_settings",
            return_value=blockchain_database,
        ),
        patch.object(setup_database, "confirm_reset"),
        patch.object(setup_database, "set_webapp_state", states),
        patch.object(
            setup_database,
            "reset_backend_database",
            side_effect=RuntimeError("reset failed"),
        ),
    ):
        with pytest.raises(RuntimeError, match="reset failed"):
            setup_database.main()

    actions = [call.kwargs["action"] for call in states.call_args_list]
    apps = [call.kwargs["app_name"] for call in states.call_args_list]
    assert actions == ["stop", "stop", "start", "start"]
    assert apps == [
        "hanium-blockchain",
        "hanium",
        "hanium",
        "hanium-blockchain",
    ]
