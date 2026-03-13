from typing import Literal
from pydantic import BaseModel


SourceType = Literal["quran", "bukhari", "muslim"]
SourceFormat = Literal["pdf", "json"]


class SourceRecord(BaseModel):
    id: str
    label: str
    source_type: SourceType
    source_format: SourceFormat = "pdf"
    # pdf_path: used for PDF sources and for PDF serving in citations
    pdf_path: str = ""
    # file_path: used for JSON sources (the local .json file)
    file_path: str = ""
    ingested: bool = False
    page_count: int | None = None
    chunk_count: int | None = None
    added_at: str = ""


class AddSourceRequest(BaseModel):
    label: str
    source_type: SourceType
    source_format: SourceFormat = "pdf"
    pdf_path: str = ""
    file_path: str = ""


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    query: str
    source_types: list[SourceType]
    conversation_history: list[ChatMessage] = []
