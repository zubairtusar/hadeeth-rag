from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.api import chat, ingest, pdf_serve, sources

app = FastAPI(title="Hadeeth RAG API", version="1.0.0")

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sources.router)
app.include_router(ingest.router)
app.include_router(chat.router)
app.include_router(pdf_serve.router)


@app.get("/health")
def health():
    return {"status": "ok", "model": settings.groq_model}
