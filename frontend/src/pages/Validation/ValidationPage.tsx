import { useState } from 'react'
import { ShieldCheck, AlertTriangle, CheckCircle, RefreshCw, Cpu, Award } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { cspApi, casesApi } from '@/api/client'
import toast from 'react-hot-toast'

export default function ValidationPage() {
  const [selectedCase, setSelectedCase] = useState<number | null>(null)
  const queryClient = useQueryClient()

  const { data: casesData } = useQuery({
    queryKey: ['cases'],
    queryFn: () => casesApi.list({ limit: 100 }),
    select: (res) => res.data?.cases || [],
  })

  const activeCaseId = selectedCase || (casesData && casesData.length > 0 ? casesData[0].id : null)

  const { data: resultsData, isLoading } = useQuery({
    queryKey: ['csp-results', activeCaseId],
    queryFn: () => cspApi.getResults(activeCaseId!),
    enabled: !!activeCaseId,
    select: (res) => res.data,
  })

  const validateMutation = useMutation({
    mutationFn: (caseId: number) => cspApi.validate(caseId),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['csp-results', activeCaseId] })
      toast.success(`CSP Backtracking completed! Validation Score: ${res.data.validation_score}%`)
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || 'CSP Validation failed'),
  })

  const summary = resultsData?.result || {
    validation_status: 'UNVALIDATED',
    validation_score: 0.0,
    violations_count: 0,
    resolved_count: 0,
    confidence_score: 0.0,
  }

  const violations = resultsData?.violations || []

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2>Enterprise CSP Validation Engine</h2>
          <p style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
            Constraint Satisfaction Problem & Backtracking solver for Knowledge Graph logical consistency
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <select
            className="btn btn-secondary"
            value={activeCaseId || ''}
            onChange={(e) => setSelectedCase(Number(e.target.value))}
          >
            {casesData?.map((c: any) => (
              <option key={c.id} value={c.id}>Case #{c.id} — {c.title}</option>
            ))}
          </select>

          <button
            className="btn btn-primary"
            onClick={() => activeCaseId && validateMutation.mutate(activeCaseId)}
            disabled={!activeCaseId || validateMutation.isPending}
          >
            <RefreshCw size={16} className={validateMutation.isPending ? 'spinner' : ''} />
            {validateMutation.isPending ? 'Running CSP Solver...' : 'Run CSP Backtracking'}
          </button>
        </div>
      </div>

      {/* Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
        <div className="card" style={{ padding: '16px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: '4px' }}>VALIDATION SCORE</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Award size={20} color="var(--color-accent)" /> {summary.validation_score}%
          </div>
        </div>

        <div className="card" style={{ padding: '16px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: '4px' }}>VALIDATION STATUS</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldCheck size={20} color={summary.validation_status === 'PASSED' ? '#10b981' : summary.validation_status === 'PARTIAL' ? '#f59e0b' : '#ef4444'} />
            <span className={`badge ${summary.validation_status === 'PASSED' ? 'badge-low' : summary.validation_status === 'PARTIAL' ? 'badge-medium' : 'badge-critical'}`}>
              {summary.validation_status}
            </span>
          </div>
        </div>

        <div className="card" style={{ padding: '16px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: '4px' }}>BACKTRACK RESOLVED</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCircle size={20} color="#10b981" /> {summary.resolved_count}
          </div>
        </div>

        <div className="card" style={{ padding: '16px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: '4px' }}>CONSTRAINT VIOLATIONS</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={20} color="#ef4444" /> {summary.violations_count}
          </div>
        </div>
      </div>

      {/* Main Results Container */}
      <div className="card" style={{ minHeight: '400px' }}>
        <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Cpu size={18} /> Evaluated Forensic Constraints & Backtracking Audit Trail
        </h3>

        {isLoading ? (
          <div className="empty-state"><div className="spinner" /></div>
        ) : violations.length === 0 ? (
          <div className="empty-state">
            <ShieldCheck size={40} className="empty-state-icon" style={{ color: '#10b981' }} />
            <h3>Graph Consistency Validated</h3>
            <p>Knowledge Graph satisfies all 5 standard forensic rule sets. Ready for UCS & A* Search reasoning algorithms.</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {violations.map((v: any) => (
              <div
                key={v.id}
                style={{
                  padding: '16px',
                  background: 'var(--color-bg-elevated)',
                  border: `1px solid ${v.status === 'VIOLATION' ? 'var(--color-severity-critical)' : 'var(--color-severity-low)'}`,
                  borderRadius: 'var(--radius-md)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span className={`badge ${v.status === 'VIOLATION' ? 'badge-critical' : 'badge-low'}`}>
                    {v.status}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                    Confidence: {(v.confidence * 100).toFixed(0)}%
                  </span>
                </div>

                <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{v.violation_reason}</div>
                {v.resolution_details && (
                  <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', background: 'var(--color-bg-surface)', padding: '8px 12px', borderRadius: 'var(--radius-sm)' }}>
                    💡 <strong>Backtracking Resolution:</strong> {v.resolution_details}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
