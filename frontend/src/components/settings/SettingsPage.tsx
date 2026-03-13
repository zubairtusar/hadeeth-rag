import { useEffect, useState } from 'react'
import { useAppStore } from '../../store/appStore'
import { addSource, deleteSource, fetchIngestStatus, fetchSources, triggerIngest } from '../../api/sources'
import type { Source, SourceType, AddSourcePayload, IngestionStatus } from '../../types'

const SOURCE_TYPE_LABELS: Record<SourceType, string> = {
  quran: 'Holy Quran',
  bukhari: 'Sahih Bukhari',
  muslim: 'Sahih Muslim',
}

function IngestionProgress({ sourceId, onDone }: { sourceId: string; onDone: () => void }) {
  const [status, setStatus] = useState<IngestionStatus | null>(null)

  useEffect(() => {
    let active = true
    const poll = async () => {
      try {
        const s = await fetchIngestStatus(sourceId)
        if (!active) return
        setStatus(s)
        if (s.status === 'running' || s.status === 'pending') {
          setTimeout(poll, 2000)
        } else {
          onDone()
        }
      } catch {
        if (active) setTimeout(poll, 3000)
      }
    }
    poll()
    return () => { active = false }
  }, [sourceId, onDone])

  if (!status) return <span className="text-xs text-gray-500">Starting...</span>

  if (status.status === 'done') {
    return <span className="text-xs text-emerald-400">✓ {status.chunk_count} chunks</span>
  }
  if (status.status === 'error') {
    return <span className="text-xs text-red-400">✗ {status.message}</span>
  }

  return (
    <div className="flex items-center gap-2">
      <div className="w-24 h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div
          className="h-full bg-indigo-500 rounded-full transition-all duration-500"
          style={{ width: `${Math.round(status.progress * 100)}%` }}
        />
      </div>
      <span className="text-xs text-gray-400">{Math.round(status.progress * 100)}%</span>
    </div>
  )
}

function SourceRow({ source, onRefresh }: { source: Source; onRefresh: () => void }) {
  const updateSource = useAppStore((s) => s.updateSource)
  const [ingesting, setIngesting] = useState(false)

  const handleIngest = async () => {
    setIngesting(true)
    updateSource(source.id, { ingested: false })
    await triggerIngest(source.id)
  }

  const handleDelete = async () => {
    if (!confirm(`Remove "${source.label}"? Its vectors will be deleted.`)) return
    await deleteSource(source.id)
    onRefresh()
  }

  const handleIngestDone = () => {
    setIngesting(false)
    onRefresh()
  }

  return (
    <div className="flex items-center gap-3 px-4 py-3 bg-gray-800 rounded-xl border border-gray-700">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className="text-sm font-medium text-gray-200">{source.label}</span>
          <span className="text-xs px-1.5 py-0.5 rounded bg-gray-700 text-gray-400">
            {SOURCE_TYPE_LABELS[source.source_type]}
          </span>
        </div>
        <p className="text-xs text-gray-500 truncate">{source.pdf_path}</p>
        <div className="mt-1">
          {ingesting ? (
            <IngestionProgress sourceId={source.id} onDone={handleIngestDone} />
          ) : source.ingested ? (
            <span className="text-xs text-emerald-400">✓ Indexed — {source.chunk_count} chunks, {source.page_count} pages</span>
          ) : (
            <span className="text-xs text-gray-500">Not indexed</span>
          )}
        </div>
      </div>
      <div className="flex gap-2 flex-shrink-0">
        <button
          onClick={handleIngest}
          disabled={ingesting}
          className="text-xs px-2.5 py-1 rounded bg-indigo-700 hover:bg-indigo-600 text-white disabled:opacity-40 transition-colors"
        >
          {ingesting ? 'Indexing...' : source.ingested ? 'Re-index' : 'Index'}
        </button>
        <button
          onClick={handleDelete}
          className="text-xs px-2.5 py-1 rounded bg-gray-700 hover:bg-red-800 text-gray-300 hover:text-red-200 transition-colors"
        >
          Remove
        </button>
      </div>
    </div>
  )
}

