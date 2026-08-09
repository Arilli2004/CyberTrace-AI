import { useState } from 'react'
import { Clock, Filter, AlertTriangle } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { timelineApi, casesApi } from '@/api/client'

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'var(--color-critical)',
  high: '#f97316',
  medium: '#eab308',
  low: 'var(--color-emerald)',
}

export default function TimelinePage() {
  const [selectedCase, setSelectedCase] = useState<number | null>(null)
  const [filter, setFilter] = useState('')

  const { data: casesData } = useQuery({
    queryKey: ['cases'],
    queryFn: () => casesApi.list({ limit: 50 }),
    select: (res) => res.data?.cases || [],
  })

  const { data: timeline, isLoading } = useQuery({
    queryKey: ['timeline', selectedCase],
    queryFn: () => timelineApi.get(selectedCase!, { limit: 200 }),
    enabled: !!selectedCase,
    select: (res) => res.data?.events || [],
  })

  const events = timeline?.filter((e: any) => {
    if (!filter) return true
    return (e.event_type || '').toLowerCase().includes(filter.toLowerCase()) ||
      (e.user || '').toLowerCase().includes(filter.toLowerCase()) ||
      (e.host || '').toLowerCase().includes(filter.toLowerCase())
  }) || []

  return (
    <div className="animate-slide-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Event Timeline</h1>
          <p className="page-subtitle">Chronological reconstruction of digital events</p>
        </div>
      </div>

      {/* Controls */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', flexWrap: 'wrap' }}>
        <select id="timeline-case-select" className="input" value={selectedCase || ''} onChange={(e) => setSelectedCase(Number(e.target.value) || null)} style={{ maxWidth: '300px' }}>
          <option value="">— Select a case —</option>
          {casesData?.map((c: any) => <option key={c.id} value={c.id}>{c.title}</option>)}
        </select>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'var(--color-bg-elevated)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: '8px 14px', flex: 1, maxWidth: '300px' }}>
          <Filter size={16} color="var(--color-text-muted)" />
          <input style={{ background: 'transparent', border: 'none', outline: 'none', color: 'var(--color-text-primary)', flex: 1, fontSize: '0.875rem' }} placeholder="Filter by user, host, event..." value={filter} onChange={(e) => setFilter(e.target.value)} />
        </div>
      </div>

      {!selectedCase ? (
        <div className="empty-state">
          <Clock size={48} className="empty-state-icon" />
          <h3>Select a Case</h3>
          <p>Choose an investigation case to view its event timeline</p>
        </div>
      ) : isLoading ? (
        <div className="empty-state"><div className="spinner" /></div>
      ) : events.length === 0 ? (
        <div className="empty-state">
          <AlertTriangle size={48} className="empty-state-icon" />
          <h3>No Events Found</h3>
          <p>Upload and parse evidence files to generate the timeline</p>
        </div>
      ) : (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px', alignItems: 'center' }}>
            <h3 style={{ margin: 0 }}>{events.length} Events</h3>
            <span style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>Chronological order</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {events.map((event: any, i: number) => (
              <div key={i} className="timeline-item">
                <div className="timeline-dot" style={{ background: `${SEVERITY_COLORS[event.severity] || 'var(--color-accent)'}20` }}>
                  <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: SEVERITY_COLORS[event.severity] || 'var(--color-accent)' }} />
                </div>

                <div style={{ flex: 1, background: 'var(--color-bg-elevated)', borderRadius: 'var(--radius-md)', padding: '14px', border: '1px solid var(--color-border)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{event.event_type || 'Unknown Event'}</span>
                      <span className={`badge badge-${event.severity}`}>{event.severity}</span>
                      {event.is_suspicious && <span className="badge badge-critical">⚠ Suspicious</span>}
                    </div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
                      {event.timestamp ? new Date(event.timestamp).toLocaleString() : '—'}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', margin: 0, marginBottom: '8px' }}>
                    {event.description}
                  </p>
                  <div style={{ display: 'flex', gap: '16px', fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                    {event.user && <span>👤 {event.user}</span>}
                    {event.host && <span>🖥 {event.host}</span>}
                    {event.ip_address && <span>🌐 {event.ip_address}</span>}
                    {event.source && <span>📁 {event.source}</span>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
