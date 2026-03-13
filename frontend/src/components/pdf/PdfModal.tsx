import { useEffect, useState } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import { useAppStore } from '../../store/appStore'

import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url
).toString()

/** Text panel for JSON-sourced citations (Quran/Hadith structured data) */
function TextCitationPanel() {
  const openCitation = useAppStore((s) => s.openCitation)!
  return (
    <div className="flex-1 overflow-auto p-6 bg-gray-950 rounded-b-2xl">
      <div className="max-w-xl mx-auto">
        <p className="text-xs text-gray-500 mb-4 uppercase tracking-wider">Retrieved passage</p>
        <div className="space-y-4">
          {openCitation.displayText.split('\n\n').map((block, i) => {
            // Each block looks like "[2:255] Text here..."
            const match = block.match(/^\[([^\]]+)\]\s*(.*)$/s)
            if (match) {
              return (
                <div key={i} className="border border-gray-700 rounded-xl p-4 bg-gray-900">
                  <p className="text-xs font-mono text-indigo-400 mb-2">{match[1]}</p>
                  <p className="text-sm text-gray-200 leading-relaxed">{match[2]}</p>
                </div>
              )
            }
            return (
              <p key={i} className="text-sm text-gray-200 leading-relaxed">{block}</p>
            )
          })}
        </div>
      </div>
    </div>
  )
}

/** PDF viewer for PDF-sourced citations */
function PdfViewerPanel() {
  const openCitation = useAppStore((s) => s.openCitation)!
  const [numPages, setNumPages] = useState<number | null>(null)
  const [currentPage, setCurrentPage] = useState(openCitation.pageNumber)
  const [scale, setScale] = useState(1.2)

  useEffect(() => {
    setCurrentPage(openCitation.pageNumber)
  }, [openCitation.pageNumber])

  const pdfUrl = `/api/pdf?path=${encodeURIComponent(openCitation.pdfPath)}`

  return (
    <>
      <div className="flex items-center gap-2 px-4 py-2 border-b border-gray-700">
        <button type="button" onClick={() => setScale((s) => Math.max(0.6, s - 0.2))}
          className="px-2 py-1 text-xs text-gray-400 hover:text-gray-200 bg-gray-800 rounded hover:bg-gray-700 transition-colors">−</button>
        <span className="text-xs text-gray-400 w-10 text-center">{Math.round(scale * 100)}%</span>
        <button type="button" onClick={() => setScale((s) => Math.min(2.5, s + 0.2))}
          className="px-2 py-1 text-xs text-gray-400 hover:text-gray-200 bg-gray-800 rounded hover:bg-gray-700 transition-colors">+</button>
      </div>
      <div className="flex-1 overflow-auto flex justify-center p-4 bg-gray-950">
        <Document
          file={pdfUrl}
          onLoadSuccess={({ numPages }) => setNumPages(numPages)}
          onLoadError={(err) => console.error('PDF load error:', err)}
          loading={<div className="flex items-center justify-center h-64 text-gray-500">Loading PDF...</div>}
          error={<div className="flex items-center justify-center h-64 text-red-400 text-sm text-center px-4">
            Failed to load PDF. Check that the file path is correct and allowed in settings.
          </div>}
        >
          <Page pageNumber={currentPage} scale={scale} renderTextLayer renderAnnotationLayer />
        </Document>
      </div>
      {numPages && numPages > 1 && (
        <div className="flex items-center justify-center gap-3 px-4 py-3 border-t border-gray-700">
          <button type="button" disabled={currentPage <= 1} onClick={() => setCurrentPage((p) => p - 1)}
            className="px-3 py-1 text-sm text-gray-400 hover:text-gray-200 disabled:opacity-30 disabled:cursor-not-allowed bg-gray-800 rounded hover:bg-gray-700 transition-colors">
            ← Prev
          </button>
          <span className="text-xs text-gray-500">{currentPage} / {numPages}</span>
          <button type="button" disabled={currentPage >= numPages} onClick={() => setCurrentPage((p) => p + 1)}
            className="px-3 py-1 text-sm text-gray-400 hover:text-gray-200 disabled:opacity-30 disabled:cursor-not-allowed bg-gray-800 rounded hover:bg-gray-700 transition-colors">
            Next →
          </button>
        </div>
      )}
    </>
  )
}

export function PdfModal() {
  const openCitation = useAppStore((s) => s.openCitation)
  const setOpenCitation = useAppStore((s) => s.setOpenCitation)

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpenCitation(null)
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [setOpenCitation])

  if (!openCitation) return null

  const isJsonSource = !openCitation.pdfPath
  const subtitle = isJsonSource
    ? openCitation.refId
    : `Page ${openCitation.pageNumber}`

  return (
    <div
      className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={(e) => e.target === e.currentTarget && setOpenCitation(null)}
    >
      <div className="bg-gray-900 rounded-2xl border border-gray-700 w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
          <div>
            <p className="text-sm font-medium text-gray-200">{openCitation.sourceLabel}</p>
            <p className="text-xs text-gray-500">{subtitle}</p>
          </div>
          <button
            type="button"
            onClick={() => setOpenCitation(null)}
            className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-200 hover:bg-gray-700 transition-colors"
          >
            ✕
          </button>
        </div>

        {isJsonSource ? <TextCitationPanel /> : <PdfViewerPanel />}
      </div>
    </div>
  )
}
