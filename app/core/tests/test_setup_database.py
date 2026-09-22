from argparse import Namespace
from unittest.mock import MagicMock, Mock, patch

import pytest

from scripts import setup_database


def database_settings(name: str = "hanium") -> setup_database.DatabaseSettings:
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


def demo_trade() -> setup_database.DemoTrade:
    return setup_database.DemoTrade(
        trade_id=1,
        listing_id=1,
        cube_id=2,
        serial_number="NO.0031",
        token_id=31,
        seller_user_id=2,
        seller_nickname="지드래곤짱",
        seller_ownership_id=2,
        buyer_user_id=1,
        buyer_nickname="블링크",
    )


def mock_connection(*, fetch_rows: list[tuple | None]) -> tuple[Mock, Mock]:
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.side_effect = fetch_rows
    return connection, cursor


def test_load_demo_trade_returns_trade_and_seller_ownership() -> None:
    connection, cursor = mock_connection(
        fetch_rows=[
            (1, 1, 2, "NO.0031", 2, "지드래곤짱", 1, "블링크"),
            (2,),
        ]
    )

    with patch.object(
        setup_database,
        "connect_database",
        return_value=connection,
    ):
        target = setup_database.load_demo_trade(
            settings=database_settings(),
            trade_id=1,
        )

    assert target == demo_trade()
    assert cursor.execute.call_count == 2
    connection.close.assert_called_once()


def test_load_demo_trade_rejects_trade_without_seller_ownership() -> None:
    connection, _ = mock_connection(
        fetch_rows=[
            (1, 1, 2, "NO.0031", 2, "지드래곤짱", 1, "블링크"),
            None,
        ]
    )

    with patch.object(
        setup_database,
        "connect_database",
        return_value=connection,
    ):
        with pytest.raises(RuntimeError, match="판매자의 큐브 소유권"):
            setup_database.load_demo_trade(
                settings=database_settings(),
                trade_id=1,
            )


def test_reset_demo_trade_database_updates_only_demo_related_rows() -> None:
    connection, cursor = mock_connection(fetch_rows=[(1,)])

    with patch.object(
        setup_database,
        "connect_database",
        return_value=connection,
    ):
        setup_database.reset_demo_trade_database(
            settings=database_settings(),
            target=demo_trade(),
        )

    queries = [call.args[0] for call in cursor.execute.call_args_list]
    assert queries[0] == "SELECT id FROM trade WHERE id = %s FOR UPDATE"
    assert any("DELETE FROM digital_certificate" in query for query in queries)
    assert any("DELETE FROM blockchain_operation" in query for query in queries)
    insert_call = next(
        call
        for call in cursor.execute.call_args_list
        if "INSERT INTO blockchain_operation" in call.args[0]
    )
    assert "'TRANSFER', 'CONFIRMED'" in insert_call.args[0]
    token_id, trade_id, _, tx_hash = insert_call.args[1]
    assert (token_id, trade_id, tx_hash) == (31, 1, setup_database.DEMO_TX_HASH)
    assert any("UPDATE cube_ownership" in query for query in queries)
    assert any("UPDATE cube SET status = 'TRADE_PENDING'" in query for query in queries)
    assert any("UPDATE sell_listing SET status = 'SOLD'" in query for query in queries)
    assert any("status = 'DELIVERED'" in query for query in queries)
    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()
    connection.close.assert_called_once()


def test_reset_demo_trade_database_rolls_back_on_failure() -> None:
    connection, cursor = mock_connection(fetch_rows=[(1,)])
    cursor.execute.side_effect = [None, RuntimeError("delete failed")]

    with patch.object(
        setup_database,
        "connect_database",
        return_value=connection,
    ):
        with pytest.raises(RuntimeError, match="delete failed"):
            setup_database.reset_demo_trade_database(
                settings=database_settings(),
                target=demo_trade(),
            )

    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()


def test_load_demo_trade_rejects_unsupported_serial_number() -> None:
    connection, _ = mock_connection(
        fetch_rows=[
            (1, 1, 2, "CUBE-31", 2, "지드래곤짱", 1, "블링크"),
            (2,),
        ]
    )

    with patch.object(
        setup_database,
        "connect_database",
        return_value=connection,
    ):
        with pytest.raises(RuntimeError, match="토큰 번호로 변환할 수 없는"):
            setup_database.load_demo_trade(
                settings=database_settings(),
                trade_id=1,
            )


def test_main_resets_demo_trade_after_confirmation() -> None:
    args = Namespace(
        yes=True,
        trade_id=1,
        resource_group="hanium-rg",
        backend_app="hanium",
    )
    target = demo_trade()
    settings = database_settings()
    events: list[str] = []

    with (
        patch.object(setup_database, "parse_args", return_value=args),
        patch.object(
            setup_database,
            "load_webapp_settings",
            return_value={"APP": "backend"},
        ),
        patch.object(
            setup_database,
            "parse_backend_database_settings",
            return_value=settings,
        ),
        patch.object(
            setup_database,
            "load_demo_trade",
            side_effect=lambda **_: events.append("load") or target,
        ),
        patch.object(
            setup_database,
            "confirm_prepare",
            side_effect=lambda **_: events.append("confirm"),
        ),
        patch.object(
            setup_database,
            "reset_demo_trade_database",
            side_effect=lambda **_: events.append("database"),
        ) as reset,
    ):
        setup_database.main()

    assert events == ["load", "confirm", "database"]
    reset.assert_called_once_with(settings=settings, target=target)


def test_main_does_not_reset_database_when_confirmation_cancelled() -> None:
    args = Namespace(
        yes=False,
        trade_id=1,
        resource_group="hanium-rg",
        backend_app="hanium",
    )

    with (
        patch.object(setup_database, "parse_args", return_value=args),
        patch.object(setup_database, "load_webapp_settings", return_value={}),
        patch.object(
            setup_database,
            "parse_backend_database_settings",
            return_value=database_settings(),
        ),
        patch.object(
            setup_database,
            "load_demo_trade",
            return_value=demo_trade(),
        ),
        patch("builtins.input", return_value="2"),
        patch.object(setup_database, "reset_demo_trade_database") as reset,
    ):
        with pytest.raises(SystemExit):
            setup_database.main()

    reset.assert_not_called()
