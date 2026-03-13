import threading

from fastapi import APIRouter, BackgroundTasks, HTTPException

from backend.ingestion.pipeline import IngestionStatus, get_status, run_ingestion
from backend.models.source_registry import get_source, update_source

router = APIRouter(prefix="/api/ingest", tags=["ingest"])


@router.post("/{source_id}", status_code=202)
def trigger_ingest(source_id: str, background_tasks: BackgroundTasks):
    source = get_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    # Reset ingested flag while running
    update_source(source_id, ingested=False)

    # Run in a thread so we don't block the event loop
    thread = threading.Thread(target=run_ingestion, args=(source,), daemon=True)
    thread.start()

    return {"message": f"Ingestion started for '{source.label}'", "source_id": source_id}


@router.get("/status/{source_id}", response_model=IngestionStatus)
def ingest_status(source_id: str):
    source = get_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return get_status(source_id)
