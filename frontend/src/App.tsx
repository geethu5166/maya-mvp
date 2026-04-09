import { useState, useEffect } from 'react'
import { useAuth } from './hooks/useAuth'
import Dashboard from './pages/Dashboard'
import Incidents from './pages/Incidents'
import Login from './pages/Login'
import Header from './components/Header'
import Sidebar from './components/Sidebar'

function App() {
  const { user, logout } = useAuth()
  const [currentPage, setCurrentPage] = useState<'dashboard' | 'incidents' | 'settings'>('dashboard')
  const [darkMode, setDarkMode] = useState(() => {
    const stored = localStorage.getItem('darkMode')
    return stored ? JSON.parse(stored) : window.matchMedia('(prefers-color-scheme: dark)').matches
  })

  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(darkMode))
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [darkMode])

  if (!user) {
    return <Login />
  }

  return (
    <div className="flex h-screen bg-white dark:bg-slate-950">
      <Sidebar currentPage={currentPage} setCurrentPage={setCurrentPage} />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header 
          darkMode={darkMode} 
          onToggleDarkMode={() => setDarkMode(!darkMode)}
          onLogout={logout}
          user={user}
        />
        
        <main className="flex-1 overflow-auto">
          {currentPage === 'dashboard' && <Dashboard />}
          {currentPage === 'incidents' && <Incidents />}
        </main>
      </div>
    </div>
  )
}

export default App
