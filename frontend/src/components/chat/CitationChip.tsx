import type { Citation } from '../../types'
import { useAppStore } from '../../store/appStore'

interface Props {
  citation: Citation
  index: number
}

const SOURCE_COLORS: Record<string, string> = {
  quran: 'bg-emerald-900/50 text-emerald-300 border-emerald-700 hover:bg-emerald-800/60',
  bukhari: 'bg-blue-900/50 text-blue-300 border-blue-700 hover:bg-blue-800/60',
  muslim: 'bg-purple-900/50 text-purple-300 border-purple-700 hover:bg-purple-800/60',
}

function getColor(label: string): string {
  const lower = label.toLowerCase()
  if (lower.includes('quran')) return SOURCE_COLORS.quran
  if (lower.includes('bukhari')) return SOURCE_COLORS.bukhari
  if (lower.includes('muslim')) return SOURCE_COLORS.muslim
  return 'bg-gray-800 text-gray-300 border-gray-600 hover:bg-gray-700'
}

export function CitationChip({ citation, index }: Props) {
  const setOpenCitation = useAppStore((s) => s.setOpenCitation)
  const isJsonSource = !citation.pdfPath

  // For JSON sources: show ref_id (e.g. "2:255" or "Book 1, Hadith 3")
  // For PDF sources: show page number
  const refLabel = isJsonSource
    ? citation.refId || citation.sourceLabel
    : `p.${citation.pageNumber}`

  const titleText = isJsonSource
    ? `${citation.sourceLabel} — ${citation.refId}`
    : `${citation.sourceLabel} — Page ${citation.pageNumber}`

  return (
    <button
      onClick={() => setOpenCitation(citation)}
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium transition-colors cursor-pointer ${getColor(citation.sourceLabel)}`}
      title={titleText}
    >
      <span className="opacity-60">[{index}]</span>
      <span>{citation.sourceLabel}</span>
      <span className="opacity-60">{refLabel}</span>
    </button>
  )
}
