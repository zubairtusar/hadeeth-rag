from pathlib import Path

from fastapi import APIRouter, HTTPException

from backend.models.schemas import AddSourceRequest, SourceRecord
from backend.models.source_registry import add_source, delete_source, list_sources

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("", response_model=list[SourceRecord])
def get_sources():
    return list_sources()


@router.post("", response_model=SourceRecord, status_code=201)
def create_source(req: AddSourceRequest):
    if req.source_format == "json":
        path = Path(req.file_path)
        if not path.exists():
            raise HTTPException(status_code=400, detail=f"File not found: {req.file_path}")
        if path.suffix.lower() != ".json":
            raise HTTPException(status_code=400, detail="File must be a .json")
    else:
        path = Path(req.pdf_path)
        if not path.exists():
            raise HTTPException(status_code=400, detail=f"File not found: {req.pdf_path}")
        if path.suffix.lower() != ".pdf":
            raise HTTPException(status_code=400, detail="File must be a .pdf")
    return add_source(req)


@router.delete("/{source_id}", status_code=204)
def remove_source(source_id: str):
    from backend.rag.vectorstore import delete_source_chunks

    deleted = delete_source(source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Source not found")
    delete_source_chunks(source_id)
