"""
Token-aware, boundary-aware text chunker for Quran and Hadith PDFs.
Respects ayah (verse) and hadith number boundaries when splitting.
"""

import re
from dataclasses import dataclass

from transformers import AutoTokenizer

from backend.ingestion.pdf_parser import PageText

# Boundary markers — patterns that indicate a natural split point
# Quran: Arabic verse markers ﴿١﴾ or English (1), (2)
# Hadith: "Hadith No." / "Book X, Number Y" / Arabic hadith markers
BOUNDARY_RE = re.compile(
    r"(?:"
    r"﴿\d+﴾"                          # Arabic ayah number ﴿١﴾
    r"|【\d+】"                         # Chinese-style markers sometimes in PDFs
    r"|\(\s*\d{1,4}\s*\)"              # English (1) style verse numbers
    r"|(?:^|\n)Hadith\s+No\.?\s*\d+"  # "Hadith No. 123"
    r"|(?:^|\n)Book\s+\d+[,،]\s*(?:Hadith|Number)\s+\d+"  # "Book 2, Hadith 45"
    r"|(?:^|\n)\d{1,4}\s*[–\-]\s*\d{1,4}"  # "123 - 456" hadith range headers
    r")",
    re.MULTILINE | re.IGNORECASE,
)

_tokenizer_cache: dict[str, AutoTokenizer] = {}


def _get_tokenizer(model_name: str) -> AutoTokenizer:
    if model_name not in _tokenizer_cache:
        _tokenizer_cache[model_name] = AutoTokenizer.from_pretrained(model_name)
    return _tokenizer_cache[model_name]


def _token_count(text: str, tokenizer: AutoTokenizer) -> int:
    return len(tokenizer.encode(text, add_special_tokens=False))


@dataclass
class Chunk:
    source_id: str
    source_type: str
    pdf_path: str
    page_number: int
    chunk_index: int
    text: str           # normalized text for embedding
    display_text: str   # original text with diacritics for display
    arabic_ratio: float
    ref_id: str = ""    # human-readable citation ref, e.g. "2:255" or "Book 1, Hadith 3"


def _split_into_segments(text: str) -> list[str]:
    """Split text at natural Quran/Hadith boundaries, or by paragraphs."""
    # Try boundary-based split first
    parts = BOUNDARY_RE.split(text)
    # Recombine: the boundary marker belongs with the segment that follows it
    matches = list(BOUNDARY_RE.finditer(text))
    if not matches:
        # Fall back to paragraph split
        return [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]

    segments: list[str] = []
    if parts[0].strip():
        segments.append(parts[0].strip())
    for i, match in enumerate(matches):
        seg = match.group() + (parts[i + 1] if i + 1 < len(parts) else "")
        if seg.strip():
            segments.append(seg.strip())
    return segments


def chunk_pages(
    pages: list[PageText],
    source_id: str,
    source_type: str,
    pdf_path: str,
    embedding_model: str,
    target_tokens: int = 450,
    overlap_tokens: int = 60,
) -> list[Chunk]:
    """
    Convert extracted page texts into overlapping chunks.
    Each chunk is roughly target_tokens long with overlap_tokens of carry-over.
    """
    from backend.rag.embedder import normalize_for_embedding  # avoid circular at module level

    tokenizer = _get_tokenizer(embedding_model)
    chunks: list[Chunk] = []
    chunk_index = 0

    carry_text = ""  # overlap carry from previous chunk
    carry_page = 1

    for page in pages:
        if page.is_scanned or not page.text:
            continue

        combined = (carry_text + "\n" + page.text).strip() if carry_text else page.text
        segments = _split_into_segments(combined)

        current_tokens = 0
        current_parts: list[str] = []
        current_page = carry_page

        for seg in segments:
            seg_tokens = _token_count(seg, tokenizer)

            if seg_tokens > target_tokens:
                # Segment itself is too large: split by sentences
                sentences = re.split(r"(?<=[.!?؟])\s+", seg)
                for sent in sentences:
                    sent_tokens = _token_count(sent, tokenizer)
                    if current_tokens + sent_tokens > target_tokens and current_parts:
                        _emit_chunk(
                            chunks, chunk_index, current_parts,
                            source_id, source_type, pdf_path,
                            current_page, page.arabic_ratio, normalize_for_embedding,
                        )
                        chunk_index += 1
                        # Overlap: keep last overlap_tokens worth
                        current_parts, current_tokens = _trim_to_overlap(
                            current_parts, overlap_tokens, tokenizer
                        )
                    current_parts.append(sent)
                    current_tokens += sent_tokens
                    current_page = page.page_number
            else:
                if current_tokens + seg_tokens > target_tokens and current_parts:
                    _emit_chunk(
                        chunks, chunk_index, current_parts,
                        source_id, source_type, pdf_path,
                        current_page, page.arabic_ratio, normalize_for_embedding,
                    )
                    chunk_index += 1
                    current_parts, current_tokens = _trim_to_overlap(
                        current_parts, overlap_tokens, tokenizer
                    )
                current_parts.append(seg)
                current_tokens += seg_tokens
                current_page = page.page_number

        # Save carry for next page
        if current_parts:
            carry_parts, _ = _trim_to_overlap(current_parts, overlap_tokens, tokenizer)
            carry_text = " ".join(carry_parts)
            carry_page = current_page
        else:
            carry_text = ""

    # Flush remaining
    if current_parts:
        _emit_chunk(
            chunks, chunk_index, current_parts,
            source_id, source_type, pdf_path,
            carry_page, pages[-1].arabic_ratio if pages else 0.0,
            normalize_for_embedding,
        )

    return chunks


def _emit_chunk(
    chunks: list[Chunk],
    chunk_index: int,
    parts: list[str],
    source_id: str,
    source_type: str,
    pdf_path: str,
    page_number: int,
    arabic_ratio: float,
    normalize_fn,
) -> None:
    display_text = " ".join(parts).strip()
    if not display_text:
        return
    chunks.append(
        Chunk(
            source_id=source_id,
            source_type=source_type,
            pdf_path=pdf_path,
            page_number=page_number,
            chunk_index=chunk_index,
            text=normalize_fn(display_text),
            display_text=display_text,
            arabic_ratio=arabic_ratio,
        )
    )


def _trim_to_overlap(
    parts: list[str], overlap_tokens: int, tokenizer: AutoTokenizer
) -> tuple[list[str], int]:
    """Return a suffix of parts totalling at most overlap_tokens."""
    result: list[str] = []
    total = 0
    for part in reversed(parts):
        t = _token_count(part, tokenizer)
        if total + t > overlap_tokens:
            break
        result.insert(0, part)
        total += t
    return result, total