function AddSourceForm({ onAdded }: { onAdded: () => void }) {
  const [label, setLabel] = useState('')
  const [sourceType, setSourceType] = useState<SourceType>('bukhari')
  const [sourceFormat, setSourceFormat] = useState<'pdf' | 'json'>('pdf')
  const [filePath, setFilePath] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    if (!label.trim() || !filePath.trim()) {
      setError('Label and file path are required.')
      return
    }
    setError('')
    setLoading(true)
    try {
      const payload: AddSourcePayload = {
        label: label.trim(),
        source_type: sourceType,
        source_format: sourceFormat,
        pdf_path: sourceFormat === 'pdf' ? filePath.trim() : '',
        file_path: sourceFormat === 'json' ? filePath.trim() : '',
      }
      await addSource(payload)
      setLabel('')
      setFilePath('')
      onAdded()
    } catch (err: any) {
      setError(err.message || 'Failed to add source')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 p-4">
      <h3 className="text-sm font-semibold text-gray-200 mb-3">Add Source</h3>
      <div className="space-y-3">
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Label</label>
          <input
            type="text"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            placeholder="e.g. Sahih Bukhari Vol 1"
            className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-indigo-500"
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Source Type</label>
            <select
              title="Source Type"
              value={sourceType}
              onChange={(e) => setSourceType(e.target.value as SourceType)}
              className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="quran">Holy Quran</option>
              <option value="bukhari">Sahih Bukhari</option>
              <option value="muslim">Sahih Muslim</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Format</label>
            <select
              title="Source Format"
              value={sourceFormat}
              onChange={(e) => { setSourceFormat(e.target.value as 'pdf' | 'json'); setFilePath('') }}
              className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="pdf">PDF file</option>
              <option value="json">JSON file</option>
            </select>
          </div>
        </div>
        <div>
          <label className="text-xs text-gray-400 mb-1 block">
            {sourceFormat === 'pdf' ? 'PDF File Path' : 'JSON File Path'}
          </label>
          <input
            type="text"
            value={filePath}
            onChange={(e) => setFilePath(e.target.value)}
            placeholder={sourceFormat === 'pdf' ? 'C:\\Users\\you\\Downloads\\quran.pdf' : 'C:\\path\\to\\bukhari.json'}
            className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-indigo-500 font-mono"
          />
          <p className="text-xs text-gray-600 mt-1">Paste the full absolute path to the file on your computer.</p>
        </div>
        {error && <p className="text-xs text-red-400">{error}</p>}
        <button
          type="button"
          onClick={handleSubmit}
          disabled={loading}
          className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-sm font-medium rounded-lg transition-colors"
        >
          {loading ? 'Adding...' : 'Add Source'}
        </button>
      </div>
    </div>
  )
}

export function SettingsPage() {
  const sources = useAppStore((s) => s.sources)
  const setSources = useAppStore((s) => s.setSources)

  const refresh = async () => {
    const data = await fetchSources()
    setSources(data)
  }

  useEffect(() => { refresh() }, [])

  return (
    <div className="flex-1 overflow-y-auto p-6 max-w-2xl mx-auto w-full">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-100">Settings</h1>
        <p className="text-sm text-gray-500 mt-1">Manage your PDF sources. PDFs are indexed locally — nothing is uploaded.</p>
      </div>

      {/* PDF guide */}
      <div className="mb-6 p-4 bg-amber-950/40 border border-amber-800/50 rounded-xl text-sm text-amber-200">
        <p className="font-semibold mb-1">📥 Where to get free PDFs</p>
        <ul className="text-amber-300/80 space-y-1 text-xs list-disc list-inside">
          <li><strong>Quran:</strong> archive.org → search "Quran Saheeh International" or "Noble Quran King Fahd"</li>
          <li><strong>Bukhari:</strong> archive.org → search "Sahih Al-Bukhari Darussalam Arabic English"</li>
          <li><strong>Muslim:</strong> archive.org → search "Sahih Muslim Abdul Hamid Siddiqui"</li>
        </ul>
        <p className="text-amber-400/60 text-xs mt-2">⚠️ Only text-layer PDFs work (you must be able to select text in your browser viewer).</p>
      </div>

      <div className="space-y-4">
        <AddSourceForm onAdded={refresh} />

        {sources.length > 0 && (
          <div>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Registered Sources ({sources.length})</h3>
            <div className="space-y-2">
              {sources.map((s) => (
                <SourceRow key={s.id} source={s} onRefresh={refresh} />
              ))}
            </div>
          </div>
        )}

        {sources.length === 0 && (
          <p className="text-center text-gray-600 text-sm py-8">
            No sources added yet. Add a PDF above to get started.
          </p>
        )}
      </div>
    </div>
  )
}
