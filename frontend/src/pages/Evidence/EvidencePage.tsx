import { useState, useCallback } from 'react'
import { Upload, File, Trash2, X, Download, Search, Clock, Play, Cpu, Layers } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { evidenceApi, casesApi, parserApi, normalizationApi } from '@/api/client'
import toast from 'react-hot-toast'

const ALLOWED_TYPES = ['evtx', 'log', 'csv', 'json', 'xml', 'txt', 'zip']

export default function EvidencePage() {
  const [selectedCase, setSelectedCase] = useState<number | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const [files, setFiles] = useState<File[]>([])
  const [search, setSearch] = useState('')
  const [selectedEvidence, setSelectedEvidence] = useState<any | null>(null)
  const [custodyLogs, setCustodyLogs] = useState<any[]>([])
  const [showCustodyModal, setShowCustodyModal] = useState(false)

  const queryClient = useQueryClient()

  const parseMutation = useMutation({
    mutationFn: (eId: number) => parserApi.parse(eId),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['evidence'] })
      toast.success(`Parsing complete! Extracted ${res.data.event_count} structured events.`)
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || 'Parsing failed'),
  })

  const normalizeMutation = useMutation({
    mutationFn: (eId: number) => normalizationApi.normalize(eId),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['evidence'] })
      toast.success(`Normalization complete! ${res.data.event_count} events standardized.`)
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || 'Normalization failed'),
  })

  const { data: casesData } = useQuery({
    queryKey: ['cases'],
    queryFn: () => casesApi.list({ limit: 100 }),
    select: (res) => res.data?.cases || [],
  })

  const { data: evidenceData, isLoading } = useQuery({
    queryKey: ['evidence', selectedCase, search],
    queryFn: () =>
      selectedCase
        ? evidenceApi.getCaseEvidence(selectedCase)
        : evidenceApi.list({ limit: 100, search: search || undefined }),
    select: (res) => res.data?.evidence || res.data || [],
  })

  const uploadMutation = useMutation({
    mutationFn: () => evidenceApi.upload(selectedCase!, files),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['evidence'] })
      toast.success(`Uploaded ${res.data.length} evidence file(s) successfully!`)
      setFiles([])
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || 'Upload failed'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => evidenceApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evidence'] })
      toast.success('Evidence file soft-deleted')
      setSelectedEvidence(null)
    },
    onError: () => toast.error('Failed to delete evidence file'),
  })

  const handleDownload = async (eId: number, originalFilename: string) => {
    try {
      const res = await evidenceApi.download(eId)
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', originalFilename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      toast.success(`Downloaded ${originalFilename}`)
    } catch {
      toast.error('Failed to download evidence file')
    }
  }

  const handleViewCustody = async (evidence: any) => {
    setSelectedEvidence(evidence)
    try {
      const res = await evidenceApi.getCustody(evidence.id)
      setCustodyLogs(res.data)
      setShowCustodyModal(true)
    } catch {
      toast.error('Failed to fetch Chain of Custody logs')
    }
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const dropped = Array.from(e.dataTransfer.files).filter((f) => {
      const ext = f.name.split('.').pop()?.toLowerCase()
      return ext && ALLOWED_TYPES.includes(ext)
    })
    setFiles((prev) => [...prev, ...dropped])
    if (dropped.length < e.dataTransfer.files.length) {
      toast.error('Some files have blocked or unsupported formats (.exe, .sh, etc.)')
    }
  }, [])

  const formatBytes = (bytes: number) => {
    if (!bytes) return '0 B'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const evidenceList = evidenceData || []

  return (
    <div className="animate-slide-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Evidence Management</h1>
          <p className="page-subtitle">Ingest, verify cryptographic hashes, and maintain Chain of Custody</p>
        </div>
      </div>

      {/* Case Selector & Global Search */}
      <div className="card" style={{ marginBottom: '20px', display: 'flex', gap: '16px', flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div className="input-group" style={{ flex: 1, minWidth: '250px' }}>
          <label className="input-label">Select Case Filter</label>
          <select
            id="evidence-case-select"
            className="input"
            value={selectedCase || ''}
            onChange={(e) => setSelectedCase(Number(e.target.value) || null)}
          >
            <option value="">— All Cases —</option>
            {casesData?.map((c: any) => (
              <option key={c.id} value={c.id}>{c.title}</option>
            ))}
          </select>
        </div>

        <div className="input-group" style={{ flex: 2, minWidth: '250px' }}>
          <label className="input-label">Search Evidence</label>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'var(--color-bg-elevated)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: '8px 12px' }}>
            <Search size={16} color="var(--color-text-muted)" />
            <input
              style={{ background: 'transparent', border: 'none', outline: 'none', color: 'var(--color-text-primary)', flex: 1 }}
              placeholder="Search filename or SHA-256 hash..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Upload Zone (Requires selected case) */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <h3 style={{ marginBottom: '16px' }}>
          Upload Forensic Evidence {selectedCase ? `to Case #${selectedCase}` : ''}
        </h3>

        {!selectedCase ? (
          <div style={{ padding: '20px', background: 'rgba(234, 179, 8, 0.1)', border: '1px solid rgba(234, 179, 8, 0.3)', borderRadius: 'var(--radius-md)', color: 'var(--color-amber)', fontSize: '0.875rem' }}>
            ⚠️ Please select a specific <strong>Case</strong> from the dropdown above to upload evidence files.
          </div>
        ) : (
          <>
            <div
              className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => document.getElementById('file-input')?.click()}
            >
              <input
                id="file-input"
                type="file"
                multiple
                accept=".evtx,.log,.csv,.json,.xml,.txt,.zip"
                style={{ display: 'none' }}
                onChange={(e) => setFiles(Array.from(e.target.files || []))}
              />
              <Upload size={36} color="var(--color-accent)" style={{ marginBottom: '12px', opacity: 0.8 }} />
              <p style={{ fontWeight: 600, marginBottom: '8px', color: 'var(--color-text-primary)' }}>
                Drag & Drop forensic evidence files here, or click to browse
              </p>
              <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
                Supported formats: <strong>.evtx, .log, .csv, .json, .xml, .txt, .zip</strong> (Max 500 MB). Executable files (.exe, .sh, .bat) are blocked.
              </p>
            </div>

            {/* Staged Files List */}
            {files.length > 0 && (
              <div style={{ marginTop: '16px' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px' }}>
                  {files.map((f, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px', background: 'var(--color-bg-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
                      <File size={16} color="var(--color-accent)" />
                      <span style={{ flex: 1, fontSize: '0.875rem' }}>{f.name}</span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{formatBytes(f.size)}</span>
                      <button onClick={() => setFiles(files.filter((_, j) => j !== i))} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)' }}>
                        <X size={14} />
                      </button>
                    </div>
                  ))}
                </div>
                <button
                  className="btn btn-primary"
                  onClick={() => uploadMutation.mutate()}
                  disabled={uploadMutation.isPending}
                >
                  {uploadMutation.isPending ? 'Ingesting & Hashing Files...' : `Upload & Hash ${files.length} Evidence File(s)`}
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Evidence Table */}
      <div className="card">
        <h3 style={{ marginBottom: '16px' }}>Ingested Evidence Repository</h3>
        {isLoading ? (
          <div className="empty-state"><div className="spinner" /></div>
        ) : evidenceList.length === 0 ? (
          <div className="empty-state">
            <File size={40} className="empty-state-icon" />
            <h3>No Evidence Files Found</h3>
            <p>Select a case and upload forensic log files to begin evidence reconstruction</p>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Original Filename</th>
                  <th>Format</th>
                  <th>Size</th>
                  <th>Cryptographic SHA-256</th>
                  <th>AI Pipeline Stage</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {evidenceList.map((e: any) => (
                  <tr key={e.id}>
                    <td>
                      <div style={{ fontWeight: 600, fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>
                        {e.original_filename}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Case #{e.case_id}</div>
                    </td>
                    <td><span className="badge badge-info">.{e.file_type}</span></td>
                    <td style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>{formatBytes(e.size)}</td>
                    <td>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                        {e.sha256?.slice(0, 16)}...
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <span className={`badge ${e.processing_stage === 'NORMALIZED' ? 'badge-high' : (e.processing_stage === 'PARSED' ? 'badge-info' : 'badge-medium')}`} style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                          <Cpu size={12} /> {e.processing_stage || 'VERIFIED'}
                        </span>
                        {e.is_parsed && (
                          <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                            {e.event_count} events
                          </span>
                        )}
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <button
                          className="btn btn-primary btn-sm"
                          title="Parse Evidence"
                          onClick={() => parseMutation.mutate(e.id)}
                          disabled={parseMutation.isPending && parseMutation.variables === e.id}
                        >
                          <Play size={14} /> Parse
                        </button>
                        <button
                          className="btn btn-secondary btn-sm"
                          title="Normalize Evidence Events"
                          onClick={() => normalizeMutation.mutate(e.id)}
                          disabled={!e.is_parsed || (normalizeMutation.isPending && normalizeMutation.variables === e.id)}
                        >
                          <Layers size={14} /> Normalize
                        </button>
                        <button className="btn btn-secondary btn-sm" title="Chain of Custody" onClick={() => handleViewCustody(e)}>
                          <Clock size={14} /> Custody
                        </button>
                        <button className="btn btn-primary btn-sm" title="Download Original File" onClick={() => handleDownload(e.id, e.original_filename)}>
                          <Download size={14} />
                        </button>
                        <button className="btn btn-danger btn-sm" title="Soft Delete Evidence" onClick={() => deleteMutation.mutate(e.id)}>
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Chain of Custody Audit Log Modal */}
      {showCustodyModal && selectedEvidence && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="card animate-slide-in" style={{ width: '650px', maxWidth: '90vw', maxHeight: '85vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h3>Chain of Custody Audit Log</h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
                  {selectedEvidence.original_filename} (ID #{selectedEvidence.id})
                </p>
              </div>
              <button onClick={() => setShowCustodyModal(false)} className="btn btn-ghost"><X size={18} /></button>
            </div>

            <div style={{ background: 'var(--color-bg-elevated)', padding: '14px', borderRadius: 'var(--radius-md)', marginBottom: '16px', fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
              <div><strong>SHA-256:</strong> {selectedEvidence.sha256}</div>
              <div><strong>SHA-1:</strong> {selectedEvidence.sha1 || 'N/A'}</div>
              <div><strong>MD5:</strong> {selectedEvidence.md5 || 'N/A'}</div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {custodyLogs.map((log: any) => (
                <div key={log.id} style={{ padding: '12px', background: 'var(--color-bg-subtle)', borderRadius: 'var(--radius-md)', borderLeft: '3px solid var(--color-accent)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 600, fontSize: '0.875rem' }}>
                    <span>ACTION: {log.action}</span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                      {new Date(log.timestamp).toLocaleString()}
                    </span>
                  </div>
                  {log.details && (
                    <pre style={{ margin: '6px 0 0 0', fontSize: '0.75rem', color: 'var(--color-text-muted)', whiteSpace: 'pre-wrap' }}>
                      {JSON.stringify(log.details, null, 2)}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
