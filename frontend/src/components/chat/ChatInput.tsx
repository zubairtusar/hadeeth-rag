import { useRef, useState, type KeyboardEvent } from 'react'
import { useAppStore } from '../../store/appStore'

interface Props {
  onSend: (text: string) => void
}

export function ChatInput({ onSend }: Props) {
  const [text, setText] = useState('')
  const isLoading = useAppStore((s) => s.isLoading)
  const activeSources = useAppStore((s) => s.activeSources)
  const sources = useAppStore((s) => s.sources)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const ingestedTypes = new Set(
    sources.filter((s) => s.ingested).map((s) => s.source_type)
  )
  const hasIngested = activeSources.some((t) => ingestedTypes.has(t))
  const disabled = isLoading || !text.trim() || activeSources.length === 0

  const handleSend = () => {
    const trimmed = text.trim()
    if (!trimmed || isLoading || activeSources.length === 0) return
    onSend(trimmed)
    setText('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = () => {
    const ta = textareaRef.current
    if (ta) {
      ta.style.height = 'auto'
      ta.style.height = Math.min(ta.scrollHeight, 160) + 'px'
    }
  }

  return (
    <div className="border-t border-gray-700 bg-gray-900 p-4">
      {!hasIngested && activeSources.length > 0 && (
        <p className="text-xs text-amber-400 mb-2 text-center">
          No ingested sources selected. Go to Settings to add PDFs.
        </p>
      )}
      {activeSources.length === 0 && (
        <p className="text-xs text-red-400 mb-2 text-center">
          Select at least one source in the sidebar.
        </p>
      )}
      <div className="flex items-end gap-2 bg-gray-800 rounded-xl border border-gray-600 focus-within:border-indigo-500 transition-colors px-3 py-2">
        <textarea
          ref={textareaRef}
          rows={1}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder="Ask about Quran or Hadith... (Enter to send, Shift+Enter for newline)"
          disabled={isLoading}
          className="flex-1 bg-transparent text-gray-100 placeholder-gray-500 text-sm resize-none outline-none min-h-[24px] max-h-[160px] py-1"
        />
        <button
          onClick={handleSend}
          disabled={disabled}
          className="flex-shrink-0 w-8 h-8 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
          title="Send (Enter)"
        >
          {isLoading ? (
            <svg className="animate-spin w-4 h-4 text-white" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
            </svg>
          ) : (
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          )}
        </button>
      </div>
    </div>
  )
}
