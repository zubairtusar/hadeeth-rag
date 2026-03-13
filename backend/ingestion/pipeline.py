"""
Ingestion pipeline: source file → chunks → embeddings → ChromaDB.
Supports both PDF sources and structured JSON sources (Quran/Hadith).
Tracks progress in-memory; safe to call from a background thread.
"""

import threading
from dataclasses import dataclass
from typing import Literal

from backend.config import get_settings
from backend.ingestion.chunker import Chunk, chunk_pages
from backend.ingestion.json_parser import TextEntry, parse_json_source
from backend.ingestion.pdf_parser import parse_pdf
from backend.models.schemas import SourceRecord
from backend.models.source_registry import update_source
from backend.rag.embedder import embed_passages, normalize_for_embedding
from backend.rag.vectorstore import upsert_chunks

StatusType = Literal["pending", "running", "done", "error"]

EMBED_BATCH = 64          # chunks per embedding batch
JSON_AYAHS_PER_CHUNK = 5  # group N ayahs/hadiths per chunk for Quran
JSON_HADITH_PER_CHUNK = 3 # group N hadiths per chunk for Hadith


@dataclass
class IngestionStatus:
    status: StatusType = "pending"
    progress: float = 0.0
    message: str = ""
    chunk_count: int = 0


# Thread-safe global status registry
_lock = threading.Lock()
_statuses: dict[str, IngestionStatus] = {}


def get_status(source_id: str) -> IngestionStatus:
    with _lock:
        return _statuses.get(source_id, IngestionStatus())


def _set_status(source_id: str, **kwargs) -> None:
    with _lock:
        if source_id not in _statuses:
            _statuses[source_id] = IngestionStatus()
        for k, v in kwargs.items():
            setattr(_statuses[source_id], k, v)


# ---------------------------------------------------------------------------
# JSON chunking helper
# ---------------------------------------------------------------------------

def _chunk_json_entries(
    entries: list[TextEntry],
    source_id: str,
    source_type: str,
    file_path: str,
    group_size: int,
) -> list[Chunk]:
    """
    Group JSON TextEntry objects into Chunk objects.
    For Quran: group_size ayahs per chunk.
    For Hadith: group_size hadiths per chunk.
    Citations will use ref_id of the first entry in the group.
    """
    chunks: list[Chunk] = []
    for i in range(0, len(entries), group_size):
        group = entries[i : i + group_size]
        display_parts = []
        for e in group:
            display_parts.append(f"[{e.ref_id}] {e.text}")
        display_text = "\n\n".join(display_parts)
        normalized = normalize_for_embedding(display_text)

        first = group[0]
        chunks.append(
            Chunk(
                source_id=source_id,
                source_type=source_type,
                pdf_path="",           # no PDF for JSON sources
                page_number=first.ref_number,   # global ref number for citation lookup
                chunk_index=i // group_size,
                text=normalized,
                display_text=display_text,
                arabic_ratio=0.0,
                ref_id=first.ref_id,   # e.g. "2:255" or "Book 1, Hadith 3"
            )
        )
    return chunks


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_ingestion(source: SourceRecord) -> None:
    """
    Full ingestion pipeline for one source.
    Dispatches to PDF or JSON pathway based on source.source_format.
    Designed to run in a background thread.
    """
    source_id = source.id
    _set_status(source_id, status="running", progress=0.0, message="Starting ingestion...")

    try:
        settings = get_settings()

        if source.source_format == "json":
            chunks, total_items = _ingest_json(source, settings)
        else:
            chunks, total_items = _ingest_pdf(source, settings)

        total_chunks = len(chunks)

        if total_chunks == 0:
            _set_status(
                source_id,
                status="error",
                message="No text could be extracted from the source file.",
            )
            update_source(source_id, ingested=False)
            return

        _set_status(
            source_id,
            progress=0.2,
            message=f"Created {total_chunks} chunks. Embedding...",
        )

        # Embed in batches and upsert
        processed = 0
        for i in range(0, total_chunks, EMBED_BATCH):
            batch = chunks[i : i + EMBED_BATCH]
            embeddings = embed_passages([c.text for c in batch])
            upsert_chunks(batch, embeddings)
            processed += len(batch)
            _set_status(
                source_id,
                progress=0.2 + 0.75 * (processed / total_chunks),
                message=f"Embedded {processed}/{total_chunks} chunks...",
            )

        update_source(
            source_id,
            ingested=True,
            page_count=total_items,
            chunk_count=total_chunks,
        )
        _set_status(
            source_id,
            status="done",
            progress=1.0,
            message=f"Done! {total_chunks} chunks from {total_items} entries.",
            chunk_count=total_chunks,
        )

    except Exception as exc:
        _set_status(source_id, status="error", progress=0.0, message=str(exc))
        update_source(source_id, ingested=False)
        raise


def _ingest_json(source: SourceRecord, settings) -> tuple[list[Chunk], int]:
    _set_status(source.id, message="Parsing JSON file...")
    entries = parse_json_source(source.source_type, source.file_path)
    total = len(entries)
    _set_status(source.id, progress=0.1, message=f"Loaded {total} entries. Chunking...")

    group_size = JSON_AYAHS_PER_CHUNK if source.source_type == "quran" else JSON_HADITH_PER_CHUNK
    chunks = _chunk_json_entries(entries, source.id, source.source_type, source.file_path, group_size)
    return chunks, total


def _ingest_pdf(source: SourceRecord, settings) -> tuple[list[Chunk], int]:
    _set_status(source.id, message="Parsing PDF...")
    pages = parse_pdf(source.pdf_path)
    total_pages = len(pages)
    scanned = sum(1 for p in pages if p.is_scanned)
    if scanned:
        print(f"[pipeline] {source.id}: {scanned}/{total_pages} scanned pages skipped.")
    _set_status(source.id, progress=0.1, message=f"Parsed {total_pages} pages. Chunking...")

    chunks = chunk_pages(
        pages=pages,
        source_id=source.id,
        source_type=source.source_type,
        pdf_path=source.pdf_path,
        embedding_model=settings.embedding_model,
    )
    return chunks, total_pages
