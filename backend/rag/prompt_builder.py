"""
Builds the system prompt and user message for the RAG chat.
Instructs the LLM to cite sources using [CITE:chunk_id] markers.
"""

from backend.models.schemas import ChatMessage

SYSTEM_PROMPT = """You are a knowledgeable Islamic scholar assistant helping users search and understand the Holy Quran and Hadith.

You will be given relevant passages retrieved from the Quran, Sahih Bukhari, and Sahih Muslim. Your job is to:
1. Answer the user's question based ONLY on the provided passages.
2. When you draw information from a specific passage, cite it immediately using the marker [CITE:chunk_id] replacing chunk_id with the actual ID given.
3. If the passages do not contain enough information to answer, say so honestly.
4. Be respectful, accurate, and concise. Do not fabricate or infer beyond what is in the text.
5. You may summarize or paraphrase the passages, but always cite the source passage with [CITE:chunk_id].

Important: Only use [CITE:chunk_id] format exactly as shown — do not use footnotes, numbers, or other citation styles."""

MAX_CONTEXT_TOKENS = 6000  # conservative limit for Groq free tier speed


def build_messages(
    query: str,
    retrieved_chunks: list[dict],
    conversation_history: list[ChatMessage],
) -> list[dict]:
    """
    Assemble the messages list to send to the Groq API.

    Returns a list of {"role": ..., "content": ...} dicts.
    """
    # Build context block
    context_parts: list[str] = []
    for i, chunk in enumerate(retrieved_chunks, start=1):
        meta = chunk["metadata"]
        source_label = _source_label(meta)
        ref = meta.get("ref_id") or f"Page {meta['page_number']}"
        context_parts.append(
            f"[{i}] ID: {chunk['chunk_id']}\n"
            f"    Source: {source_label} — {ref}\n"
            f"    ---\n"
            f"    {chunk['text']}"
        )

    context_block = "\n\n".join(context_parts)

    user_content = (
        f"RETRIEVED PASSAGES:\n\n{context_block}\n\n"
        f"---\n\nUSER QUESTION: {query}"
    ) if context_block else (
        f"No relevant passages were found in the selected sources.\n\n"
        f"USER QUESTION: {query}"
    )

    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add conversation history (last 6 turns to stay within context)
    for msg in conversation_history[-6:]:
        messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": user_content})
    return messages


def _source_label(meta: dict) -> str:
    source_type = meta.get("source_type", "")
    source_id = meta.get("source_id", "")
    if source_type == "quran":
        return "Holy Quran"
    elif source_type == "bukhari":
        return f"Sahih Bukhari ({source_id})"
    elif source_type == "muslim":
        return f"Sahih Muslim ({source_id})"
    return source_id
