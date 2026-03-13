import type { Message, SourceType } from '../types'

export interface StreamEvent {
  type: 'token' | 'citation' | 'done' | 'error'
  content?: string
  chunk_id?: string
  source_label?: string
  pdf_path?: string
  page_number?: number
  ref_id?: string
  display_text?: string
  message?: string
}

export async function* streamChat(
  query: string,
  sourceTypes: SourceType[],
  history: Message[]
): AsyncGenerator<StreamEvent> {
  const conversationHistory = history
    .filter((m) => !m.isStreaming)
    .map((m) => ({ role: m.role, content: m.content }))

  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      source_types: sourceTypes,
      conversation_history: conversationHistory,
    }),
  })

  if (!res.ok || !res.body) {
    yield { type: 'error', message: 'Failed to connect to chat API' }
    return
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      const data = line.slice(6).trim()
      if (!data) continue
      try {
        yield JSON.parse(data) as StreamEvent
      } catch {
        // ignore malformed
      }
    }
  }
}
