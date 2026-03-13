import json
import re
from datetime import datetime, timezone
from pathlib import Path

from backend.config import get_settings
from backend.models.schemas import AddSourceRequest, SourceRecord


def _registry_path() -> Path:
    return Path(get_settings().sources_json_path)


def _load() -> list[SourceRecord]:
    path = _registry_path()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("[]")
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [SourceRecord(**item) for item in data]


def _save(records: list[SourceRecord]) -> None:
    path = _registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([r.model_dump() for r in records], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _make_id(label: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
    return base[:40]


def list_sources() -> list[SourceRecord]:
    return _load()


def get_source(source_id: str) -> SourceRecord | None:
    return next((s for s in _load() if s.id == source_id), None)


def add_source(req: AddSourceRequest) -> SourceRecord:
    records = _load()
    source_id = _make_id(req.label)
    # Ensure uniqueness
    existing_ids = {r.id for r in records}
    candidate = source_id
    i = 2
    while candidate in existing_ids:
        candidate = f"{source_id}_{i}"
        i += 1
    record = SourceRecord(
        id=candidate,
        label=req.label,
        source_type=req.source_type,
        pdf_path=req.pdf_path,
        added_at=datetime.now(timezone.utc).isoformat(),
    )
    records.append(record)
    _save(records)
    return record


def delete_source(source_id: str) -> bool:
    records = _load()
    new_records = [r for r in records if r.id != source_id]
    if len(new_records) == len(records):
        return False
    _save(new_records)
    return True


def update_source(source_id: str, **kwargs) -> SourceRecord | None:
    records = _load()
    for i, r in enumerate(records):
        if r.id == source_id:
            updated = r.model_copy(update=kwargs)
            records[i] = updated
            _save(records)
            return updated
    return None
