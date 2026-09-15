from unittest.mock import Mock, patch

import pytest

from app.core.chroma import (
    create_chroma_client,
    get_chroma_client,
    get_jenny_knowledge_collection,
    ping_chroma,
)
from app.core.config import Settings, get_settings


@pytest.fixture(autouse=True)
def clear_chroma_caches() -> None:
    get_chroma_client.cache_clear()
    get_jenny_knowledge_collection.cache_clear()
    get_settings.cache_clear()
    yield
    get_chroma_client.cache_clear()
    get_jenny_knowledge_collection.cache_clear()
    get_settings.cache_clear()


def test_create_chroma_client_uses_settings() -> None:
    settings = Settings(
        _env_file=None,
        chroma_host="chroma.internal",
        chroma_port=8443,
        chroma_ssl_enabled=True,
    )

    with patch("app.core.chroma.chromadb.HttpClient") as http_client:
        result = create_chroma_client(settings)

    assert result is http_client.return_value
    http_client.assert_called_once_with(
        host="chroma.internal",
        port=8443,
        ssl=True,
    )


def test_get_chroma_client_reuses_cached_client() -> None:
    with patch("app.core.chroma.create_chroma_client") as create_client:
        first = get_chroma_client()
        second = get_chroma_client()

    assert first is second
    create_client.assert_called_once_with()


def test_get_jenny_collection_disables_default_embedding_function() -> None:
    client = Mock()
    settings = Settings(
        _env_file=None,
        chroma_collection_name="test_jenny_knowledge",
    )

    with (
        patch("app.core.chroma.get_chroma_client", return_value=client),
        patch("app.core.chroma.get_settings", return_value=settings),
    ):
        collection = get_jenny_knowledge_collection()

    assert collection is client.get_or_create_collection.return_value
    client.get_or_create_collection.assert_called_once_with(
        name="test_jenny_knowledge",
        embedding_function=None,
    )


def test_ping_chroma_calls_heartbeat() -> None:
    client = Mock()

    with patch("app.core.chroma.get_chroma_client", return_value=client):
        assert ping_chroma() is True

    client.heartbeat.assert_called_once_with()


def test_ping_chroma_propagates_connection_error() -> None:
    client = Mock()
    client.heartbeat.side_effect = ConnectionError("chroma unavailable")

    with (
        patch("app.core.chroma.get_chroma_client", return_value=client),
        pytest.raises(ConnectionError, match="chroma unavailable"),
    ):
        ping_chroma()
