import { useEffect } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { Sidebar } from './components/sidebar/Sidebar'
import { ChatWindow } from './components/chat/ChatWindow'
import { PdfModal } from './components/pdf/PdfModal'
import { SettingsPage } from './components/settings/SettingsPage'
import { useAppStore } from './store/appStore'
import { fetchSources } from './api/sources'

function App() {
  const setSources = useAppStore((s) => s.setSources)

  useEffect(() => {
    fetchSources()
      .then(setSources)
      .catch(() => {}) // backend may not be running yet
  }, [setSources])

  return (
    <BrowserRouter>
      <div className="flex h-full">
        <Sidebar />
        <main className="flex-1 flex flex-col min-w-0 bg-gray-950">
          <Routes>
            <Route path="/" element={<ChatWindow />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
      <PdfModal />
    </BrowserRouter>
  )
}

export default App
