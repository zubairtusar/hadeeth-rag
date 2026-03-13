import { useEffect, useRef } from 'react'
import { useAppStore } from '../../store/appStore'
import { streamChat } from '../../api/chat'
import type { Citation, Message } from '../../types'
import { MessageBubble } from './MessageBubble'
import { ChatInput } from './ChatInput'

function EmptyState() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center text-center px-4">
      <div className="text-4xl mb-4">📖</div>
      <h2 className="text-xl font-semibold text-gray-200 mb-2">Islamic Text Search</h2>
      <p className="text-gray-500 text-sm max-w-sm">
        Ask questions about the Quran, Sahih Bukhari, or Sahih Muslim. Select sources in the sidebar, then start chatting.
      </p>
    </div>
  )
}

export function ChatWindow() {
  const messages = useAppStore((s) => s.messages)
  const activeSources = useAppStore((s) => s.activeSources)
  const { addMessage, appendToken, addCitation, finalizeMessage, setLoading } = useAppStore()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (text: string) => {
    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      citations: [],
    }
    addMessage(userMsg)

    const assistantId = `assistant-${Date.now()}`
    const assistantMsg: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      citations: [],
      isStreaming: true,
    }
    addMessage(assistantMsg)
    setLoading(true)

    try {
      for await (const event of streamChat(text, activeSources, messages)) {
        if (event.type === 'token' && event.content) {
          appendToken(assistantId, event.content)
        } else if (event.type === 'citation') {
          const citation: Citation = {
            chunkId: event.chunk_id!,
            sourceLabel: event.source_label!,
            pdfPath: event.pdf_path ?? '',
            pageNumber: event.page_number ?? 0,
            refId: event.ref_id ?? '',
            displayText: event.display_text ?? '',
          }
          addCitation(assistantId, citation)
        } else if (event.type === 'error') {
          appendToken(assistantId, `\n\n⚠️ Error: ${event.message}`)
        }
      }
    } catch (err) {
      appendToken(assistantId, '\n\n⚠️ Connection error. Is the backend running?')
    } finally {
      finalizeMessage(assistantId)
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {messages.length === 0 ? (
          <EmptyState />
        ) : (
          messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
        )}
        <div ref={bottomRef} />
      </div>
      <ChatInput onSend={handleSend} />
    </div>
  )
}
