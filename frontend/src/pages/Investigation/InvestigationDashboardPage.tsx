// ═══════════════════════════════════════════════════════════════════════════════
// Investigation Dashboard — Case Investigation Workbench
// Reconstructed Attack Path Visualizer & Simulation Engine
// ═══════════════════════════════════════════════════════════════════════════════

import { useState, useEffect, useMemo, useRef } from 'react'
import { useParams } from 'react-router-dom'
import {
  Play, Pause, SkipBack, SkipForward, RotateCcw, Shield, AlertTriangle,
  Zap, Activity, Users, Server, Bug, Terminal, FileCode,
  Globe, Lock, Eye, Cpu, HardDrive
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { casesApi, graphApi, cspApi } from '@/api/client'

/* ─── Types ──────────────────────────────────────────────────────────────── */
interface GraphNode { uuid_id: string; type: string; label: string; properties: Record<string, unknown> }
interface GraphEdge { source: string; target: string; relationship: string; weight: number; properties?: Record<string, unknown> }
interface AttackStage { index: number; node: GraphNode; edges: GraphEdge[]; severity: 'critical'|'high'|'medium'|'low'; description: string; category: string }

/* ─── Constants ──────────────────────────────────────────────────────────── */
const SEV_COLOR: Record<string,string> = { critical:'#ef4444', high:'#f97316', medium:'#eab308', low:'#22c55e' }
const SEV_BG:    Record<string,string> = { critical:'rgba(239,68,68,.12)', high:'rgba(249,115,22,.12)', medium:'rgba(234,179,8,.12)', low:'rgba(34,197,94,.12)' }
const RISK_MAP: Record<string,{label:string;color:string}> = { critical:{label:'CRITICAL',color:'#ef4444'}, high:{label:'SEVERE',color:'#f97316'}, medium:{label:'ELEVATED',color:'#eab308'}, low:{label:'GUARDED',color:'#22c55e'} }

/* ─── Helpers ────────────────────────────────────────────────────────────── */
function nodeIcon(type:string){const t=type.toLowerCase();if(t.includes('user')||t.includes('account'))return Users;if(t.includes('host')||t.includes('server'))return Server;if(t.includes('malware')||t.includes('exploit'))return Bug;if(t.includes('process')||t.includes('cmd'))return Terminal;if(t.includes('file')||t.includes('log'))return FileCode;if(t.includes('ip')||t.includes('domain'))return Globe;if(t.includes('credential'))return Lock;if(t.includes('registry'))return Cpu;return HardDrive}
function sev(n:GraphNode):AttackStage['severity']{const t=(n.type||'').toLowerCase(),l=(n.label||'').toLowerCase();if(t.includes('malware')||t.includes('exploit')||l.includes('ransomware'))return'critical';if(t.includes('user')||t.includes('cmd')||l.includes('admin')||l.includes('privilege'))return'high';if(t.includes('file')||t.includes('process')||l.includes('scan'))return'medium';return'low'}
function cat(n:GraphNode):string{const t=(n.type||'').toLowerCase(),l=(n.label||'').toLowerCase();if(l.includes('lateral'))return'Lateral Movement';if(l.includes('privilege')||l.includes('escalat'))return'Privilege Escalation';if(l.includes('exfil'))return'Data Exfiltration';if(t.includes('malware'))return'Malware Execution';if(t.includes('user')||t.includes('credential'))return'Unauthorized Access';if(t.includes('process')||t.includes('cmd'))return'Process Execution';if(t.includes('host')||t.includes('server'))return'Host Compromise';return'Unknown Activity'}

/* ─── Component ──────────────────────────────────────────────────────────── */
export default function InvestigationDashboardPage() {
  const { caseId: paramCaseId } = useParams<{ caseId: string }>()

  const { data: cases } = useQuery({
    queryKey: ['cases'], queryFn: () => casesApi.list({ limit: 50 }),
    select: r => r.data?.cases ?? r.data ?? [],
  })
  const [caseIdx, setCaseIdx] = useState(0)
  const caseId = paramCaseId ? Number(paramCaseId) : (cases?.[caseIdx]?.id ?? null)

  const { data: graphData, isLoading } = useQuery({
    queryKey: ['graph', caseId], queryFn: () => graphApi.getCaseGraph(caseId!),
    enabled: !!caseId, select: r => r.data,
  })

  const { data: cspData } = useQuery({
    queryKey: ['csp-results', caseId], queryFn: () => cspApi.getResults(caseId!),
    enabled: !!caseId, select: r => r.data,
  })

  const stages: AttackStage[] = useMemo(() => {
    if (!graphData?.nodes?.length) return []
    const nodes: GraphNode[] = graphData.nodes, edges: GraphEdge[] = graphData.edges || []
    return nodes.map((n, i) => {
      const s = sev(n), c = cat(n)
      return { index:i, node:n, edges: edges.filter(e => e.source===n.uuid_id||e.target===n.uuid_id), severity:s, category:c, description:`${c} — ${n.type} entity "${n.label}" detected in the attack chain.` }
    })
  }, [graphData])

  const riskScore = useMemo(() => {
    if (!stages.length) return 0
    const w = {critical:25,high:15,medium:8,low:3}; let s=0; stages.forEach(st => s += w[st.severity]); return Math.min(100,s)
  }, [stages])

  const riskLevel = riskScore>=75?'critical':riskScore>=50?'high':riskScore>=25?'medium':'low'
  const riskInfo = RISK_MAP[riskLevel]
  const threats = useMemo(() => { const s=new Set<string>(); stages.forEach(st => { if(st.category!=='Unknown Activity') s.add(st.category.toUpperCase().replace(/ /g,'_')) }); return [...s].slice(0,4) }, [stages])
  const accts = useMemo(() => { const s=new Set<string>(); stages.forEach(st => { if(st.node.type?.toLowerCase().includes('user')) s.add(st.node.label) }); return [...s].slice(0,3) }, [stages])
  const hosts = useMemo(() => { const s=new Set<string>(); stages.forEach(st => { if(st.node.type?.toLowerCase().includes('host')||st.node.type?.toLowerCase().includes('server')) s.add(st.node.label) }); return [...s].slice(0,3) }, [stages])

  const [playing, setPlaying] = useState(false)
  const [step, setStep] = useState(0)
  const [spd, setSpd] = useState('1')
  const total = stages.length
  const tlRef = useRef<HTMLDivElement>(null)
  const spdMs: Record<string,number> = {'0.5':3000,'1':1500,'2':800,'3':400}

  // Animation Interval
  useEffect(() => {
    if (!playing || !total) return
    const id = setInterval(() => {
      setStep(s => {
        if (s + 1 >= total) {
          setPlaying(false)
          return total - 1
        }
        return s + 1
      })
    }, spdMs[spd] || 1500)
    return () => clearInterval(id)
  }, [playing, total, spd])

  // Isolated Horizontal Scroll — prevents page layout from jumping!
  useEffect(() => {
    const el = tlRef.current
    if (!el) return
    const activeEl = el.querySelector('[data-active="true"]') as HTMLElement | null
    if (activeEl) {
      const containerRect = el.getBoundingClientRect()
      const itemRect = activeEl.getBoundingClientRect()
      const targetScrollLeft = (itemRect.left - containerRect.left) + el.scrollLeft - (containerRect.width / 2) + (itemRect.width / 2)
      el.scrollTo({ left: Math.max(0, targetScrollLeft), behavior: 'smooth' })
    }
  }, [step])

  const cur = stages[step] || null
  const plaus = cspData?.score ?? (riskScore>0 ? (100-riskScore*0.3).toFixed(1) : 0)

  /* ─── Inline Styles ──────────────────────────────────────────────────── */
  const card: React.CSSProperties = { background:'var(--color-bg-card)', border:'1px solid var(--color-border)', borderRadius:'var(--radius-lg)', padding:'20px' }

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:'16px', minHeight:0 }}>

      {/* ═══ HEADER ═══ */}
      <div style={{ ...card, background:'linear-gradient(135deg,var(--color-bg-card) 0%,#0d1a30 100%)', display:'flex', justifyContent:'space-between', alignItems:'center', flexWrap:'wrap', gap:'12px', padding:'20px 24px' }}>
        <div style={{ minWidth:0, flex:'1 1 400px' }}>
          <div style={{ display:'flex', alignItems:'center', gap:'10px', flexWrap:'wrap' }}>
            <h2 style={{ margin:0, fontSize:'1.25rem', whiteSpace:'nowrap' }}>Case Investigation Workbench</h2>
            <span style={{ padding:'3px 12px', borderRadius:'999px', fontSize:'0.7rem', fontWeight:700, border:`1px solid ${riskInfo.color}`, color:riskInfo.color, background:`${riskInfo.color}10`, whiteSpace:'nowrap' }}>
              {riskInfo.label} RISK ({riskScore}/100)
            </span>
          </div>
          <p style={{ margin:'4px 0 0', fontSize:'0.78rem', color:'var(--color-text-muted)' }}>
            Evidence-Based Incident Reconstruction combining Knowledge Graph, CSP, UCS, A*, Reasoning, &amp; Risk Analysis
          </p>
        </div>
        <div style={{ display:'flex', alignItems:'center', gap:'8px', flexShrink:0, flexWrap:'wrap' }}>
          <button className="btn btn-primary" style={{ display:'flex', alignItems:'center', gap:'6px', background:'var(--gradient-accent)', border:'none', fontWeight:600, fontSize:'0.8rem', padding:'8px 16px', whiteSpace:'nowrap' }}>
            <Zap size={14} /> Run AI Pipeline &amp; Build Graph
          </button>
          {cases && cases.length > 1 && (
            <select value={caseIdx} onChange={e=>{setCaseIdx(+e.target.value);setStep(0);setPlaying(false)}}
              style={{ background:'var(--color-bg-elevated)', color:'var(--color-text-primary)', border:'1px solid var(--color-border)', borderRadius:'var(--radius-md)', padding:'6px 10px', fontSize:'0.78rem' }}>
              {cases.map((c:any,i:number)=><option key={c.id} value={i}>Case #{c.id}</option>)}
            </select>
          )}
        </div>
      </div>

      {/* ═══ RISK + SCOPE ROW ═══ */}
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'16px' }}>
        {/* Risk Assessment */}
        <div style={card}>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'16px' }}>
            <h4 style={{ margin:0, fontSize:'0.9rem', color:'var(--color-text-secondary)' }}>Cybersecurity Risk Assessment</h4>
            <Shield size={16} color="var(--color-text-muted)" />
          </div>
          <div style={{ display:'flex', alignItems:'center', gap:'20px' }}>
            <div style={{ position:'relative', width:'80px', height:'80px', flexShrink:0 }}>
              <svg width="80" height="80" viewBox="0 0 80 80">
                <circle cx="40" cy="40" r="34" fill="none" stroke="var(--color-border)" strokeWidth="6"/>
                <circle cx="40" cy="40" r="34" fill="none" stroke={riskInfo.color} strokeWidth="6"
                  strokeDasharray={`${(riskScore/100)*213.6} 213.6`} strokeLinecap="round" transform="rotate(-90 40 40)"
                  style={{transition:'stroke-dasharray 0.8s ease'}}/>
              </svg>
              <div style={{ position:'absolute', top:'50%', left:'50%', transform:'translate(-50%,-50%)', textAlign:'center' }}>
                <div style={{ fontSize:'1.4rem', fontWeight:800, color:riskInfo.color, lineHeight:1 }}>{riskScore}</div>
                <div style={{ fontSize:'0.55rem', color:'var(--color-text-muted)' }}>/ 100</div>
              </div>
            </div>
            <div>
              <div style={{ fontSize:'1.1rem', fontWeight:700, color:riskInfo.color, marginBottom:'4px' }}>{riskInfo.label}</div>
              <div style={{ fontSize:'0.78rem', color:'var(--color-text-muted)' }}>Confidence: {stages.length?'95':'0'}%</div>
              <div style={{ fontSize:'0.78rem', color:'var(--color-text-muted)' }}>Supporting Events: {stages.length}</div>
            </div>
          </div>
        </div>

        {/* Attack Scope */}
        <div style={card}>
          <h4 style={{ margin:'0 0 14px', fontSize:'0.9rem', color:'var(--color-text-secondary)' }}>Attack Scope &amp; Threat Types</h4>
          <div style={{ display:'flex', flexWrap:'wrap', gap:'6px', marginBottom:'12px' }}>
            {threats.length ? threats.map(t => (
              <span key={t} style={{ display:'inline-flex', alignItems:'center', gap:'4px', padding:'3px 10px', borderRadius:'999px', fontSize:'0.68rem', fontWeight:600, background:'rgba(239,68,68,.12)', color:'#ef4444', border:'1px solid rgba(239,68,68,.3)' }}>
                <Zap size={10}/> {t}
              </span>
            )) : <span style={{ fontSize:'0.78rem', color:'var(--color-text-muted)' }}>No threats detected</span>}
          </div>
          <div style={{ display:'flex', gap:'16px', fontSize:'0.78rem', color:'var(--color-text-secondary)', flexWrap:'wrap' }}>
            <span><Users size={13} style={{ verticalAlign:'middle', marginRight:'4px' }}/>Accounts: {accts.length?accts.join(', '):'—'}</span>
            <span><Server size={13} style={{ verticalAlign:'middle', marginRight:'4px' }}/>Hosts: {hosts.length?hosts.join(', '):'—'}</span>
          </div>
        </div>
      </div>

      {/* ═══ ATTACK PATH VISUALIZER ═══ */}
      <div style={card}>
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'4px', flexWrap:'wrap', gap:'8px' }}>
          <div style={{ display:'flex', alignItems:'center', gap:'8px' }}>
            <Activity size={18} color="var(--color-cyan)"/>
            <h3 style={{ margin:0, fontSize:'1rem' }}>Reconstructed Attack Path Visualizer &amp; Simulation Engine</h3>
          </div>
          {playing && (
            <div style={{ display:'inline-flex', alignItems:'center', gap:'6px', padding:'4px 12px', borderRadius:'999px', background:'rgba(239,68,68,0.15)', border:'1px solid rgba(239,68,68,0.4)', color:'#ef4444', fontSize:'0.7rem', fontWeight:700 }}>
              <span style={{ width:'8px', height:'8px', borderRadius:'50%', background:'#ef4444', animation:'statusBeacon 0.8s infinite' }} />
              LIVE ATTACK SIMULATION PLAYBACK
            </div>
          )}
        </div>
        <p style={{ margin:'0 0 14px', fontSize:'0.75rem', color:'var(--color-text-muted)' }}>
          Plausibility Score: {plaus} / 100 • Step-by-Step Traversal • Knowledge Graph, UCS, A*, &amp; Reasoning
        </p>

        {/* Controls Bar */}
        <div style={{ display:'flex', alignItems:'center', gap:'8px', flexWrap:'wrap', marginBottom:'16px', background:'var(--color-bg-elevated)', padding:'10px 14px', borderRadius:'var(--radius-md)', border:'1px solid var(--color-border)' }}>
          <button onClick={()=>{if(step>=total-1&&!playing)setStep(0);setPlaying(p=>!p)}} disabled={isLoading||!total}
            style={{ display:'flex', alignItems:'center', gap:'6px', background:playing?'#ef4444':'#10b981', color:'#fff', border:'none', padding:'8px 18px', borderRadius:'var(--radius-md)', fontSize:'0.8rem', fontWeight:700, cursor:'pointer', opacity:isLoading||!total?.5:1, boxShadow: playing?'0 0 12px rgba(239,68,68,0.4)':'0 0 12px rgba(16,185,129,0.3)', transition:'all 0.2s ease' }}>
            {playing?<Pause size={14}/>:<Play size={14}/>} {playing?'Pause Simulation':'Play Attack Simulation'}
          </button>
          <button className="btn btn-secondary" title="Reset to Start" onClick={()=>{setStep(0);setPlaying(false)}} style={{padding:'7px 10px'}}><SkipBack size={14}/></button>
          <button className="btn btn-secondary" title="Step Back" onClick={()=>{setStep(s=>Math.max(0,s-1));setPlaying(false)}} disabled={step<=0} style={{padding:'7px 10px'}}><SkipBack size={14} style={{transform:'rotate(180deg)'}}/></button>
          <button className="btn btn-secondary" title="Step Forward" onClick={()=>{setStep(s=>Math.min(s+1,total-1));setPlaying(false)}} disabled={step>=total-1} style={{padding:'7px 10px'}}><SkipForward size={14}/></button>
          <button className="btn btn-secondary" title="Restart" onClick={()=>{setStep(0);setPlaying(false)}} style={{padding:'7px 10px'}}><RotateCcw size={14}/></button>
          
          <div style={{ display:'flex', alignItems:'center', gap:'6px', marginLeft:'4px', background:'var(--color-bg-card)', border:'1px solid var(--color-border)', borderRadius:'var(--radius-md)', padding:'4px 10px' }}>
            <span style={{ fontSize:'0.7rem', color:'var(--color-text-muted)', fontWeight:600 }}>Speed:</span>
            <select value={spd} onChange={e=>setSpd(e.target.value)}
              style={{ background:'transparent', border:'none', color:'var(--color-text-primary)', fontSize:'0.75rem', fontWeight:700, cursor:'pointer', outline:'none' }}>
              <option value="0.5">0.5x (Slow)</option>
              <option value="1">1.0x (Normal)</option>
              <option value="2">2.0x (Fast)</option>
              <option value="3">3.0x (Ultra)</option>
            </select>
          </div>

          <div style={{ marginLeft:'auto', display:'flex', alignItems:'center', gap:'10px' }}>
            <div style={{ fontSize:'0.75rem', color:'var(--color-text-secondary)', fontWeight:600 }}>
              Stage <span style={{ color:SEV_COLOR[cur?.severity||'low'], fontWeight:800 }}>{total ? step + 1 : 0}</span> of {total}
            </div>
            <div style={{ width:'100px', height:'6px', background:'var(--color-bg-card)', borderRadius:'3px', overflow:'hidden', border:'1px solid var(--color-border)' }}>
              <div style={{ height:'100%', width:`${total ? ((step + 1) / total) * 100 : 0}%`, background:'var(--gradient-accent)', transition:'width 0.3s ease' }} />
            </div>
          </div>
        </div>

        {/* Current Stage Banner */}
        {cur && (
          <div style={{ background:'var(--color-bg-elevated)', border:`1px solid ${SEV_COLOR[cur.severity]}50`, borderRadius:'var(--radius-md)', padding:'14px 18px', marginBottom:'16px', display:'flex', alignItems:'center', gap:'12px', boxShadow:`0 4px 20px ${SEV_COLOR[cur.severity]}15` }}>
            <div style={{ position:'relative', flexShrink:0 }}>
              <div style={{ width:'32px', height:'32px', borderRadius:'50%', background:SEV_BG[cur.severity], border:`2px solid ${SEV_COLOR[cur.severity]}`, display:'flex', alignItems:'center', justifyContent:'center', fontSize:'0.8rem', fontWeight:800, color:SEV_COLOR[cur.severity] }}>
                {step+1}
              </div>
              {playing && (
                <div style={{ position:'absolute', top:'-2px', left:'-2px', right:'-2px', bottom:'-2px', borderRadius:'50%', border:`2px solid ${SEV_COLOR[cur.severity]}`, animation:'nodeRadar 1.2s infinite ease-out' }} />
              )}
            </div>
            <div style={{ minWidth:0, flex:1 }}>
              <div style={{ display:'flex', alignItems:'center', gap:'8px', flexWrap:'wrap' }}>
                <span style={{ fontSize:'0.9rem', fontWeight:800, color:'var(--color-text-primary)' }}>STAGE #{step+1}: {cur.node.label}</span>
                <span style={{ padding:'2px 8px', borderRadius:'4px', fontSize:'0.65rem', fontWeight:700, background:SEV_BG[cur.severity], color:SEV_COLOR[cur.severity], textTransform:'uppercase' }}>{cur.severity} SEVERITY</span>
                <span style={{ padding:'2px 8px', borderRadius:'4px', fontSize:'0.65rem', fontWeight:600, background:'var(--color-bg-card)', color:'var(--color-cyan)', border:'1px solid var(--color-border)' }}>{cur.category}</span>
              </div>
              <div style={{ fontSize:'0.78rem', color:'var(--color-text-secondary)', marginTop:'2px', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{cur.description}</div>
            </div>
          </div>
        )}

        {/* Tree Hierarchical Visualizer Container */}
        {!total ? (
          <div style={{ textAlign:'center', padding:'40px 20px', color:'var(--color-text-muted)', border:'2px dashed var(--color-border)', borderRadius:'var(--radius-md)' }}>
            <Shield size={36} style={{marginBottom:'8px',opacity:.4}}/><p style={{margin:0}}>No attack path data. Build a Knowledge Graph first.</p>
          </div>
        ) : (
          <div ref={tlRef} style={{ display:'flex', flexDirection:'column', gap:'20px', padding:'12px 0' }}>
            {(() => {
              const BOXES_PER_ROW = 4
              const rowCount = Math.ceil(stages.length / BOXES_PER_ROW)
              const rows: AttackStage[][] = []
              for (let r = 0; r < rowCount; r++) {
                rows.push(stages.slice(r * BOXES_PER_ROW, (r + 1) * BOXES_PER_ROW))
              }

              return rows.map((rowStages, rIdx) => {
                const isCurrentRowActive = step >= rIdx * BOXES_PER_ROW && step < (rIdx + 1) * BOXES_PER_ROW
                return (
                  <div key={`tree-row-${rIdx}`} style={{ display:'flex', flexDirection:'column', gap:'12px' }}>
                    {/* Tree Level Header Badge */}
                    <div style={{ display:'flex', alignItems:'center', gap:'10px' }}>
                      <span style={{
                        display:'inline-flex', alignItems:'center', gap:'6px',
                        padding:'4px 12px', borderRadius:'6px', fontSize:'0.7rem', fontWeight:800,
                        background: isCurrentRowActive ? 'rgba(6,182,212,0.15)' : 'var(--color-bg-elevated)',
                        border: `1px solid ${isCurrentRowActive ? 'var(--color-cyan)' : 'var(--color-border)'}`,
                        color: isCurrentRowActive ? 'var(--color-cyan)' : 'var(--color-text-muted)',
                        letterSpacing:'0.04em'
                      }}>
                        <span style={{ width:'6px', height:'6px', borderRadius:'50%', background: isCurrentRowActive ? 'var(--color-cyan)' : 'var(--color-text-muted)' }} />
                        TREE LEVEL {rIdx + 1} • {rIdx === 0 ? 'INITIAL COMPROMISE & VECTOR' : rIdx === 1 ? 'EXECUTION & ELEVATION' : 'OBJECTIVES & IMPACT'}
                      </span>
                      <div style={{ height:'1px', flex:1, background: isCurrentRowActive ? 'linear-gradient(90deg, var(--color-cyan), transparent)' : 'var(--color-border)' }} />
                    </div>

                    {/* Nodes Row (Max 4-5 items) */}
                    <div style={{ display:'flex', alignItems:'center', flexWrap:'wrap', gap:'12px 0' }}>
                      {rowStages.map((sg, cIdx) => {
                        const globalIdx = rIdx * BOXES_PER_ROW + cIdx
                        const active = globalIdx === step
                        const past = globalIdx < step
                        const Icon = nodeIcon(sg.node.type)
                        const isLastInRow = cIdx === rowStages.length - 1

                        return (
                          <div key={sg.node.uuid_id} data-active={active?'true':'false'} style={{ display:'flex', alignItems:'center', flexShrink:0 }}>
                            {/* Node Card */}
                            <div onClick={()=>{setStep(globalIdx);setPlaying(false)}} style={{
                              width:'175px',
                              background: active ? 'var(--color-bg-elevated)' : past ? 'var(--color-bg-card)' : 'rgba(15,22,41,0.6)',
                              border: `2px solid ${active ? SEV_COLOR[sg.severity] : past ? '#ef4444' : 'var(--color-border)'}`,
                              borderRadius: 'var(--radius-md)',
                              padding: '14px 12px',
                              cursor: 'pointer',
                              position: 'relative',
                              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                              boxShadow: active ? `0 0 24px ${SEV_COLOR[sg.severity]}40` : past ? '0 0 10px rgba(239,68,68,0.15)' : 'none',
                              animation: active ? 'nodeGlowPulse 2s infinite ease-in-out' : 'none',
                            }}>
                              {/* Radar Ring when Active */}
                              {active && playing && (
                                <div style={{ position:'absolute', inset:'-6px', borderRadius:'var(--radius-lg)', border:`2px solid ${SEV_COLOR[sg.severity]}`, animation:'nodeRadar 1.5s infinite ease-out', pointerEvents:'none' }} />
                              )}

                              {/* Step Tag */}
                              {active ? (
                                <div style={{ position:'absolute', top:'-10px', right:'8px', background:SEV_COLOR[sg.severity], color:'#fff', fontSize:'.55rem', fontWeight:900, padding:'2px 8px', borderRadius:'4px', textTransform:'uppercase', letterSpacing:'.05em', boxShadow:'0 2px 6px rgba(0,0,0,0.4)' }}>
                                  ACTIVE STEP #{globalIdx + 1}
                                </div>
                              ) : past ? (
                                <div style={{ position:'absolute', top:'-10px', right:'8px', background:'#ef4444', color:'#fff', fontSize:'.5rem', fontWeight:800, padding:'1px 6px', borderRadius:'3px', textTransform:'uppercase' }}>
                                  COMPROMISED
                                </div>
                              ) : null}

                              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'8px' }}>
                                <span style={{ fontSize:'.62rem', color:'var(--color-text-muted)', fontWeight:700, textTransform:'uppercase', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap', maxWidth:'95px' }}>
                                  STAGE #{globalIdx + 1}
                                </span>
                                <span style={{ padding:'1px 6px', borderRadius:'3px', fontSize:'.52rem', fontWeight:800, background:SEV_BG[sg.severity], color:SEV_COLOR[sg.severity], textTransform:'uppercase' }}>
                                  {sg.severity}
                                </span>
                              </div>

                              <div style={{ display:'flex', alignItems:'center', gap:'8px' }}>
                                <div style={{ width:'32px', height:'32px', borderRadius:'8px', background: active ? `${SEV_COLOR[sg.severity]}25` : past ? 'rgba(239,68,68,0.15)' : 'var(--color-bg-elevated)', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0, border:`1px solid ${active?SEV_COLOR[sg.severity]:past?'rgba(239,68,68,0.3)':'var(--color-border)'}` }}>
                                  <Icon size={16} color={active ? SEV_COLOR[sg.severity] : past ? '#ef4444' : 'var(--color-text-muted)'} />
                                </div>
                                <div style={{ overflow:'hidden' }}>
                                  <div style={{ fontSize:'.8rem', fontWeight:700, fontFamily:'var(--font-mono)', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap', color: active ? '#fff' : past ? 'var(--color-text-primary)' : 'var(--color-text-secondary)' }}>
                                    {sg.node.label}
                                  </div>
                                  <div style={{ fontSize:'.62rem', color:'var(--color-text-muted)', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>
                                    {sg.node.type}
                                  </div>
                                </div>
                              </div>
                            </div>

                            {/* In-Row Horizontal Vector Arrow */}
                            {!isLastInRow && (
                              <div style={{ display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', width:'70px', flexShrink:0, padding:'0 4px' }}>
                                <div style={{ fontSize:'.53rem', color: (globalIdx === step && playing) ? 'var(--color-cyan)' : globalIdx < step ? '#ef4444' : 'var(--color-text-muted)', marginBottom:'4px', textTransform:'uppercase', fontWeight:700, whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis', maxWidth:'65px', textAlign:'center' }}>
                                  {sg.edges[0]?.relationship || 'TREE_LINK'}
                                </div>

                                <div style={{ width:'100%', height:'3px', background: globalIdx < step ? 'linear-gradient(90deg, #ef4444, #ef4444)' : globalIdx === step ? 'linear-gradient(90deg, #ef4444, var(--color-cyan))' : 'var(--color-border)', position:'relative', borderRadius:'2px' }}>
                                  {globalIdx === step && (
                                    <div style={{
                                      position: 'absolute',
                                      top: '-3.5px',
                                      width: '10px',
                                      height: '10px',
                                      borderRadius: '50%',
                                      background: '#06b6d4',
                                      boxShadow: '0 0 10px #06b6d4, 0 0 20px #06b6d4',
                                      animation: `laserPacket ${spdMs[spd]}ms infinite linear`,
                                      zIndex: 5,
                                    }} />
                                  )}
                                  <div style={{
                                    position: 'absolute',
                                    right: '-4px',
                                    top: '-3.5px',
                                    width: 0,
                                    height: 0,
                                    borderTop: '5px solid transparent',
                                    borderBottom: '5px solid transparent',
                                    borderLeft: `7px solid ${globalIdx < step ? '#ef4444' : globalIdx === step ? 'var(--color-cyan)' : 'var(--color-border)'}`
                                  }} />
                                </div>
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>

                    {/* Downward Tree Branch Indicator (Connecting row N to row N+1) */}
                    {rIdx < rowCount - 1 && (
                      <div style={{ display:'flex', alignItems:'center', justifyContent:'center', padding:'4px 0 8px', color: (step >= (rIdx + 1) * BOXES_PER_ROW) ? '#ef4444' : 'var(--color-text-muted)' }}>
                        <div style={{ height:'1px', flex:1, background:'var(--color-border)' }} />
                        <div style={{
                          display:'inline-flex', alignItems:'center', gap:'6px',
                          padding:'4px 14px', borderRadius:'999px',
                          background:'var(--color-bg-elevated)', border:`1px solid ${(step >= (rIdx + 1) * BOXES_PER_ROW) ? 'rgba(239,68,68,0.4)' : 'var(--color-border)'}`,
                          fontSize:'0.66rem', fontWeight:700,
                          color: (step >= (rIdx + 1) * BOXES_PER_ROW) ? '#ef4444' : 'var(--color-cyan)',
                          boxShadow: (step >= (rIdx + 1) * BOXES_PER_ROW) ? '0 0 10px rgba(239,68,68,0.2)' : 'none'
                        }}>
                          ↓ TREE LEVEL {rIdx + 2} DOWNWARD BRANCH (ATTACK TRAVERSAL)
                        </div>
                        <div style={{ height:'1px', flex:1, background:'var(--color-border)' }} />
                      </div>
                    )}
                  </div>
                )
              })
            })()}
          </div>
        )}
      </div>

      {/* ═══ REAL-TIME TELEMETRY LOG STREAM ═══ */}
      {cur && (
        <div style={{ ...card, padding:'16px 20px', background:'var(--color-bg-card)' }}>
          <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:'10px' }}>
            <div style={{ display:'flex', alignItems:'center', gap:'8px' }}>
              <Terminal size={16} color="var(--color-cyan)" />
              <h4 style={{ margin:0, fontSize:'.88rem', fontWeight:700 }}>Attack Step Simulation Telemetry Stream</h4>
            </div>
            <span style={{ fontSize:'0.7rem', fontFamily:'var(--font-mono)', color:'var(--color-text-muted)' }}>
              Step {step + 1} of {total} — Executed Sequential Logs
            </span>
          </div>

          <div style={{ background:'var(--color-bg-primary)', border:'1px solid var(--color-border)', borderRadius:'var(--radius-sm)', padding:'12px', fontFamily:'var(--font-mono)', fontSize:'0.72rem', maxHeight:'140px', overflowY:'auto', display:'flex', flexDirection:'column', gap:'6px' }}>
            {stages.slice(0, step + 1).map((stg, idx) => (
              <div key={stg.node.uuid_id} style={{ display:'flex', alignItems:'flex-start', gap:'8px', color: idx === step ? '#06b6d4' : 'var(--color-text-secondary)', fontWeight: idx === step ? 700 : 400 }}>
                <span style={{ color: idx === step ? '#ef4444' : 'var(--color-text-muted)', flexShrink:0 }}>[STAGE #{idx + 1}]</span>
                <span style={{ flexShrink:0, color: SEV_COLOR[stg.severity] }}>[{stg.category.toUpperCase().replace(/ /g, '_')}]</span>
                <span>{stg.description}</span>
                {idx === step && (
                  <span style={{ marginLeft:'auto', flexShrink:0, color:'#ef4444', animation:'statusBeacon 0.8s infinite' }}>[ACTIVE]</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ═══ DEFENSE PLAYBOOK + PROPERTIES ═══ */}
      {cur && (
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'16px' }}>
          <div style={{ ...card, borderLeft:'4px solid var(--color-cyan)' }}>
            <div style={{ display:'flex', alignItems:'center', gap:'8px', marginBottom:'12px' }}>
              <Shield size={16} color="var(--color-cyan)"/>
              <h4 style={{ margin:0, fontSize:'.88rem' }}>Cyber Defense Interception Playbook</h4>
            </div>
            <ul style={{ listStyle:'none', padding:0, margin:0, display:'flex', flexDirection:'column', gap:'6px' }}>
              {['Isolate affected host immediately','Block IOCs at firewall/proxy layer','Revoke compromised credentials','Initiate incident response plan','Preserve forensic evidence (memory + disk)'].map((m,i) => (
                <li key={i} style={{ display:'flex', alignItems:'flex-start', gap:'8px', padding:'7px 10px', borderRadius:'var(--radius-sm)', background:'var(--color-bg-elevated)', fontSize:'.78rem' }}>
                  <AlertTriangle size={13} color="var(--color-amber)" style={{flexShrink:0,marginTop:'2px'}}/> {m}
                </li>
              ))}
            </ul>
          </div>
          <div style={{ ...card, borderLeft:'4px solid var(--color-purple)' }}>
            <div style={{ display:'flex', alignItems:'center', gap:'8px', marginBottom:'12px' }}>
              <Eye size={16} color="var(--color-purple)"/>
              <h4 style={{ margin:0, fontSize:'.88rem' }}>Current Node Properties</h4>
            </div>
            <pre style={{ background:'var(--color-bg-elevated)', padding:'10px', borderRadius:'var(--radius-sm)', fontSize:'.7rem', fontFamily:'var(--font-mono)', overflowX:'auto', maxHeight:'200px', overflowY:'auto', margin:0, border:'1px solid var(--color-border)' }}>
{JSON.stringify(cur.node, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}
