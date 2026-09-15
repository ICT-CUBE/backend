from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from chromadb.api.models.Collection import Collection
from openai import OpenAI

from app.core.chroma import get_jenny_knowledge_collection
from app.core.config import Settings, get_settings
from app.rag.chunking import DocumentChunk, load_document_chunks

DEFAULT_EMBEDDING_BATCH_SIZE = 64


@dataclass(frozen=True)
class IndexingResult:
    source: str
    collection_name: str
    embedded_chunks: int
    upserted_chunks: int
    deleted_stale_chunks: int
    collection_count: int


def create_embeddings(
    texts: Sequence[str],
    *,
    client: OpenAI,
    model: str,
    batch_size: int = DEFAULT_EMBEDDING_BATCH_SIZE,
) -> list[list[float]]:
    """Create embeddings in batches while preserving the input order."""
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")
    if not model.strip():
        raise ValueError("model must not be empty")
    if any(not text.strip() for text in texts):
        raise ValueError("embedding input must not contain empty text")

    embeddings: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        batch = list(texts[start : start + batch_size])
        response = client.embeddings.create(model=model, input=batch)
        ordered_data = sorted(response.data, key=lambda item: item.index)
        expected_indexes = list(range(len(batch)))
        actual_indexes = [item.index for item in ordered_data]
        if actual_indexes != expected_indexes:
            raise RuntimeError(
                "OpenAI embedding response indexes do not match the request batch"
            )
        embeddings.extend([list(item.embedding) for item in ordered_data])

    if len(embeddings) != len(texts):
        raise RuntimeError("OpenAI embedding response count does not match input count")
    return embeddings


def index_document(
    path: str | Path,
    *,
    settings: Settings | None = None,
    openai_client: OpenAI | None = None,
    collection: Collection | None = None,
    batch_size: int = DEFAULT_EMBEDDING_BATCH_SIZE,
    document_version: int = 1,
) -> IndexingResult:
    """Embed a document, upsert its chunks, and remove stale source chunks."""
    resolved_settings = settings or get_settings()
    resolved_path = Path(path)
    chunks = load_document_chunks(
        resolved_path,
        embedding_model=resolved_settings.openai_embedding_model,
        document_version=document_version,
    )
    if not chunks:
        raise ValueError(f"No indexable content found in {resolved_path}")

    resolved_openai_client = (
        openai_client
        if openai_client is not None
        else _create_openai_client(resolved_settings)
    )
    resolved_collection = (
        collection if collection is not None else get_jenny_knowledge_collection()
    )
    embeddings = create_embeddings(
        [chunk.document for chunk in chunks],
        client=resolved_openai_client,
        model=resolved_settings.openai_embedding_model,
        batch_size=batch_size,
    )

    resolved_collection.upsert(
        ids=[chunk.id for chunk in chunks],
        embeddings=embeddings,
        documents=[chunk.document for chunk in chunks],
        metadatas=[chunk.metadata for chunk in chunks],
    )

    stale_ids = _find_stale_chunk_ids(resolved_collection, chunks)
    if stale_ids:
        resolved_collection.delete(ids=stale_ids)

    return IndexingResult(
        source=resolved_path.name,
        collection_name=resolved_settings.chroma_collection_name,
        embedded_chunks=len(chunks),
        upserted_chunks=len(chunks),
        deleted_stale_chunks=len(stale_ids),
        collection_count=resolved_collection.count(),
    )


def _create_openai_client(settings: Settings) -> OpenAI:
    if not settings.openai_api_key.strip():
        raise ValueError("OPENAI_API_KEY must be configured before indexing")
    return OpenAI(api_key=settings.openai_api_key)


def _find_stale_chunk_ids(
    collection: Collection,
    current_chunks: Sequence[DocumentChunk],
) -> list[str]:
    source = str(current_chunks[0].metadata["source"])
    existing: dict[str, Any] = collection.get(where={"source": source})
    existing_ids = set(existing.get("ids") or [])
    current_ids = {chunk.id for chunk in current_chunks}
    return sorted(existing_ids - current_ids)
