"""
Multilingual embedding using intfloat/multilingual-e5-base.
Enforces the query/passage prefix convention required by this model.
Handles Arabic normalization for better retrieval quality.
"""

import re
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from backend.config import get_settings

# Arabic normalization patterns
_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670]")
_ALEF_RE = re.compile(r"[أإآٱ]")
_TA_MARBUTA_RE = re.compile(r"ة")
_ALEF_MAQSURA_RE = re.compile(r"ى")


def normalize_for_embedding(text: str) -> str:
    """
    Normalize Arabic text for embedding.
    Strips diacritics (tashkeel), normalizes alef variants and ta marbuta.
    English text is unaffected.
    """
    text = _DIACRITICS_RE.sub("", text)
    text = _ALEF_RE.sub("ا", text)
    text = _TA_MARBUTA_RE.sub("ه", text)
    text = _ALEF_MAQSURA_RE.sub("ي", text)
    return text


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    model_name = get_settings().embedding_model
    print(f"[embedder] Loading model: {model_name} (first run downloads ~500MB)")
    return SentenceTransformer(model_name)


def embed_passages(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of passage texts.
    Prepends 'passage: ' as required by multilingual-e5-base.
    """
    if not texts:
        return []
    model = _get_model()
    prefixed = [f"passage: {t}" for t in texts]
    embeddings = model.encode(
        prefixed,
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return embeddings.tolist()


def embed_query(text: str) -> list[float]:
    """
    Embed a single query string.
    Prepends 'query: ' as required by multilingual-e5-base.
    """
    model = _get_model()
    embedding = model.encode(
        f"query: {text}",
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return embedding.tolist()
