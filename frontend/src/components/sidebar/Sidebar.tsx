import { Link, useLocation } from 'react-router-dom'
import { useAppStore } from '../../store/appStore'
import type { SourceType } from '../../types'

const SOURCE_OPTIONS: { type: SourceType; label: string; emoji: string }[] = [
  { type: 'quran', label: 'Holy Quran', emoji: '📗' },
  { type: 'bukhari', label: 'Sahih Bukhari', emoji: '📘' },
  { type: 'muslim', label: 'Sahih Muslim', emoji: '📙' },
]

export function Sidebar() {
  const activeSources = useAppStore((s) => s.activeSources)
  const sources = useAppStore((s) => s.sources)
  const toggleSource = useAppStore((s) => s.toggleSource)
  const location = useLocation()

  const ingestedTypes = new Set(
    sources.filter((s) => s.ingested).map((s) => s.source_type)
  )

  return (
    <aside className="w-56 flex-shrink-0 bg-gray-900 border-r border-gray-700 flex flex-col">
      {/* Logo */}
      <div className="px-4 py-5 border-b border-gray-700">
        <h1 className="text-base font-bold text-gray-100">🕌 Hadeeth RAG</h1>
        <p className="text-xs text-gray-500 mt-0.5">Islamic Text Search</p>
      </div>

      {/* Source selection */}
      <div className="px-4 py-4 flex-1">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Sources</p>
        <div className="space-y-2">
          {SOURCE_OPTIONS.map(({ type, label, emoji }) => {
            const isIngested = ingestedTypes.has(type)
            const isActive = activeSources.includes(type)
            return (
              <label
                key={type}
                className={`flex items-center gap-2.5 px-2 py-2 rounded-lg cursor-pointer transition-colors ${
                  isActive ? 'bg-gray-800' : 'hover:bg-gray-800/50'
                }`}
              >
                <input
                  type="checkbox"
                  checked={isActive}
                  onChange={() => toggleSource(type)}
                  className="w-4 h-4 accent-indigo-500"
                />
                <span className="text-sm">{emoji}</span>
                <span className={`text-sm flex-1 ${isActive ? 'text-gray-100' : 'text-gray-400'}`}>
                  {label}
                </span>
                {isIngested ? (
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" title="Indexed" />
                ) : (
                  <span className="w-1.5 h-1.5 rounded-full bg-gray-600" title="Not indexed" />
                )}
              </label>
            )
          })}
        </div>
      </div>

      {/* Nav */}
      <div className="px-4 py-4 border-t border-gray-700 space-y-1">
        <Link
          to="/"
          className={`flex items-center gap-2 px-2 py-1.5 rounded-lg text-sm transition-colors ${
            location.pathname === '/'
              ? 'bg-indigo-600 text-white'
              : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
          }`}
        >
          <span>💬</span> Chat
        </Link>
        <Link
          to="/settings"
          className={`flex items-center gap-2 px-2 py-1.5 rounded-lg text-sm transition-colors ${
            location.pathname === '/settings'
              ? 'bg-indigo-600 text-white'
              : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
          }`}
        >
          <span>⚙️</span> Settings
        </Link>
      </div>
    </aside>
  )
}
