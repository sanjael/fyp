import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Home from './pages/Home'
import Upload from './pages/Upload'
import Query from './pages/Query'
import Dashboard from './pages/Dashboard'
import { getHealth } from './api'

function Sidebar({ health }) {
  const navItems = [
    { to: '/', icon: '🏠', label: 'Home', exact: true },
    { to: '/upload', icon: '📄', label: 'Upload Docs' },
    { to: '/query', icon: '💬', label: 'Query' },
    { to: '/dashboard', icon: '📊', label: 'Dashboard' },
  ]

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-mark">
          <div className="logo-icon">🛡️</div>
          <div className="logo-text"><span>RAG</span>Shield</div>
        </div>
        <div className="logo-tagline">Hallucination Prevention</div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section-label">Navigation</div>
        {navItems.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.exact}
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-bottom">
        <div className="status-indicator">
          <div className={`status-dot ${health?.status === 'healthy' ? '' : 'offline'}`} />
          <span>{health?.status === 'healthy' ? 'Backend Online' : 'Backend Offline'}</span>
        </div>
        {health && (
          <div className="mt-1 text-xs text-muted">
            {health.total_chunks || 0} chunks indexed
          </div>
        )}
      </div>
    </aside>
  )
}

export default function App() {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await getHealth()
        setHealth(res.data)
      } catch {
        setHealth({ status: 'offline' })
      }
    }
    checkHealth()
    const interval = setInterval(checkHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar health={health} />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home health={health} />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/query" element={<Query />} />
            <Route path="/dashboard" element={<Dashboard />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
