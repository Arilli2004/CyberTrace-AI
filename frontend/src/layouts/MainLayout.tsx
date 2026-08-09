import { NavLink, useNavigate } from 'react-router-dom'
import { Outlet } from 'react-router-dom'
import {
  LayoutDashboard, FolderSearch, Upload, Clock, Bell, Network, ShieldCheck,
  FileText, Bot, Settings, LogOut, Shield, Search, User, Zap
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import toast from 'react-hot-toast'

const NAV_ITEMS = [
  { icon: LayoutDashboard, label: 'Dashboard', to: '/dashboard' },
  { icon: Zap, label: 'Investigation Workbench', to: '/investigation' },
  { icon: FolderSearch, label: 'Cases', to: '/cases' },
  { icon: Upload, label: 'Evidence', to: '/evidence' },
  { icon: Network, label: 'Knowledge Graph', to: '/graph' },
  { icon: ShieldCheck, label: 'CSP Validation', to: '/validation' },
  { icon: Clock, label: 'Timeline', to: '/timeline/1' },
  { icon: Bell, label: 'Alerts', to: '/alerts', badge: 3 },
  { icon: FileText, label: 'Reports', to: '/reports' },
  { icon: Bot, label: 'AI Assistant', to: '/ai-assistant' },
  { icon: Settings, label: 'Settings', to: '/settings' },
]

export default function MainLayout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    toast.success('Logged out successfully')
    navigate('/login')
  }

  return (
    <div className="app-layout">
      {/* ─── Sidebar ── */}
      <aside className="sidebar">
        {/* Logo */}
        <div className="sidebar-logo">
          <div className="logo-icon">
            <Shield size={18} color="white" />
          </div>
          <div>
            <div className="logo-text">CyberTrace</div>
            <div className="logo-sub">AI Forensics Platform</div>
          </div>
        </div>

        {/* Nav */}
        <nav className="nav-section" style={{ flex: 1 }}>
          <div className="nav-section-title">Navigation</div>
          {NAV_ITEMS.map(({ icon: Icon, label, to, badge }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            >
              <Icon size={18} />
              {label}
              {badge && <span className="nav-badge">{badge}</span>}
            </NavLink>
          ))}
        </nav>

        {/* User Footer */}
        <div style={{
          padding: '16px',
          borderTop: '1px solid var(--color-border)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <div style={{
            width: '36px', height: '36px',
            background: 'var(--gradient-accent)',
            borderRadius: '50%',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0
          }}>
            <User size={16} color="white" />
          </div>
          <div style={{ flex: 1, overflow: 'hidden' }}>
            <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {user?.name || 'Investigator'}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{user?.role}</div>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={handleLogout} title="Logout">
            <LogOut size={16} />
          </button>
        </div>
      </aside>

      {/* ─── Main Content ── */}
      <div className="main-content">
        {/* Topbar */}
        <header className="topbar">
          <div style={{ flex: 1 }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              background: 'var(--color-bg-elevated)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              padding: '8px 14px',
              maxWidth: '400px',
            }}>
              <Search size={16} color="var(--color-text-muted)" />
              <input
                style={{ background: 'transparent', border: 'none', outline: 'none', color: 'var(--color-text-primary)', flex: 1, fontSize: '0.875rem' }}
                placeholder="Search cases, evidence, events..."
              />
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {/* Status indicator */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '999px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--color-emerald)', animation: 'pulse-dot 2s infinite' }} />
              <span style={{ fontSize: '0.75rem', color: 'var(--color-emerald)' }}>System Online</span>
            </div>

            <button className="btn btn-ghost btn-sm" style={{ position: 'relative' }}>
              <Bell size={18} />
              <span style={{ position: 'absolute', top: '4px', right: '4px', width: '8px', height: '8px', background: 'var(--color-rose)', borderRadius: '50%' }} />
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="page-content animate-fade-in">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
