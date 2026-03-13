"""
JSON source parser for Quran and Hadith datasets.

Supported formats:
  - Quran (alquran.cloud): {data: {surahs: [{number, englishName, ayahs: [{numberInSurah, text, page}]}]}}
  - Hadith (fawazahmed0 hadith-api): {metadata: {sections: {...}}, hadiths: [{hadithnumber, text, reference: {book, hadith}}]}
"""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TextEntry:
    """A single extractable text unit from a JSON source."""
    ref_id: str          # human-readable reference, e.g. "2:255" or "Book 1, Hadith 3"
    ref_number: int      # numeric key for ordering / citation (ayah number or hadith number)
    book_number: int     # surah number or book number
    text: str
    section_label: str   # e.g. "Al-Baqarah" or "The Book of Faith"


def parse_quran_json(file_path: str | Path) -> list[TextEntry]:
    """
    Parse an alquran.cloud-format JSON file into TextEntry objects.
    Each entry = one ayah.
    """
    data = json.loads(Path(file_path).read_text(encoding="utf-8"))
    surahs = data["data"]["surahs"]

    entries: list[TextEntry] = []
    for surah in surahs:
        surah_num = surah["number"]
        surah_name = surah.get("englishName", f"Surah {surah_num}")
        for ayah in surah["ayahs"]:
            ayah_in_surah = ayah["numberInSurah"]
            entries.append(
                TextEntry(
                    ref_id=f"{surah_num}:{ayah_in_surah}",
                    ref_number=ayah["number"],          # global ayah number 1-6236
                    book_number=surah_num,
                    text=ayah["text"].strip(),
                    section_label=surah_name,
                )
            )
    return entries


def parse_hadith_json(file_path: str | Path) -> list[TextEntry]:
    """
    Parse a fawazahmed0/hadith-api-format JSON file into TextEntry objects.
    Each entry = one hadith.
    """
    data = json.loads(Path(file_path).read_text(encoding="utf-8"))
    sections: dict[str, str] = data.get("metadata", {}).get("sections", {})
    hadiths = data["hadiths"]

    entries: list[TextEntry] = []
    for h in hadiths:
        text = h.get("text", "").strip()
        if not text:
            continue
        ref = h.get("reference", {})
        book_num = int(float(ref.get("book", 0)))
        hadith_num = ref.get("hadith", h.get("hadithnumber", 0))
        hadith_global = int(float(h.get("hadithnumber", 0)))
        section_label = sections.get(str(book_num), f"Book {book_num}")

        entries.append(
            TextEntry(
                ref_id=f"Book {book_num}, Hadith {hadith_num}",
                ref_number=hadith_global,
                book_number=book_num,
                text=text,
                section_label=section_label,
            )
        )
    return entries


def parse_json_source(source_type: str, file_path: str | Path) -> list[TextEntry]:
    """Dispatch to the correct parser based on source_type."""
    if source_type == "quran":
        return parse_quran_json(file_path)
    elif source_type in ("bukhari", "muslim"):
        return parse_hadith_json(file_path)
    else:
        raise ValueError(f"Unknown source_type for JSON parsing: {source_type}")
