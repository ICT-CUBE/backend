from functools import lru_cache

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection

from app.core.config import Settings, get_settings


def create_chroma_client(settings: Settings | None = None) -> ClientAPI:
    """Create a Chroma HTTP client from application settings."""
    resolved_settings = settings or get_settings()
    return chromadb.HttpClient(
        host=resolved_settings.chroma_host,
        port=resolved_settings.chroma_port,
        ssl=resolved_settings.chroma_ssl_enabled,
    )


@lru_cache
def get_chroma_client() -> ClientAPI:
    """Return the process-wide Chroma HTTP client."""
    return create_chroma_client()


@lru_cache
def get_jenny_knowledge_collection() -> Collection:
    """Return the collection that stores explicitly generated OpenAI embeddings."""
    settings = get_settings()
    return get_chroma_client().get_or_create_collection(
        name=settings.chroma_collection_name,
        embedding_function=None,
    )


def ping_chroma() -> bool:
    """Raise on connection failure and return True when Chroma is reachable."""
    get_chroma_client().heartbeat()
    return True
