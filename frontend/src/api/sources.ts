import type { AddSourcePayload, IngestionStatus, Source } from '../types'

export async function fetchSources(): Promise<Source[]> {
  const res = await fetch('/api/sources')
  if (!res.ok) throw new Error('Failed to fetch sources')
  return res.json()
}

export async function addSource(payload: AddSourcePayload): Promise<Source> {
  const res = await fetch('/api/sources', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to add source')
  }
  return res.json()
}

export async function deleteSource(id: string): Promise<void> {
  const res = await fetch(`/api/sources/${id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Failed to delete source')
}

export async function triggerIngest(id: string): Promise<void> {
  const res = await fetch(`/api/ingest/${id}`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to start ingestion')
}

export async function fetchIngestStatus(id: string): Promise<IngestionStatus> {
  const res = await fetch(`/api/ingest/status/${id}`)
  if (!res.ok) throw new Error('Failed to fetch status')
  return res.json()
}
