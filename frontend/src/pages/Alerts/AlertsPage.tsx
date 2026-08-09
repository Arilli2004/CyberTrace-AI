import { Bell, AlertTriangle, CheckCircle, XCircle } from 'lucide-react'

const MOCK_ALERTS = [
  { id: 1, title: 'Brute Force Attack Detected', desc: '12 failed login attempts in 5 minutes from 192.168.1.105', severity: 'critical', time: '2 min ago', rule: 'brute_force_login', acknowledged: false },
  { id: 2, title: 'Audit Log Cleared', desc: 'Windows Security Event Log cleared by user Administrator', severity: 'critical', time: '45 min ago', rule: 'log_cleared', acknowledged: false },
  { id: 3, title: 'New Service Installed', desc: 'Service "svchost32" installed from C:\\Temp — possible persistence', severity: 'high', time: '1 hr ago', rule: 'new_service_installed', acknowledged: false },
  { id: 4, title: 'Privilege Escalation', desc: 'Special privileges assigned to user jdoe after logon', severity: 'high', time: '2 hr ago', rule: 'privilege_escalation', acknowledged: true },
  { id: 5, title: 'New User Account Created', desc: 'Account "backdoor_user" created by Administrator', severity: 'medium', time: '3 hr ago', rule: 'account_created', acknowledged: false },
  { id: 6, title: 'Account Locked Out', desc: 'User account "jane.doe" locked after 5 failed attempts', severity: 'medium', time: '4 hr ago', rule: 'account_locked', acknowledged: true },
]

const SEVERITY_ICONS: Record<string, React.ReactNode> = {
  critical: <XCircle size={18} color="var(--color-critical)" />,
  high: <AlertTriangle size={18} color="#f97316" />,
  medium: <Bell size={18} color="#eab308" />,
  low: <CheckCircle size={18} color="var(--color-emerald)" />,
}

export default function AlertsPage() {
  return (
    <div className="animate-slide-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Security Alerts</h1>
          <p className="page-subtitle">Suspicious activity detections across all cases</p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <span className="badge badge-critical">2 Critical</span>
          <span className="badge badge-high">1 High</span>
          <span className="badge badge-medium">2 Medium</span>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {MOCK_ALERTS.map((alert) => (
          <div key={alert.id} className="card card-sm" style={{
            display: 'flex', alignItems: 'flex-start', gap: '16px',
            opacity: alert.acknowledged ? 0.6 : 1,
            borderLeft: `3px solid ${alert.severity === 'critical' ? 'var(--color-critical)' : alert.severity === 'high' ? '#f97316' : alert.severity === 'medium' ? '#eab308' : 'var(--color-emerald)'}`,
          }}>
            <div style={{ marginTop: '2px', flexShrink: 0 }}>{SEVERITY_ICONS[alert.severity]}</div>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{alert.title}</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{alert.time}</span>
              </div>
              <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', margin: '0 0 8px' }}>{alert.desc}</p>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <span className={`badge badge-${alert.severity}`}>{alert.severity}</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>Rule: {alert.rule}</span>
                {alert.acknowledged && <span style={{ fontSize: '0.75rem', color: 'var(--color-emerald)' }}>✓ Acknowledged</span>}
              </div>
            </div>
            {!alert.acknowledged && (
              <button className="btn btn-ghost btn-sm" style={{ flexShrink: 0 }}>
                <CheckCircle size={14} /> Acknowledge
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
