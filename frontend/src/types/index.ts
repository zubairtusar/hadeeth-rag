export type SourceType = 'quran' | 'bukhari' | 'muslim'
export type SourceFormat = 'pdf' | 'json'

export interface Citation {
  chunkId: string
  sourceLabel: string
  pdfPath: string       // empty string for JSON sources
  pageNumber: number
  refId: string         // e.g. "2:255" or "Book 1, Hadith 3" — for JSON sources
  displayText: string   // snippet text for JSON citation popover
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations: Citation[]
  isStreaming?: boolean
}

export interface Source {
  id: string
  label: string
  source_type: SourceType
  source_format: SourceFormat
  pdf_path: string
  file_path: string
  ingested: boolean
  page_count: number | null
  chunk_count: number | null
  added_at: string
}

export interface IngestionStatus {
  status: 'pending' | 'running' | 'done' | 'error'
  progress: number
  message: string
  chunk_count: number
}

export interface AddSourcePayload {
  label: string
  source_type: SourceType
  source_format: SourceFormat
  pdf_path: string
  file_path: string
}
