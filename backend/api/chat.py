import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.groq_client import stream_chat
from backend.models.schemas import ChatRequest
from backend.rag.prompt_builder import build_messages
from backend.rag.retriever import retrieve

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
async def chat(req: ChatRequest):
    if not req.source_types:
        async def _no_sources():
            yield f"data: {json.dumps({'type': 'error', 'message': 'No source types selected.'})}\n\n"
        return StreamingResponse(_no_sources(), media_type="text/event-stream")

    # Retrieve relevant chunks
    chunks = retrieve(query=req.query, source_types=req.source_types)

    # Build prompt messages
    messages = build_messages(
        query=req.query,
        retrieved_chunks=chunks,
        conversation_history=req.conversation_history,
    )

    async def event_stream():
        async for event in stream_chat(messages=messages, retrieved_chunks=chunks):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
