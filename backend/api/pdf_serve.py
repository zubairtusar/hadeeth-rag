"""
Serves local PDF files securely.
Only paths that start with an allowed prefix (from settings) are served.
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from backend.config import get_settings

router = APIRouter(prefix="/api/pdf", tags=["pdf"])


def _is_allowed(path: str) -> bool:
    settings = get_settings()
    norm = Path(path).resolve().as_posix().lower()
    for prefix in settings.pdf_allowed_prefixes:
        if norm.startswith(Path(prefix).as_posix().lower()):
            return True
    return False


@router.get("")
def serve_pdf(path: str = Query(..., description="Absolute path to the PDF file")):
    if not _is_allowed(path):
        raise HTTPException(status_code=403, detail="Access to this path is not allowed.")

    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="PDF file not found.")
    if file_path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files can be served.")

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        headers={"Content-Disposition": "inline"},
    )
