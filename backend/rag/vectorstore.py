"""
ChromaDB vector store with three separate collections:
  - quran
  - hadith_bukhari
  - hadith_muslim

Uses cosine similarity. Collections are created on first access.
"""

from functools import lru_cache

import chromadb
from chromadb import Collection

from backend.config import get_settings
from backend.ingestion.chunker import Chunk

COLLECTION_MAP: dict[str, str] = {
    "quran": "quran",
    "bukhari": "hadith_bukhari",
    "muslim": "hadith_muslim",
}

UPSERT_BATCH_SIZE = 100


@lru_cache(maxsize=1)
def _get_client() -> chromadb.PersistentClient:
    path = get_settings().chroma_db_path
    return chromadb.PersistentClient(path=path)


def _get_collection(source_type: str) -> Collection:
    client = _get_client()
    name = COLLECTION_MAP.get(source_type, source_type)
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def upsert_chunks(chunks: list[Chunk], embeddings: list[list[float]]) -> None:
    """Upsert chunks with their embeddings into the appropriate collection."""
    if not chunks:
        return

    # Group by source_type
    groups: dict[str, list[tuple[Chunk, list[float]]]] = {}
    for chunk, emb in zip(chunks, embeddings):
        groups.setdefault(chunk.source_type, []).append((chunk, emb))

    for source_type, items in groups.items():
        collection = _get_collection(source_type)
        # Process in batches
        for i in range(0, len(items), UPSERT_BATCH_SIZE):
            batch = items[i : i + UPSERT_BATCH_SIZE]
            ids = [
                f"{c.source_id}_{int(c.page_number):04d}_{c.chunk_index:04d}"
                for c, _ in batch
            ]
            docs = [c.display_text for c, _ in batch]
            embs = [e for _, e in batch]
            metas = [
                {
                    "source_id": c.source_id,
                    "source_type": c.source_type,
                    "pdf_path": c.pdf_path,
                    "page_number": c.page_number,
                    "chunk_index": c.chunk_index,
                    "arabic_ratio": c.arabic_ratio,
                    "ref_id": c.ref_id,
                }
                for c, _ in batch
            ]
            collection.upsert(ids=ids, documents=docs, embeddings=embs, metadatas=metas)


def query_collection(
    source_type: str,
    query_embedding: list[float],
    n_results: int = 5,
) -> list[dict]:
    """
    Query a single collection and return results as dicts with text + metadata.
    """
    collection = _get_collection(source_type)
    try:
        count = collection.count()
    except Exception:
        count = 0

    if count == 0:
        return []

    n_results = min(n_results, count)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    output: list[dict] = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        output.append({"text": doc, "metadata": meta, "distance": dist})

    return output


def delete_source_chunks(source_id: str) -> None:
    """Remove all chunks belonging to a source from all collections."""
    client = _get_client()
    for collection_name in COLLECTION_MAP.values():
        try:
            col = client.get_collection(collection_name)
            col.delete(where={"source_id": source_id})
        except Exception:
            pass  # Collection may not exist yet
