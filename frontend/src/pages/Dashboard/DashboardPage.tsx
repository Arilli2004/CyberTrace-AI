import { FolderSearch, Upload, Clock, AlertTriangle, Shield, Activity, Bot, RefreshCw } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { casesApi } from '@/api/client'
import { useAuthStore } from '@/store/authStore'
import { useNavigate } from 'react-router-dom'

export default function DashboardPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()

  // Fetch Live Dashboard Database Statistics
  const { data: statsData, isLoading: isStatsLoading, refetch: refetchStats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => casesApi.getDashboardStats(),
    select: (res) => res.data,
  })

  // Fetch Live Recent Cases from DB
  const { data: casesData, isLoading: isCasesLoading } = useQuery({
    queryKey: ['cases-dashboard'],
    queryFn: () => casesApi.list({ limit: 5 }),
    select: (res) => res.data,
  })

  const statCards = [
    {
      icon: FolderSearch,
      label: 'Total Cases',
      value: isStatsLoading ? '...' : String(statsData?.total_cases ?? 0),
      color: '#3b82f6',
      bg: 'rgba(59,130,246,0.1)',
      trend: 'Live in Database',
    },
    {
      icon: Upload,
      label: 'Evidence Files',
      value: isStatsLoading ? '...' : String(statsData?.total_evidence ?? 0),
      color: '#06b6d4',
      bg: 'rgba(6,182,212,0.1)',
      trend: 'Uploaded Artifacts',
    },
    {
      icon: AlertTriangle,
      label: 'Active Threat Alerts',
      value: isStatsLoading ? '...' : String(statsData?.active_alerts ?? 0),
      color: '#f43f5e',
      bg: 'rgba(244,63,94,0.1)',
      trend: 'High / Critical Severity',
    },
    {
      icon: Clock,
      label: 'Timelines Built',
      value: isStatsLoading ? '...' : String(statsData?.timelines_built ?? 0),
      color: '#10b981',
      bg: 'rgba(16,185,129,0.1)',
      trend: 'Parsed Evidence Logs',
    },
  ]

  const recentCases = casesData?.cases || []
  const activityFeed = statsData?.activity_feed || []

  return (
    <div className="animate-slide-in">
      {/* Header */}
      <div className="page-header" style={{ flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 className="page-title">
            Welcome back, {user?.name?.split(' ')[0] || 'Investigator'} 👋
          </h1>
          <p className="page-subtitle">CyberTrace AI — Live Digital Forensics & Database Overview</p>
        </div>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button className="btn btn-secondary btn-sm" onClick={() => refetchStats()}>
            <RefreshCw size={14} /> Refresh DB Metrics
          </button>
          <button className="btn btn-secondary btn-sm" onClick={() => navigate('/investigation')}>
            <Activity size={16} /> Investigation Workbench
          </button>
          <button className="btn btn-primary btn-sm" onClick={() => navigate('/cases')}>
            <FolderSearch size={16} /> Manage Cases
          </button>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid-4" style={{ marginBottom: '24px' }}>
        {statCards.map(({ icon: Icon, label, value, color, bg, trend }) => (
          <div key={label} className="stat-card">
            <div className="stat-icon" style={{ background: bg }}>
              <Icon size={22} color={color} />
            </div>
            <div className="stat-info">
              <div className="stat-value">{value}</div>
              <div className="stat-label">{label}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '2px' }}>{trend}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Main Content */}
      <div className="grid-2">
        {/* Recent Cases */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3 style={{ margin: 0 }}>Active Database Cases ({recentCases.length})</h3>
            <button onClick={() => navigate('/cases')} className="btn btn-ghost btn-sm">View All →</button>
          </div>

          {isCasesLoading ? (
            <div style={{ padding: '20px', textAlign: 'center', color: 'var(--color-text-muted)' }}>Loading cases...</div>
          ) : recentCases.length === 0 ? (
            <div style={{ padding: '30px', textAlign: 'center', color: 'var(--color-text-muted)', border: '1px dashed var(--color-border)', borderRadius: 'var(--radius-md)' }}>
              No active cases found in database. Click "Manage Cases" to create one.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {recentCases.map((c: any) => (
                <div
                  key={c.id}
                  onClick={() => navigate('/cases')}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '12px 16px',
                    background: 'var(--color-bg-elevated)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--color-border)',
                    transition: 'all 0.2s ease',
                    cursor: 'pointer',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--color-accent)')}
                  onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--color-border)')}
                >
                  <div style={{
                    width: '40px', height: '40px',
                    background: 'rgba(59,130,246,0.1)',
                    borderRadius: 'var(--radius-sm)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    flexShrink: 0,
                  }}>
                    <FolderSearch size={18} color="var(--color-accent)" />
                  </div>
                  <div style={{ flex: 1, overflow: 'hidden' }}>
                    <div style={{ fontWeight: 600, fontSize: '0.875rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      Case #{c.id}: {c.title}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                      Status: {c.status || 'analysis'} • Priority: {c.priority || 'high'}
                    </div>
                  </div>
                  <span className={`badge badge-${c.priority === 'critical' ? 'critical' : c.priority === 'high' ? 'high' : 'medium'}`}>
                    {c.priority ? c.priority.toUpperCase() : 'HIGH'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Audit Log & Activity Feed from DB */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3 style={{ margin: 0 }}>Live Chain of Custody Audit Log</h3>
            <Shield size={18} color="var(--color-cyan)" />
          </div>

          {activityFeed.length === 0 ? (
            <div style={{ padding: '30px', textAlign: 'center', color: 'var(--color-text-muted)', border: '1px dashed var(--color-border)', borderRadius: 'var(--radius-md)' }}>
              No audit activities logged yet in database. Upload or parse evidence files to generate custody logs.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {activityFeed.map((item: any) => (
                <div key={item.id} className="timeline-item">
                  <div className="timeline-dot" style={{
                    background: item.severity === 'critical' ? 'rgba(239,68,68,0.15)' :
                      item.severity === 'high' ? 'rgba(249,115,22,0.15)' :
                        'rgba(59,130,246,0.15)',
                  }}>
                    <div style={{
                      width: '8px', height: '8px', borderRadius: '50%',
                      background: item.severity === 'critical' ? 'var(--color-critical)' :
                        item.severity === 'high' ? '#f97316' : 'var(--color-accent)',
                    }} />
                  </div>
                  <div style={{ flex: 1, paddingTop: '4px' }}>
                    <div style={{ fontSize: '0.84rem', color: 'var(--color-text-primary)', fontWeight: 600 }}>
                      {item.action}
                    </div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>{item.time}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* AI Insight Banner */}
      <div style={{
        marginTop: '24px',
        padding: '20px 24px',
        background: 'linear-gradient(135deg, rgba(59,130,246,0.1) 0%, rgba(139,92,246,0.08) 100%)',
        border: '1px solid rgba(59,130,246,0.2)',
        borderRadius: 'var(--radius-lg)',
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
        flexWrap: 'wrap',
      }}>
        <div style={{
          width: '44px', height: '44px',
          background: 'var(--gradient-accent)',
          borderRadius: 'var(--radius-md)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0,
        }}>
          <Bot size={22} color="white" />
        </div>
        <div style={{ flex: 1, minWidth: '240px' }}>
          <div style={{ fontWeight: 700, marginBottom: '4px' }}>Gemma AI Investigation Assistant Active</div>
          <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
            Ask Gemma AI about active cases, evidence logs, threat severity, or generate formal investigation reports.
          </div>
        </div>
        <button className="btn btn-primary btn-sm" onClick={() => navigate('/ai-assistant')}>
          Launch AI Assistant →
        </button>
      </div>
    </div>
  )
}
