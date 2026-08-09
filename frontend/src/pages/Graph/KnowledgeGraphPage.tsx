import { useState } from 'react'
import { Network, Cpu, RefreshCw, Search, Zap, Layers, Server, User, Terminal, FileText, Globe } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { graphApi, casesApi } from '@/api/client'
import toast from 'react-hot-toast'

export default function KnowledgeGraphPage() {
  const [selectedCase, setSelectedCase] = useState<number | null>(null)
  const [search, setSearch] = useState('')
  const [selectedType, setSelectedType] = useState<string>('ALL')
  const [selectedNode, setSelectedNode] = useState<any | null>(null)

  const queryClient = useQueryClient()

  const { data: casesData } = useQuery({
    queryKey: ['cases'],
    queryFn: () => casesApi.list({ limit: 100 }),
    select: (res) => res.data?.cases || [],
  })

  const activeCaseId = selectedCase || (casesData && casesData.length > 0 ? casesData[0].id : null)

  const { data: graphData, isLoading: isGraphLoading } = useQuery({
    queryKey: ['graph', activeCaseId],
    queryFn: () => graphApi.getCaseGraph(activeCaseId!),
    enabled: !!activeCaseId,
    select: (res) => res.data,
  })

  const { data: statsData } = useQuery({
    queryKey: ['graph-stats', activeCaseId],
    queryFn: () => graphApi.getStatistics(activeCaseId!),
    enabled: !!activeCaseId,
    select: (res) => res.data,
  })

  const buildMutation = useMutation({
    mutationFn: (caseId: number) => graphApi.buildCase(caseId),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['graph', activeCaseId] })
      queryClient.invalidateQueries({ queryKey: ['graph-stats', activeCaseId] })
      toast.success(`Knowledge Graph built! ${res.data.node_count} nodes & ${res.data.edge_count} edges constructed.`)
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || 'Graph construction failed'),
  })

  const nodes = graphData?.nodes || []
  const edges = graphData?.edges || []

  const filteredNodes = nodes.filter((n: any) => {
    const matchesSearch = n.label.toLowerCase().includes(search.toLowerCase()) || n.type.toLowerCase().includes(search.toLowerCase())
    const matchesType = selectedType === 'ALL' || n.type === selectedType
    return matchesSearch && matchesType
  })

  const getNodeIcon = (type: string) => {
    switch (type) {
      case 'Host': return <Server size={14} color="var(--color-accent)" />
      case 'User': return <User size={14} color="#3b82f6" />
      case 'Process': return <Terminal size={14} color="#10b981" />
      case 'IP_Address': return <Globe size={14} color="#f59e0b" />
      default: return <FileText size={14} color="var(--color-text-muted)" />
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2>Enterprise Evidence Knowledge Graph</h2>
          <p style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
            Canonical network graph reasoning model for AI attack path reconstruction & correlation
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
            onClick={() => activeCaseId && buildMutation.mutate(activeCaseId)}
            disabled={!activeCaseId || buildMutation.isPending}
          >
            <RefreshCw size={16} className={buildMutation.isPending ? 'spinner' : ''} />
            {buildMutation.isPending ? 'Constructing Graph...' : 'Rebuild Knowledge Graph'}
          </button>
        </div>
      </div>

      {/* Metrics Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
        <div className="card" style={{ padding: '16px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: '4px' }}>TOTAL NODES</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Cpu size={20} color="var(--color-accent)" /> {statsData?.node_count || nodes.length}
          </div>
        </div>

        <div className="card" style={{ padding: '16px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: '4px' }}>RELATIONSHIP EDGES</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Network size={20} color="#3b82f6" /> {statsData?.edge_count || edges.length}
          </div>
        </div>

        <div className="card" style={{ padding: '16px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: '4px' }}>GRAPH DENSITY</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Zap size={20} color="#10b981" /> {statsData?.density ?? 0.0}
          </div>
        </div>

        <div className="card" style={{ padding: '16px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: '4px' }}>CONNECTED COMPONENTS</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={20} color="#f59e0b" /> {statsData?.connected_components ?? 1}
          </div>
        </div>
      </div>

      {/* Interactive Controls Bar */}
      <div style={{ display: 'flex', gap: '12px', background: 'var(--color-bg-surface)', padding: '12px 16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
        <div style={{ flex: 1, position: 'relative' }}>
          <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)' }} />
          <input
            type="text"
            className="input"
            style={{ paddingLeft: '36px' }}
            placeholder="Search nodes by entity label or type (e.g. DC-01, admin, powershell)..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <select className="btn btn-secondary" value={selectedType} onChange={(e) => setSelectedType(e.target.value)}>
          <option value="ALL">All Entity Types</option>
          <option value="Host">Hosts</option>
          <option value="User">Users</option>
          <option value="IP_Address">IP Addresses</option>
          <option value="Process">Processes</option>
          <option value="File">Files</option>
          <option value="Evidence">Evidence</option>
        </select>
      </div>

      {/* Main Graph Visualization Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: selectedNode ? '2fr 1fr' : '1fr', gap: '20px' }}>
        <div className="card" style={{ minHeight: '480px', display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Network size={18} /> Interactive Entity Network Model ({filteredNodes.length} nodes)
          </h3>

          {isGraphLoading ? (
            <div className="empty-state"><div className="spinner" /></div>
          ) : nodes.length === 0 ? (
            <div className="empty-state">
              <Network size={40} className="empty-state-icon" />
              <h3>No Knowledge Graph Built</h3>
              <p>Click "Rebuild Knowledge Graph" to generate nodes and weighted edges from normalized events</p>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '12px', overflowY: 'auto', maxHeight: '440px', paddingRight: '4px' }}>
              {filteredNodes.map((n: any) => (
                <div
                  key={n.id}
                  onClick={() => setSelectedNode(n)}
                  style={{
                    padding: '12px',
                    background: selectedNode?.id === n.id ? 'var(--color-accent-subtle)' : 'var(--color-bg-elevated)',
                    border: `1px solid ${selectedNode?.id === n.id ? 'var(--color-accent)' : 'var(--color-border)'}`,
                    borderRadius: 'var(--radius-md)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                    {getNodeIcon(n.type)}
                    <span className="badge badge-info" style={{ fontSize: '0.7rem' }}>{n.type}</span>
                  </div>
                  <div style={{ fontWeight: 600, fontSize: '0.875rem', wordBreak: 'break-all', fontFamily: 'var(--font-mono)' }}>
                    {n.label}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Node Detail Side Drawer */}
        {selectedNode && (
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--color-border)', paddingBottom: '12px' }}>
              <h3>Entity Node Inspector</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setSelectedNode(null)}>Close</button>
            </div>

            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>NODE ID</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>{selectedNode.uuid_id}</div>
            </div>

            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>ENTITY TYPE</div>
              <span className="badge badge-high">{selectedNode.type}</span>
            </div>

            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>LABEL</div>
              <div style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>{selectedNode.label}</div>
            </div>

            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: '6px' }}>PROPERTIES</div>
              <pre style={{ background: 'var(--color-bg-elevated)', padding: '10px', borderRadius: 'var(--radius-md)', fontSize: '0.75rem', overflowX: 'auto' }}>
                {JSON.stringify(selectedNode.properties, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
