import hashlib
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MAX_CHUNK_CHARS = 1200
DEFAULT_DOCUMENT_VERSION = 1
_SECTION_HEADER_PATTERN = re.compile(r"^\[([^\[\]\r\n]+)\]\s*$")
_PARAGRAPH_BREAK_PATTERN = re.compile(r"\n\s*\n+")
_SENTENCE_BREAK_PATTERN = re.compile(r"(?<=[.!?。！？])\s+")


@dataclass(frozen=True)
class DocumentSection:
    title: str
    content: str


@dataclass(frozen=True)
class DocumentChunk:
    id: str
    document: str
    metadata: dict[str, str | int]


def parse_sections(text: str) -> list[DocumentSection]:
    """Parse bracket headings and their non-empty bodies from a text document."""
    normalized_text = text.replace("\r\n", "\n").replace("\r", "\n")
    sections: list[DocumentSection] = []
    current_title: str | None = None
    current_lines: list[str] = []

    def append_current_section() -> None:
        if current_title is None:
            return
        content = "\n".join(current_lines).strip()
        if content:
            sections.append(DocumentSection(title=current_title, content=content))

    for line in normalized_text.split("\n"):
        header_match = _SECTION_HEADER_PATTERN.fullmatch(line.strip())
        if header_match:
            append_current_section()
            current_title = header_match.group(1).strip()
            current_lines = []
            continue

        if current_title is None and line.strip():
            current_title = "문서"
        if current_title is not None:
            current_lines.append(line.rstrip())

    append_current_section()
    return sections


def chunk_document(
    text: str,
    *,
    source: str,
    embedding_model: str,
    max_chunk_chars: int = DEFAULT_MAX_CHUNK_CHARS,
    document_version: int = DEFAULT_DOCUMENT_VERSION,
) -> list[DocumentChunk]:
    """Split a source document into deterministic, Chroma-ready chunks."""
    if max_chunk_chars <= 0:
        raise ValueError("max_chunk_chars must be greater than zero")
    if document_version <= 0:
        raise ValueError("document_version must be greater than zero")
    if not source.strip():
        raise ValueError("source must not be empty")
    if not embedding_model.strip():
        raise ValueError("embedding_model must not be empty")

    chunks: list[DocumentChunk] = []
    source_name = Path(source).name
    source_slug = _slugify(Path(source_name).stem)

    for section in parse_sections(text):
        header = f"[{section.title}]"
        body_max_chars = max_chunk_chars - len(header) - 1
        if body_max_chars <= 0:
            raise ValueError(
                "max_chunk_chars is too small to include the section heading"
            )

        section_slug = _slugify(section.title)
        bodies = _split_section_body(section.content, body_max_chars)
        for chunk_index, body in enumerate(bodies):
            document = f"{header}\n{body}"
            content_hash = hashlib.sha256(document.encode("utf-8")).hexdigest()
            chunk_id = (
                f"{source_slug}:{section_slug}:{chunk_index}:{content_hash[:16]}"
            )
            chunks.append(
                DocumentChunk(
                    id=chunk_id,
                    document=document,
                    metadata={
                        "source": source_name,
                        "section": section.title,
                        "chunk_index": chunk_index,
                        "content_hash": content_hash,
                        "document_version": document_version,
                        "embedding_model": embedding_model,
                    },
                )
            )

    return chunks


def load_document_chunks(
    path: str | Path,
    *,
    embedding_model: str,
    max_chunk_chars: int = DEFAULT_MAX_CHUNK_CHARS,
    document_version: int = DEFAULT_DOCUMENT_VERSION,
) -> list[DocumentChunk]:
    """Read a UTF-8 document and return deterministic chunks."""
    document_path = Path(path)
    return chunk_document(
        document_path.read_text(encoding="utf-8"),
        source=document_path.name,
        embedding_model=embedding_model,
        max_chunk_chars=max_chunk_chars,
        document_version=document_version,
    )


def _split_section_body(content: str, max_chars: int) -> list[str]:
    paragraphs = [
        paragraph.strip()
        for paragraph in _PARAGRAPH_BREAK_PATTERN.split(content)
        if paragraph.strip()
    ]
    units: list[str] = []
    for paragraph in paragraphs:
        units.extend(_split_oversized_paragraph(paragraph, max_chars))

    chunks: list[str] = []
    current = ""
    for unit in units:
        candidate = unit if not current else f"{current}\n\n{unit}"
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = unit

    if current:
        chunks.append(current)
    return chunks


def _split_oversized_paragraph(paragraph: str, max_chars: int) -> list[str]:
    if len(paragraph) <= max_chars:
        return [paragraph]

    lines = [line.strip() for line in paragraph.split("\n") if line.strip()]
    if len(lines) > 1:
        parts: list[str] = []
        for line in lines:
            parts.extend(_split_oversized_paragraph(line, max_chars))
        return parts

    sentences = [
        sentence.strip()
        for sentence in _SENTENCE_BREAK_PATTERN.split(paragraph)
        if sentence.strip()
    ]
    if len(sentences) > 1:
        return _pack_parts(sentences, max_chars)

    return _split_at_word_boundary(paragraph, max_chars)


def _pack_parts(parts: list[str], max_chars: int) -> list[str]:
    packed: list[str] = []
    current = ""
    for part in parts:
        if len(part) > max_chars:
            split_parts = _split_at_word_boundary(part, max_chars)
        else:
            split_parts = [part]

        for split_part in split_parts:
            candidate = split_part if not current else f"{current} {split_part}"
            if len(candidate) <= max_chars:
                current = candidate
                continue
            if current:
                packed.append(current)
            current = split_part

    if current:
        packed.append(current)
    return packed


def _split_at_word_boundary(text: str, max_chars: int) -> list[str]:
    remaining = text.strip()
    parts: list[str] = []
    while len(remaining) > max_chars:
        split_at = remaining.rfind(" ", 0, max_chars + 1)
        if split_at <= 0:
            split_at = max_chars
        parts.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining:
        parts.append(remaining)
    return parts


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    slug = re.sub(r"[^\w]+", "_", normalized, flags=re.UNICODE).strip("_")
    return slug or "section"
