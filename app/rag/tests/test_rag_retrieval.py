from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.core.config import Settings
from app.rag.retrieval import search_jenny_knowledge

EMBEDDING_MODEL = "text-embedding-3-small"


def embedding_response(vector: list[float]) -> SimpleNamespace:
    return SimpleNamespace(
        data=[SimpleNamespace(index=0, embedding=vector)],
    )


def test_search_jenny_knowledge_embeds_question_and_queries_chroma() -> None:
    settings = Settings(
        _env_file=None,
        openai_embedding_model=EMBEDDING_MODEL,
    )
    openai_client = Mock()
    openai_client.embeddings.create.return_value = embedding_response([0.1, 0.2])
    collection = Mock()
    collection.query.return_value = {
        "ids": [["chunk-1", "chunk-2"]],
        "documents": [["[취향]\n겨울을 좋아합니다.", "[음악]\n솔로곡입니다."]],
        "metadatas": [[{"section": "취향"}, {"section": "음악"}]],
        "distances": [[0.12, 0.35]],
    }

    results = search_jenny_knowledge(
        "  제니가 좋아하는 계절은?  ",
        top_k=2,
        settings=settings,
        openai_client=openai_client,
        collection=collection,
    )

    openai_client.embeddings.create.assert_called_once_with(
        model=EMBEDDING_MODEL,
        input=["제니가 좋아하는 계절은?"],
    )
    collection.query.assert_called_once_with(
        query_embeddings=[[0.1, 0.2]],
        n_results=2,
        include=["documents", "metadatas", "distances"],
    )
    assert [result.chunk_id for result in results] == ["chunk-1", "chunk-2"]
    assert results[0].document == "[취향]\n겨울을 좋아합니다."
    assert results[0].metadata == {"section": "취향"}
    assert results[0].distance == 0.12


def test_search_jenny_knowledge_uses_default_top_k() -> None:
    openai_client = Mock()
    openai_client.embeddings.create.return_value = embedding_response([0.1])
    collection = Mock()
    collection.query.return_value = {
        "ids": [[]],
        "documents": [[]],
        "metadatas": [[]],
        "distances": [[]],
    }

    results = search_jenny_knowledge(
        "검색 결과가 없는 질문",
        settings=Settings(_env_file=None),
        openai_client=openai_client,
        collection=collection,
    )

    assert results == []
    assert collection.query.call_args.kwargs["n_results"] == 4


@pytest.mark.parametrize("question", ["", "  ", "\n"])
def test_search_jenny_knowledge_rejects_empty_question(question: str) -> None:
    openai_client = Mock()
    collection = Mock()

    with pytest.raises(ValueError, match="question must not be empty"):
        search_jenny_knowledge(
            question,
            settings=Settings(_env_file=None),
            openai_client=openai_client,
            collection=collection,
        )

    openai_client.embeddings.create.assert_not_called()
    collection.query.assert_not_called()


def test_search_jenny_knowledge_rejects_non_positive_top_k() -> None:
    with pytest.raises(ValueError, match="top_k must be greater than zero"):
        search_jenny_knowledge(
            "질문",
            top_k=0,
            settings=Settings(_env_file=None),
            openai_client=Mock(),
            collection=Mock(),
        )


def test_search_jenny_knowledge_requires_api_key_without_injected_client() -> None:
    collection = Mock()

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        search_jenny_knowledge(
            "제니의 생일은?",
            settings=Settings(_env_file=None, openai_api_key=""),
            collection=collection,
        )

    collection.query.assert_not_called()


def test_search_jenny_knowledge_rejects_mismatched_chroma_result() -> None:
    openai_client = Mock()
    openai_client.embeddings.create.return_value = embedding_response([0.1])
    collection = Mock()
    collection.query.return_value = {
        "ids": [["chunk-1"]],
        "documents": [[]],
        "metadatas": [[{"section": "기본 정보"}]],
        "distances": [[0.1]],
    }

    with pytest.raises(RuntimeError, match="mismatched lengths"):
        search_jenny_knowledge(
            "제니의 생일은?",
            settings=Settings(_env_file=None),
            openai_client=openai_client,
            collection=collection,
        )
