"""
Groq API client with streaming support.
Parses [CITE:chunk_id] markers out of the token stream and emits them as separate events.
"""

import json
import re
from typing import AsyncGenerator

import httpx

from backend.config import get_settings

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
CITE_RE = re.compile(r"\[CITE:([^\]]+)\]")

# Buffer size for detecting split citation markers across token boundaries
CITE_BUFFER_MAX = 60


async def stream_chat(
    messages: list[dict],
    retrieved_chunks: list[dict],
) -> AsyncGenerator[dict, None]:
    """
    Stream chat completions from Groq.
    Yields dicts:
      {"type": "token", "content": "..."}
      {"type": "citation", "chunk_id": "...", "source_label": "...", "pdf_path": "...", "page_number": N}
      {"type": "done"}
      {"type": "error", "message": "..."}
    """
    settings = get_settings()

    # Build a lookup from chunk_id → chunk metadata for citation resolution
    chunk_lookup: dict[str, dict] = {c["chunk_id"]: c for c in retrieved_chunks}

    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.groq_model,
        "messages": messages,
        "stream": True,
        "temperature": 0.3,
        "max_tokens": 1024,
    }

    buffer = ""  # rolling buffer for partial [CITE:...] tokens

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", GROQ_API_URL, headers=headers, json=payload) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    yield {"type": "error", "message": f"Groq API error {resp.status_code}: {body.decode()}"}
                    return

                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break

                    try:
                        obj = json.loads(data)
                    except json.JSONDecodeError:
                        continue

                    delta = obj.get("choices", [{}])[0].get("delta", {})
                    token = delta.get("content", "")
                    if not token:
                        continue

                    buffer += token

                    # Flush safe prefix (everything before any potential [CITE opening)
                    safe, buffer = _split_safe(buffer)
                    if safe:
                        # Scan the safe portion for complete [CITE:...] markers
                        async for event in _process_text(safe, chunk_lookup):
                            yield event

                    # If buffer is growing large without a match, flush it
                    if len(buffer) > CITE_BUFFER_MAX:
                        async for event in _process_text(buffer, chunk_lookup):
                            yield event
                        buffer = ""

        # Flush remaining buffer
        if buffer:
            async for event in _process_text(buffer, chunk_lookup):
                yield event

        yield {"type": "done"}

    except httpx.TimeoutException:
        yield {"type": "error", "message": "Request to Groq API timed out."}
    except Exception as exc:
        yield {"type": "error", "message": str(exc)}


def _split_safe(text: str) -> tuple[str, str]:
    """
    Split text into a safe-to-emit prefix and a buffer suffix.
    The buffer may contain an incomplete [CITE:...] marker.
    """
    idx = text.rfind("[")
    if idx == -1:
        return text, ""
    # If there's already a complete citation in the text up to idx, keep everything safe
    after = text[idx:]
    if "]" in after:
        # Complete marker present in the suffix — return all as safe
        return text, ""
    return text[:idx], text[idx:]


async def _process_text(text: str, chunk_lookup: dict) -> AsyncGenerator[dict, None]:
    """Scan text for [CITE:id] markers, emit citation events and plain token events."""
    last = 0
    for match in CITE_RE.finditer(text):
        before = text[last : match.start()]
        if before:
            yield {"type": "token", "content": before}
        chunk_id = match.group(1).strip()
        chunk = chunk_lookup.get(chunk_id)
        if chunk:
            meta = chunk["metadata"]
            from backend.rag.prompt_builder import _source_label
            yield {
                "type": "citation",
                "chunk_id": chunk_id,
                "source_label": _source_label(meta),
                "pdf_path": meta.get("pdf_path", ""),
                "page_number": meta.get("page_number", 1),
                "ref_id": meta.get("ref_id", ""),
                "display_text": chunk.get("text", ""),
            }
        last = match.end()

    remaining = text[last:]
    if remaining:
        yield {"type": "token", "content": remaining}
