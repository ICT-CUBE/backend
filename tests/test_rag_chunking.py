from pathlib import Path

import pytest

from app.services.rag.chunking import (
    DEFAULT_MAX_CHUNK_CHARS,
    chunk_document,
    load_document_chunks,
    parse_sections,
)


EMBEDDING_MODEL = "text-embedding-3-small"


def test_parse_sections_uses_bracket_headings_and_ignores_empty_sections() -> None:
    text = """소개 문장

[기본 정보]
제니의 기본 정보입니다.

[빈 섹션]

[취향 및 일상]
제니는 겨울을 좋아합니다.
"""

    sections = parse_sections(text)

    assert [(section.title, section.content) for section in sections] == [
        ("문서", "소개 문장"),
        ("기본 정보", "제니의 기본 정보입니다."),
        ("취향 및 일상", "제니는 겨울을 좋아합니다."),
    ]


def test_chunk_document_keeps_short_section_and_heading_together() -> None:
    chunks = chunk_document(
        "[기본 정보]\n제니의 생일은 1996년 1월 16일입니다.",
        source="jennie_text.md",
        embedding_model=EMBEDDING_MODEL,
    )

    assert len(chunks) == 1
    assert chunks[0].document == (
        "[기본 정보]\n제니의 생일은 1996년 1월 16일입니다."
    )
    assert chunks[0].id.startswith("jennie_text:기본_정보:0:")
    assert chunks[0].metadata["section"] == "기본 정보"
    assert chunks[0].metadata["chunk_index"] == 0
    assert chunks[0].metadata["embedding_model"] == EMBEDDING_MODEL


def test_chunk_document_splits_long_section_within_limit() -> None:
    text = "[활동]\n" + "\n".join(
        f"제니의 활동 정보 {index}입니다." for index in range(20)
    )

    chunks = chunk_document(
        text,
        source="jennie_text.md",
        embedding_model=EMBEDDING_MODEL,
        max_chunk_chars=90,
    )

    assert len(chunks) > 1
    assert all(len(chunk.document) <= 90 for chunk in chunks)
    assert all(chunk.document.startswith("[활동]\n") for chunk in chunks)
    assert [chunk.metadata["chunk_index"] for chunk in chunks] == list(
        range(len(chunks))
    )


def test_chunk_document_is_deterministic() -> None:
    kwargs = {
        "source": "jennie_text.md",
        "embedding_model": EMBEDDING_MODEL,
        "max_chunk_chars": 80,
    }
    text = "[성격 및 평소 모습]\n차분합니다.\n무대에서는 자신감이 있습니다."

    first = chunk_document(text, **kwargs)
    second = chunk_document(text, **kwargs)

    assert first == second


def test_chunk_document_returns_no_chunks_for_empty_text() -> None:
    assert (
        chunk_document(
            " \n\n ",
            source="jennie_text.md",
            embedding_model=EMBEDDING_MODEL,
        )
        == []
    )


@pytest.mark.parametrize(
    ("argument", "value", "message"),
    [
        ("max_chunk_chars", 0, "max_chunk_chars"),
        ("document_version", 0, "document_version"),
        ("source", "", "source"),
        ("embedding_model", "", "embedding_model"),
    ],
)
def test_chunk_document_rejects_invalid_options(
    argument: str,
    value: str | int,
    message: str,
) -> None:
    kwargs: dict[str, str | int] = {
        "source": "jennie_text.md",
        "embedding_model": EMBEDDING_MODEL,
    }
    kwargs[argument] = value

    with pytest.raises(ValueError, match=message):
        chunk_document("[정보]\n본문", **kwargs)  # type: ignore[arg-type]


def test_load_document_chunks_reads_utf8_file(tmp_path: Path) -> None:
    source = tmp_path / "jennie_text.md"
    source.write_text("[취향]\n제니는 겨울을 좋아합니다.", encoding="utf-8")

    chunks = load_document_chunks(source, embedding_model=EMBEDDING_MODEL)

    assert chunks[0].metadata["source"] == "jennie_text.md"
    assert chunks[0].document == "[취향]\n제니는 겨울을 좋아합니다."


def test_real_jennie_document_meets_chunk_contract() -> None:
    source = Path(__file__).parents[1] / "scripts" / "rag" / "jennie_text.md"

    chunks = load_document_chunks(source, embedding_model=EMBEDDING_MODEL)

    assert len(chunks) > 1
    assert len({chunk.id for chunk in chunks}) == len(chunks)
    assert all(chunk.document.startswith("[") for chunk in chunks)
    assert all(len(chunk.document) <= DEFAULT_MAX_CHUNK_CHARS for chunk in chunks)
    assert all(chunk.metadata["content_hash"] for chunk in chunks)
