"""
Retriever: embeds user query, queries relevant ChromaDB collections,
merges results, and returns top-k chunks sorted by relevance.
"""

from backend.config import get_settings
from backend.rag.embedder import embed_query
from backend.rag.vectorstore import query_collection

COLLECTION_TYPES = ["quran", "bukhari", "muslim"]


def retrieve(
    query: str,
    source_types: list[str],
    top_k: int | None = None,
) -> list[dict]:
    """
    Retrieve top-k relevant chunks across the specified source types.

    Returns a list of dicts, each with:
      - text: str
      - metadata: dict (source_id, source_type, pdf_path, page_number, ...)
      - distance: float (cosine distance; lower = more similar)
      - chunk_id: str  (unique id for citation)
    """
    if not source_types:
        return []

    settings = get_settings()
    k = top_k or settings.top_k_retrieval

    query_emb = embed_query(query)

    # Query each requested collection; fetch more per collection so merge has enough
    per_collection_k = min(k * 2, 20)
    all_results: list[dict] = []

    for source_type in source_types:
        if source_type not in COLLECTION_TYPES:
            continue
        results = query_collection(source_type, query_emb, n_results=per_collection_k)
        for r in results:
            meta = r["metadata"]
            chunk_id = (
                f"{meta['source_id']}_{meta['page_number']:04d}_{meta['chunk_index']:04d}"
            )
            all_results.append(
                {
                    "chunk_id": chunk_id,
                    "text": r["text"],
                    "metadata": meta,
                    "distance": r["distance"],
                }
            )

    # Sort by distance ascending (most similar first) and take top-k
    all_results.sort(key=lambda x: x["distance"])
    return all_results[:k]
