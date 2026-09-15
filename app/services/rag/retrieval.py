from dataclasses import dataclass
from typing import Any

from chromadb.api.models.Collection import Collection
from openai import OpenAI

from app.core.chroma import get_jenny_knowledge_collection
from app.core.config import Settings, get_settings
from app.services.rag.indexing import create_embeddings


DEFAULT_TOP_K = 4


@dataclass(frozen=True)
class KnowledgeSearchResult:
    chunk_id: str
    document: str
    metadata: dict[str, Any]
    distance: float


def search_jenny_knowledge(
    question: str,
    *,
    top_k: int = DEFAULT_TOP_K,
    settings: Settings | None = None,
    openai_client: OpenAI | None = None,
    collection: Collection | None = None,
) -> list[KnowledgeSearchResult]:
    """Embed a question and return the nearest Jenny knowledge chunks."""
    normalized_question = question.strip()
    if not normalized_question:
        raise ValueError("question must not be empty")
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")

    resolved_settings = settings or get_settings()
    resolved_openai_client = (
        openai_client
        if openai_client is not None
        else _create_openai_client(resolved_settings)
    )
    question_embedding = create_embeddings(
        [normalized_question],
        client=resolved_openai_client,
        model=resolved_settings.openai_embedding_model,
    )[0]
    resolved_collection = (
        collection if collection is not None else get_jenny_knowledge_collection()
    )

    query_result = resolved_collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    return _parse_query_result(query_result)


def _create_openai_client(settings: Settings) -> OpenAI:
    if not settings.openai_api_key.strip():
        raise ValueError("OPENAI_API_KEY must be configured before searching")
    return OpenAI(api_key=settings.openai_api_key)


def _parse_query_result(result: dict[str, Any]) -> list[KnowledgeSearchResult]:
    ids = _first_query_items(result, "ids")
    documents = _first_query_items(result, "documents")
    metadatas = _first_query_items(result, "metadatas")
    distances = _first_query_items(result, "distances")

    result_lengths = {len(ids), len(documents), len(metadatas), len(distances)}
    if len(result_lengths) != 1:
        raise RuntimeError("Chroma query result fields have mismatched lengths")

    search_results: list[KnowledgeSearchResult] = []
    for chunk_id, document, metadata, distance in zip(
        ids,
        documents,
        metadatas,
        distances,
        strict=True,
    ):
        if not isinstance(chunk_id, str) or not isinstance(document, str):
            raise RuntimeError("Chroma query result contains an invalid chunk")
        if metadata is not None and not isinstance(metadata, dict):
            raise RuntimeError("Chroma query result contains invalid metadata")
        if not isinstance(distance, (int, float)):
            raise RuntimeError("Chroma query result contains an invalid distance")

        search_results.append(
            KnowledgeSearchResult(
                chunk_id=chunk_id,
                document=document,
                metadata=dict(metadata or {}),
                distance=float(distance),
            )
        )
    return search_results


def _first_query_items(result: dict[str, Any], field: str) -> list[Any]:
    queries = result.get(field)
    if queries is None:
        raise RuntimeError(f"Chroma query result is missing {field}")
    if not isinstance(queries, list):
        raise RuntimeError(f"Chroma query result has invalid {field}")
    if not queries:
        return []

    items = queries[0]
    if not isinstance(items, list):
        raise RuntimeError(f"Chroma query result has invalid {field}")
    return items
