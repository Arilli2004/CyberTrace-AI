import { FolderSearch, Upload, Clock, AlertTriangle, Shield, Activity, Bot } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { casesApi } from '@/api/client'
import { useAuthStore } from '@/store/authStore'

const STAT_CARDS = [
  { icon: FolderSearch, label: 'Total Cases', value: '12', color: '#3b82f6', bg: 'rgba(59,130,246,0.1)', trend: '+3 this week' },
  { icon: Upload, label: 'Evidence Files', value: '47', color: '#06b6d4', bg: 'rgba(6,182,212,0.1)', trend: '+8 today' },
  { icon: AlertTriangle, label: 'Active Alerts', value: '23', color: '#f43f5e', bg: 'rgba(244,63,94,0.1)', trend: '5 critical' },
  { icon: Clock, label: 'Timelines Built', value: '9', color: '#10b981', bg: 'rgba(16,185,129,0.1)', trend: '100% accuracy' },
]

const RECENT_ACTIVITY = [
  { time: '2 min ago', action: 'Evidence uploaded to Case #1042', type: 'upload', severity: 'info' },
  { time: '15 min ago', action: 'Critical alert: Log clearing detected', type: 'alert', severity: 'critical' },
  { time: '1 hr ago', action: 'AI report generated for Ransomware Case', type: 'report', severity: 'info' },
  { time: '2 hr ago', action: 'New case created: Data Exfiltration - Finance', type: 'case', severity: 'medium' },
  { time: '3 hr ago', action: 'Failed login brute force detected (5 attempts)', type: 'alert', severity: 'high' },
]

export default function DashboardPage() {
  const { user } = useAuthStore()

  const { data: casesData } = useQuery({
    queryKey: ['cases'],
    queryFn: () => casesApi.list({ limit: 5 }),
    select: (res) => res.data,
  })

  return (
    <div className="animate-slide-in">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            Welcome back, {user?.name?.split(' ')[0] || 'Investigator'} 👋
          </h1>
          <p className="page-subtitle">CyberTrace AI — Digital Forensics Dashboard</p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn btn-secondary btn-sm">
            <Activity size={16} /> View Alerts
          </button>
          <button className="btn btn-primary btn-sm">
            <FolderSearch size={16} /> New Case
          </button>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid-4" style={{ marginBottom: '24px' }}>
        {STAT_CARDS.map(({ icon: Icon, label, value, color, bg, trend }) => (
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
            <h3 style={{ margin: 0 }}>Recent Cases</h3>
            <a href="/cases" className="btn btn-ghost btn-sm">View All →</a>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {(casesData?.cases || MOCK_CASES).map((c: any, i: number) => (
              <div key={i} style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '12px',
                background: 'var(--color-bg-elevated)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--color-border)',
                transition: 'border-color 0.2s',
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
                    {c.title || `Case #${1040 + i}`}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                    {c.status || 'analysis'} • {c.priority || 'high'} priority
                  </div>
                </div>
                <span className={`badge badge-${c.priority === 'critical' ? 'critical' : c.priority === 'high' ? 'high' : 'medium'}`}>
                  {c.priority || 'high'}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Activity Feed */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3 style={{ margin: 0 }}>Recent Activity</h3>
            <Shield size={18} color="var(--color-text-muted)" />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
            {RECENT_ACTIVITY.map((item, i) => (
              <div key={i} className="timeline-item">
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
                <div style={{ flex: 1, paddingTop: '6px' }}>
                  <div style={{ fontSize: '0.875rem', color: 'var(--color-text-primary)', marginBottom: '2px' }}>
                    {item.action}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{item.time}</div>
                </div>
              </div>
            ))}
          </div>
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
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 600, marginBottom: '4px' }}>AI Investigation Assistant Ready</div>
          <div style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
            3 active cases have new evidence. Click to start AI-assisted investigation and generate reports.
          </div>
        </div>
        <button className="btn btn-primary btn-sm">Start Analysis →</button>
      </div>
    </div>
  )
}

const MOCK_CASES = [
  { title: 'Ransomware Investigation - ACME Corp', status: 'analysis', priority: 'critical' },
  { title: 'Data Exfiltration - Finance Dept', status: 'evidence_uploaded', priority: 'high' },
  { title: 'Unauthorized Access - HR Systems', status: 'new', priority: 'medium' },
]
