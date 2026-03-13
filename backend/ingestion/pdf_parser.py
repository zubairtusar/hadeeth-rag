"""
PDF text extraction using PyMuPDF.
Handles Arabic RTL text ordering and detects scanned (image-only) pages.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF


ARABIC_RE = re.compile(r"[\u0600-\u06FF]")
MIN_TEXT_CHARS = 50  # pages with fewer chars are likely scanned


@dataclass
class PageText:
    page_number: int  # 1-indexed
    text: str
    arabic_ratio: float
    is_scanned: bool


def _arabic_ratio(text: str) -> float:
    if not text:
        return 0.0
    arabic = sum(1 for c in text if "\u0600" <= c <= "\u06FF")
    return arabic / len(text)


def _extract_page_text(page: fitz.Page) -> str:
    """
    Extract text from a page with RTL-aware span sorting.
    For Arabic/RTL content, spans on each line are sorted right-to-left (descending x).
    """
    try:
        page_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
    except Exception:
        return ""

    lines_out: list[str] = []

    for block in page_dict.get("blocks", []):
        if block.get("type") != 0:  # 0 = text block
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue

            # Determine dominant script for this line
            line_text_raw = " ".join(s.get("text", "") for s in spans)
            ratio = _arabic_ratio(line_text_raw)

            if ratio > 0.3:
                # RTL: sort spans by x-origin descending (right to left)
                spans = sorted(spans, key=lambda s: s.get("origin", (0, 0))[0], reverse=True)

            line_text = " ".join(s.get("text", "").strip() for s in spans if s.get("text", "").strip())
            if line_text:
                lines_out.append(line_text)

    return "\n".join(lines_out)


def parse_pdf(pdf_path: str | Path) -> list[PageText]:
    """
    Open a PDF and extract text from every page.
    Returns a list of PageText objects (one per page).
    Scanned pages are included but flagged with is_scanned=True.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    results: list[PageText] = []

    doc = fitz.open(str(path))
    try:
        for page_index in range(len(doc)):
            page = doc[page_index]
            text = _extract_page_text(page)
            clean_text = text.strip()

            is_scanned = len(clean_text) < MIN_TEXT_CHARS
            ratio = _arabic_ratio(clean_text)

            results.append(
                PageText(
                    page_number=page_index + 1,
                    text=clean_text,
                    arabic_ratio=ratio,
                    is_scanned=is_scanned,
                )
            )
    finally:
        doc.close()

    return results
