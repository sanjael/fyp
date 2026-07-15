import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { LayoutDashboard, MessageSquareText, Files, Settings, LogOut, ShieldAlert } from 'lucide-react';
import '../App.css';

const SidebarLayout = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <ShieldAlert size={28} color="var(--primary)" />
            RAGGuard-TR
          </div>
        </div>
        
        <nav className="nav-links">
          <NavLink to="/" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"} end>
            <LayoutDashboard size={20} />
            Dashboard
          </NavLink>
          <NavLink to="/query" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
            <MessageSquareText size={20} />
            Query Engine
          </NavLink>
          <NavLink to="/documents" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
            <Files size={20} />
            Documents
          </NavLink>
          <NavLink to="/settings" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
            <Settings size={20} />
            Settings
          </NavLink>
        </nav>

        <div className="sidebar-footer">
          <button 
            onClick={handleLogout}
            style={{ 
              width: '100%', 
              display: 'flex', 
              alignItems: 'center', 
              gap: '10px',
              padding: '12px',
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              fontWeight: 500,
              fontFamily: 'var(--font-body)',
              transition: 'color 0.2s ease'
            }}
            onMouseOver={(e) => e.currentTarget.style.color = 'var(--accent-red)'}
            onMouseOut={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
          >
            <LogOut size={20} />
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        <header className="top-header">
          <h2 className="page-title">Temporal-Aware Context Engine</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: 'var(--accent-green)', boxShadow: '0 0 10px var(--accent-green)' }}></div>
            <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>System Online</span>
            <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'linear-gradient(135deg, var(--primary), var(--secondary))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', marginLeft: '10px' }}>
              A
            </div>
          </div>
        </header>
        
        <div className="page-container animate-fade-in">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default SidebarLayout;
