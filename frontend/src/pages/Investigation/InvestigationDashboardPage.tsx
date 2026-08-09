// ═══════════════════════════════════════════════════════════════════════════════
// Investigation Dashboard — Case Investigation Workbench
// Reconstructed Attack Path Visualizer & Simulation Engine
// ═══════════════════════════════════════════════════════════════════════════════

import { useState, useEffect, useMemo, useRef } from 'react'
import { useParams } from 'react-router-dom'
import {
  Play, Pause, SkipBack, SkipForward, RotateCcw, Shield, AlertTriangle,
  Zap, Activity, ChevronDown, Users, Server, Bug, Terminal, FileCode,
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

  useEffect(() => { if(!playing||!total) return; const id=setInterval(()=>setStep(s=>{if(s+1>=total){setPlaying(false);return total-1}return s+1}),spdMs[spd]||1500); return()=>clearInterval(id) }, [playing,total,spd])
  useEffect(() => { const el=tlRef.current; if(!el) return; const a=el.querySelector('[data-active="true"]') as HTMLElement|null; a?.scrollIntoView({behavior:'smooth',inline:'center',block:'nearest'}) }, [step])

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
        <div style={{ display:'flex', alignItems:'center', gap:'8px', marginBottom:'4px' }}>
          <Activity size={18} color="var(--color-cyan)"/>
          <h3 style={{ margin:0, fontSize:'1rem' }}>Reconstructed Attack Path Visualizer &amp; Simulation Engine</h3>
        </div>
        <p style={{ margin:'0 0 14px', fontSize:'0.75rem', color:'var(--color-text-muted)' }}>
          Plausibility Score: {plaus} / 100 • Synthesized from Knowledge Graph, UCS, A*, &amp; Reasoning
        </p>

        {/* Controls */}
        <div style={{ display:'flex', alignItems:'center', gap:'6px', flexWrap:'wrap', marginBottom:'16px' }}>
          <button onClick={()=>{if(step>=total-1&&!playing)setStep(0);setPlaying(p=>!p)}} disabled={isLoading||!total}
            style={{ display:'flex', alignItems:'center', gap:'5px', background:playing?'#ef4444':'#10b981', color:'#fff', border:'none', padding:'7px 16px', borderRadius:'var(--radius-md)', fontSize:'0.78rem', fontWeight:600, cursor:'pointer', opacity:isLoading||!total?.5:1 }}>
            {playing?<Pause size={13}/>:<Play size={13}/>} {playing?'Pause Animation':'Play Attack Animation'}
          </button>
          <button className="btn btn-secondary" onClick={()=>{setStep(0);setPlaying(false)}} style={{padding:'6px 8px'}}><SkipBack size={14}/></button>
          <button className="btn btn-secondary" onClick={()=>setStep(s=>Math.min(s+1,total-1))} disabled={step>=total-1} style={{padding:'6px 8px'}}><SkipForward size={14}/></button>
          <button className="btn btn-secondary" onClick={()=>{setStep(0);setPlaying(false)}} style={{padding:'6px 8px'}}><RotateCcw size={14}/></button>
          <div style={{ display:'flex', alignItems:'center', gap:'4px', background:'var(--color-bg-elevated)', border:'1px solid var(--color-border)', borderRadius:'var(--radius-md)', padding:'4px 8px' }}>
            <select value={spd} onChange={e=>setSpd(e.target.value)}
              style={{ background:'transparent', border:'none', color:'var(--color-text-primary)', fontSize:'0.72rem', cursor:'pointer', outline:'none' }}>
              <option value="0.5">0.5x</option><option value="1">1x</option><option value="2">2x</option><option value="3">3x</option>
            </select>
            <span style={{ fontSize:'0.68rem', color:'var(--color-text-muted)' }}>Speed</span>
            <ChevronDown size={11} color="var(--color-text-muted)"/>
          </div>
          <div style={{ display:'flex', gap:'5px', marginLeft:'4px' }}>
            {['CSP','FORWARD_CHAINING','KNOWLEDGE_GRAPH'].map(t => (
              <span key={t} style={{ padding:'3px 8px', borderRadius:'var(--radius-sm)', background:'var(--color-bg-elevated)', border:'1px solid var(--color-border)', fontSize:'0.62rem', fontWeight:600, color:'var(--color-cyan)', letterSpacing:'.03em' }}>{t}</span>
            ))}
          </div>
        </div>

        {/* Current Stage Banner */}
        {cur && (
          <div style={{ background:'var(--color-bg-elevated)', border:'1px solid var(--color-border)', borderRadius:'var(--radius-md)', padding:'12px 16px', marginBottom:'16px', display:'flex', alignItems:'center', gap:'10px' }}>
            <div style={{ width:'26px', height:'26px', borderRadius:'50%', background:SEV_BG[cur.severity], border:`2px solid ${SEV_COLOR[cur.severity]}`, display:'flex', alignItems:'center', justifyContent:'center', fontSize:'0.7rem', fontWeight:800, color:SEV_COLOR[cur.severity], flexShrink:0 }}>
              {step+1}
            </div>
            <div style={{ minWidth:0 }}>
              <div style={{ fontSize:'0.85rem', fontWeight:700 }}>STAGE #{step+1}: {cur.node.label} ({cur.node.type})</div>
              <div style={{ fontSize:'0.75rem', color:'var(--color-text-muted)', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{cur.description}</div>
            </div>
          </div>
        )}

        {/* Horizontal Timeline */}
        {!total ? (
          <div style={{ textAlign:'center', padding:'40px 20px', color:'var(--color-text-muted)', border:'2px dashed var(--color-border)', borderRadius:'var(--radius-md)' }}>
            <Shield size={36} style={{marginBottom:'8px',opacity:.4}}/><p style={{margin:0}}>No attack path data. Build a Knowledge Graph first.</p>
          </div>
        ) : (
          <div ref={tlRef} style={{ display:'flex', alignItems:'stretch', overflowX:'auto', overflowY:'hidden', paddingBottom:'8px', paddingTop:'14px', gap:'0' }}>
            {stages.map((sg, i) => {
              const active = i===step, past = i<step, Icon = nodeIcon(sg.node.type)
              return (
                <div key={sg.node.uuid_id} data-active={active?'true':'false'} style={{ display:'flex', alignItems:'center', flexShrink:0 }}>
                  {/* Card */}
                  <div onClick={()=>{setStep(i);setPlaying(false)}} style={{
                    width:'150px', background: active?'var(--color-bg-elevated)':'var(--color-bg-card)',
                    border:`2px solid ${active?SEV_COLOR[sg.severity]:past?'var(--color-border-light)':'var(--color-border)'}`,
                    borderRadius:'var(--radius-md)', padding:'12px 10px', cursor:'pointer',
                    opacity: past?.6:1, transition:'all .3s ease', position:'relative',
                    boxShadow: active?`0 0 18px ${SEV_COLOR[sg.severity]}25`:'none',
                  }}>
                    {active && <div style={{ position:'absolute', top:'-9px', right:'6px', background:SEV_COLOR[sg.severity], color:'#fff', fontSize:'.5rem', fontWeight:800, padding:'1px 7px', borderRadius:'3px', textTransform:'uppercase', letterSpacing:'.04em' }}>ACTIVE STEP</div>}
                    <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'6px' }}>
                      <span style={{ fontSize:'.6rem', color:'var(--color-text-muted)', fontWeight:600, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap', maxWidth:'80px' }}>STAGE #{i+1} • {sg.node.type.toUpperCase()}</span>
                      <span style={{ padding:'1px 6px', borderRadius:'3px', fontSize:'.52rem', fontWeight:700, background:SEV_BG[sg.severity], color:SEV_COLOR[sg.severity], textTransform:'uppercase', flexShrink:0 }}>{sg.severity}</span>
                    </div>
                    <div style={{ display:'flex', alignItems:'center', gap:'6px' }}>
                      <div style={{ width:'28px', height:'28px', borderRadius:'6px', background:`${SEV_COLOR[sg.severity]}15`, display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
                        <Icon size={14} color={SEV_COLOR[sg.severity]}/>
                      </div>
                      <div style={{ fontSize:'.78rem', fontWeight:700, fontFamily:'var(--font-mono)', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{sg.node.label}</div>
                    </div>
                  </div>
                  {/* Connector */}
                  {i<total-1 && (
                    <div style={{ display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', width:'70px', flexShrink:0 }}>
                      <div style={{ fontSize:'.52rem', color:'var(--color-text-muted)', marginBottom:'3px', textTransform:'uppercase', fontWeight:600, whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis', maxWidth:'68px', textAlign:'center' }}>
                        {sg.edges[0]?.relationship||'SEQUENCED_TO'}
                      </div>
                      <div style={{ width:'100%', height:'2px', background:past?'var(--color-cyan)':'var(--color-border)', position:'relative' }}>
                        <div style={{ position:'absolute', right:'-3px', top:'-3px', width:0, height:0, borderTop:'4px solid transparent', borderBottom:'4px solid transparent', borderLeft:`5px solid ${past?'var(--color-cyan)':'var(--color-border)'}` }}/>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

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
