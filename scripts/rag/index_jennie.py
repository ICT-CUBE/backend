"""Embed the Jennie knowledge document and synchronize it to ChromaDB.

Run from the project root inside the API container:
    python scripts/rag/index_jennie.py
"""

import argparse
import sys
from pathlib import Path
from textwrap import dedent

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.rag.indexing import DEFAULT_EMBEDDING_BATCH_SIZE, index_document

DEFAULT_SOURCE = Path(__file__).with_name("jennie_text.md")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Embed the Jennie knowledge document and upsert it to ChromaDB."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"UTF-8 source document (default: {DEFAULT_SOURCE})",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_EMBEDDING_BATCH_SIZE,
        help="Number of chunks per OpenAI embedding request.",
    )
    parser.add_argument(
        "--document-version",
        type=int,
        default=1,
        help="Positive document version stored in Chroma metadata.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = index_document(
        args.source,
        batch_size=args.batch_size,
        document_version=args.document_version,
    )
    print(
        dedent(
            f"""
            Jennie RAG indexing completed
            source: {result.source}
            collection: {result.collection_name}
            embedded/upserted chunks: {result.upserted_chunks}
            deleted stale chunks: {result.deleted_stale_chunks}
            total collection records: {result.collection_count}
            """
        ).strip()
    )


if __name__ == "__main__":
    main()
