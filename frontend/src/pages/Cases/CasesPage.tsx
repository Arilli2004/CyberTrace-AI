import { useState } from 'react'
import { FolderSearch, Plus, Search, Trash2, ChevronRight } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { casesApi } from '@/api/client'
import toast from 'react-hot-toast'

const STATUS_COLORS: Record<string, string> = {
  new: 'badge-info',
  evidence_uploaded: 'badge-medium',
  parsing: 'badge-medium',
  analysis: 'badge-high',
  completed: 'badge-low',
  archived: 'badge-info',
}

export default function CasesPage() {
  const [showCreate, setShowCreate] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState('medium')
  const [search, setSearch] = useState('')
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['cases'],
    queryFn: () => casesApi.list({ limit: 50 }),
    select: (res) => res.data,
  })

  const createMutation = useMutation({
    mutationFn: () => casesApi.create({ title, description, priority }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cases'] })
      toast.success('Case created successfully')
      setShowCreate(false)
      setTitle('')
      setDescription('')
    },
    onError: () => toast.error('Failed to create case'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => casesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cases'] })
      toast.success('Case deleted')
    },
  })

  const cases = data?.cases?.filter((c: any) =>
    c.title.toLowerCase().includes(search.toLowerCase())
  ) || []

  return (
    <div className="animate-slide-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Investigation Cases</h1>
          <p className="page-subtitle">Manage all forensic investigation cases</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
          <Plus size={18} /> New Case
        </button>
      </div>

      {/* Search */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'var(--color-bg-elevated)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: '10px 14px', marginBottom: '20px' }}>
        <Search size={16} color="var(--color-text-muted)" />
        <input
          style={{ background: 'transparent', border: 'none', outline: 'none', color: 'var(--color-text-primary)', flex: 1 }}
          placeholder="Search cases..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex',
          alignItems: 'center', justifyContent: 'center', zIndex: 1000,
        }}>
          <div className="card animate-slide-in" style={{ width: '500px', maxWidth: '90vw' }}>
            <h3 style={{ marginBottom: '20px' }}>Create New Case</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div className="input-group">
                <label className="input-label">Case Title *</label>
                <input id="case-title" className="input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Ransomware Attack - Server Farm" />
              </div>
              <div className="input-group">
                <label className="input-label">Description</label>
                <textarea id="case-description" className="input" rows={3} value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Describe the incident..." style={{ resize: 'vertical' }} />
              </div>
              <div className="input-group">
                <label className="input-label">Priority</label>
                <select id="case-priority" className="input" value={priority} onChange={(e) => setPriority(e.target.value)}>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
              <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                <button className="btn btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
                <button className="btn btn-primary" onClick={() => createMutation.mutate()} disabled={!title || createMutation.isPending}>
                  {createMutation.isPending ? 'Creating...' : 'Create Case'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Cases Table */}
      {isLoading ? (
        <div className="empty-state"><div className="spinner" /></div>
      ) : cases.length === 0 ? (
        <div className="empty-state">
          <FolderSearch size={48} className="empty-state-icon" />
          <h3>No Cases Found</h3>
          <p>Create your first investigation case to get started</p>
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Case Title</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((c: any) => (
                <tr key={c.id}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <FolderSearch size={16} color="var(--color-accent)" />
                      <div>
                        <div style={{ fontWeight: 600 }}>{c.title}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>#{c.id}</div>
                      </div>
                    </div>
                  </td>
                  <td><span className={`badge ${STATUS_COLORS[c.status] || 'badge-info'}`}>{c.status}</span></td>
                  <td><span className={`badge badge-${c.priority === 'critical' ? 'critical' : c.priority === 'high' ? 'high' : c.priority === 'medium' ? 'medium' : 'low'}`}>{c.priority}</span></td>
                  <td style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
                    {new Date(c.created_at).toLocaleDateString()}
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button className="btn btn-ghost btn-sm"><ChevronRight size={16} /></button>
                      <button className="btn btn-danger btn-sm" onClick={() => deleteMutation.mutate(c.id)}><Trash2 size={16} /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
