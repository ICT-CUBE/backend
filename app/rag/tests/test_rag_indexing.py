from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

from app.core.config import Settings
from app.rag.indexing import create_embeddings, index_document

EMBEDDING_MODEL = "text-embedding-3-small"


def embedding_response(*vectors: list[float]) -> SimpleNamespace:
    return SimpleNamespace(
        data=[
            SimpleNamespace(index=index, embedding=vector)
            for index, vector in enumerate(vectors)
        ]
    )


def test_create_embeddings_batches_requests_and_preserves_order() -> None:
    client = Mock()
    client.embeddings.create.side_effect = [
        embedding_response([1.0, 0.0], [0.0, 1.0]),
        embedding_response([0.5, 0.5]),
    ]

    result = create_embeddings(
        ["first", "second", "third"],
        client=client,
        model=EMBEDDING_MODEL,
        batch_size=2,
    )

    assert result == [[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]]
    assert client.embeddings.create.call_args_list == [
        call(model=EMBEDDING_MODEL, input=["first", "second"]),
        call(model=EMBEDDING_MODEL, input=["third"]),
    ]


def test_create_embeddings_rejects_mismatched_response_indexes() -> None:
    client = Mock()
    client.embeddings.create.return_value = SimpleNamespace(
        data=[SimpleNamespace(index=1, embedding=[1.0, 0.0])]
    )

    with pytest.raises(RuntimeError, match="indexes do not match"):
        create_embeddings(
            ["first"],
            client=client,
            model=EMBEDDING_MODEL,
        )


def test_index_document_upserts_chunks_and_removes_stale_ids(
    tmp_path: Path,
) -> None:
    source = tmp_path / "jennie_text.md"
    source.write_text(
        "[기본 정보]\n제니의 생일은 1996년 1월 16일입니다.\n\n"
        "[취향]\n제니는 겨울을 좋아합니다.",
        encoding="utf-8",
    )
    settings = Settings(
        _env_file=None,
        openai_embedding_model=EMBEDDING_MODEL,
        chroma_collection_name="test_jenny_knowledge",
    )
    openai_client = Mock()
    openai_client.embeddings.create.return_value = embedding_response(
        [1.0, 0.0],
        [0.0, 1.0],
    )
    collection = Mock()
    collection.get.return_value = {"ids": ["stale-chunk-id"]}
    collection.count.return_value = 2

    result = index_document(
        source,
        settings=settings,
        openai_client=openai_client,
        collection=collection,
    )

    upsert = collection.upsert.call_args.kwargs
    assert len(upsert["ids"]) == 2
    assert upsert["embeddings"] == [[1.0, 0.0], [0.0, 1.0]]
    assert upsert["documents"][0].startswith("[기본 정보]")
    assert upsert["metadatas"][0]["embedding_model"] == EMBEDDING_MODEL
    collection.get.assert_called_once_with(where={"source": "jennie_text.md"})
    collection.delete.assert_called_once_with(ids=["stale-chunk-id"])
    assert result.collection_name == "test_jenny_knowledge"
    assert result.embedded_chunks == 2
    assert result.upserted_chunks == 2
    assert result.deleted_stale_chunks == 1
    assert result.collection_count == 2


def test_index_document_does_not_delete_when_there_are_no_stale_ids(
    tmp_path: Path,
) -> None:
    source = tmp_path / "jennie_text.md"
    source.write_text("[정보]\n제니 정보", encoding="utf-8")
    settings = Settings(
        _env_file=None,
        openai_embedding_model=EMBEDDING_MODEL,
    )
    openai_client = Mock()
    openai_client.embeddings.create.return_value = embedding_response([1.0])
    collection = Mock()
    collection.get.return_value = {"ids": []}
    collection.count.return_value = 1

    index_document(
        source,
        settings=settings,
        openai_client=openai_client,
        collection=collection,
    )

    collection.delete.assert_not_called()


def test_index_document_rejects_empty_source_without_external_calls(
    tmp_path: Path,
) -> None:
    source = tmp_path / "empty.md"
    source.write_text("  \n", encoding="utf-8")
    openai_client = Mock()
    collection = Mock()

    with pytest.raises(ValueError, match="No indexable content"):
        index_document(
            source,
            settings=Settings(_env_file=None),
            openai_client=openai_client,
            collection=collection,
        )

    openai_client.embeddings.create.assert_not_called()
    collection.upsert.assert_not_called()


def test_index_document_requires_api_key_when_client_is_not_injected(
    tmp_path: Path,
) -> None:
    source = tmp_path / "jennie_text.md"
    source.write_text("[정보]\n제니 정보", encoding="utf-8")

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        index_document(
            source,
            settings=Settings(_env_file=None, openai_api_key=""),
            collection=Mock(),
        )
