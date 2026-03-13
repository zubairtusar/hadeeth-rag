import { create } from 'zustand'
import type { Citation, Message, Source, SourceType } from '../types'

interface AppState {
  // Chat
  messages: Message[]
  isLoading: boolean

  // Source selection
  activeSources: SourceType[]

  // Sources registry
  sources: Source[]

  // PDF modal
  openCitation: Citation | null

  // Actions
  addMessage: (msg: Message) => void
  appendToken: (id: string, token: string) => void
  addCitation: (id: string, citation: Citation) => void
  finalizeMessage: (id: string) => void
  setLoading: (v: boolean) => void

  toggleSource: (type: SourceType) => void
  setSources: (sources: Source[]) => void
  updateSource: (id: string, partial: Partial<Source>) => void

  setOpenCitation: (citation: Citation | null) => void
}

export const useAppStore = create<AppState>((set) => ({
  messages: [],
  isLoading: false,
  activeSources: ['quran', 'bukhari', 'muslim'],
  sources: [],
  openCitation: null,

  addMessage: (msg) =>
    set((state) => ({ messages: [...state.messages, msg] })),

  appendToken: (id, token) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === id ? { ...m, content: m.content + token } : m
      ),
    })),

  addCitation: (id, citation) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === id
          ? { ...m, citations: [...m.citations, citation] }
          : m
      ),
    })),

  finalizeMessage: (id) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === id ? { ...m, isStreaming: false } : m
      ),
    })),

  setLoading: (v) => set({ isLoading: v }),

  toggleSource: (type) =>
    set((state) => ({
      activeSources: state.activeSources.includes(type)
        ? state.activeSources.filter((s) => s !== type)
        : [...state.activeSources, type],
    })),

  setSources: (sources) => set({ sources }),

  updateSource: (id, partial) =>
    set((state) => ({
      sources: state.sources.map((s) =>
        s.id === id ? { ...s, ...partial } : s
      ),
    })),

  setOpenCitation: (citation) => set({ openCitation: citation }),
}))
