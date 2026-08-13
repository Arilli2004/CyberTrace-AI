import { useState, useEffect } from 'react'
import { Send, Sparkles, RefreshCw, Cpu, ShieldCheck } from 'lucide-react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { aiApi, casesApi } from '@/api/client'
import toast from 'react-hot-toast'

interface Message { role: 'user' | 'ai'; content: string; timestamp: Date }

export default function AIAssistantPage() {
  const [selectedCase, setSelectedCase] = useState<number | null>(null)
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'ai',
      content: "👋 Hello! I am Gemma AI — your local digital forensics investigation assistant.\n\nSelect a case above and ask me any question about the evidence, suspicious log events, attack vectors, or request a complete forensic report!",
      timestamp: new Date(),
    }
  ])

  const { data: casesData } = useQuery({
    queryKey: ['cases'],
    queryFn: () => casesApi.list({ limit: 50 }),
    select: (res) => res.data?.cases || [],
  })

  // Auto-select first case if available
  useEffect(() => {
    if (casesData && casesData.length > 0 && !selectedCase) {
      setSelectedCase(casesData[0].id)
    }
  }, [casesData, selectedCase])

  const analyzeMutation = useMutation({
    mutationFn: (userQ: string) => aiApi.analyze(selectedCase!, userQ),
    onSuccess: (res) => {
      setMessages((prev) => [
        ...prev,
        { role: 'ai', content: res.data.analysis, timestamp: new Date() }
      ])
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || 'Gemma AI analysis failed'),
  })

  const reportMutation = useMutation({
    mutationFn: () => aiApi.generateReport(selectedCase!),
    onSuccess: (res) => {
      setMessages((prev) => [
        ...prev,
        { role: 'ai', content: `📄 **FULL INVESTIGATION REPORT (Gemma AI)**\n\n${res.data.report}`, timestamp: new Date() }
      ])
      toast.success('Gemma AI Report generated successfully!')
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || 'Report generation failed'),
  })

  const handleSend = (overrideQ?: string) => {
    const textToSend = overrideQ || question
    if (!textToSend.trim()) return
    if (!selectedCase) { toast.error('Please select a case first'); return }

    setMessages((prev) => [...prev, { role: 'user', content: textToSend, timestamp: new Date() }])
    analyzeMutation.mutate(textToSend)
    setQuestion('')
  }

  const isLoading = analyzeMutation.isPending || reportMutation.isPending

  return (
    <div className="animate-slide-in" style={{ height: 'calc(100vh - 112px)', display: 'flex', flexDirection: 'column' }}>
      <div className="page-header" style={{ marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '42px', height: '42px', background: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 16px rgba(6,182,212,0.3)' }}>
            <Cpu size={22} color="white" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h1 className="page-title" style={{ margin: 0 }}>Gemma AI Investigation Assistant</h1>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', padding: '2px 8px', borderRadius: '999px', fontSize: '0.65rem', fontWeight: 800, background: 'rgba(34,197,94,0.15)', color: '#22c55e', border: '1px solid rgba(34,197,94,0.4)' }}>
                <ShieldCheck size={12} /> LM STUDIO (ONLINE)
              </span>
            </div>
            <p className="page-subtitle" style={{ margin: 0 }}>
              Powered by Gemma 4 / LM Studio • Local Private LLM • Real Case Evidence Context
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <select
            id="ai-case-select"
            className="input"
            value={selectedCase || ''}
            onChange={(e) => setSelectedCase(Number(e.target.value) || null)}
            style={{ maxWidth: '280px', fontWeight: 600 }}
          >
            <option value="">— Select a case —</option>
            {casesData?.map((c: any) => (
              <option key={c.id} value={c.id}>Case #{c.id}: {c.title}</option>
            ))}
          </select>

          {selectedCase && (
            <button className="btn btn-primary btn-sm" onClick={() => reportMutation.mutate()} disabled={isLoading} style={{ background: 'var(--gradient-accent)', fontWeight: 700 }}>
              <Sparkles size={16} /> Generate Gemma AI Report
            </button>
          )}
        </div>
      </div>

      {/* Chat Window */}
      <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
        {/* Messages Container */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {messages.map((msg, i) => (
            <div key={i} className={`chat-bubble ${msg.role}`} style={{ maxWidth: '85%', alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
              {msg.role === 'ai' && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px', fontSize: '0.75rem', color: 'var(--color-cyan)', fontWeight: 800 }}>
                  <Cpu size={14} /> Gemma AI (LM Studio)
                </div>
              )}
              <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.7, fontSize: '0.88rem' }}>{msg.content}</div>
              <div style={{ fontSize: '0.68rem', opacity: 0.6, marginTop: '8px', textAlign: msg.role === 'user' ? 'right' : 'left' }}>
                {msg.timestamp.toLocaleTimeString()}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="chat-bubble ai" style={{ alignSelf: 'flex-start' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-cyan)', fontWeight: 600 }}>
                <RefreshCw size={16} style={{ animation: 'spin 1s linear infinite' }} />
                Gemma AI is processing case evidence and generating response...
              </div>
            </div>
          )}
        </div>

        {/* Quick Prompts */}
        <div style={{ padding: '12px 20px', borderTop: '1px solid var(--color-border)', display: 'flex', gap: '8px', flexWrap: 'wrap', background: 'var(--color-bg-card)' }}>
          {[
            'Summarize all suspicious activities in this case',
            'What is the likely attack vector and root cause?',
            'List compromised accounts and hostnames',
            'Recommend digital forensic next steps',
          ].map((promptText) => (
            <button
              key={promptText}
              className="btn btn-ghost btn-sm"
              style={{ fontSize: '0.78rem', background: 'var(--color-bg-elevated)', border: '1px solid var(--color-border)' }}
              onClick={() => { setQuestion(promptText); handleSend(promptText); }}
              disabled={isLoading}
            >
              💡 {promptText}
            </button>
          ))}
        </div>

        {/* Input Area */}
        <div style={{ padding: '16px 20px', borderTop: '1px solid var(--color-border)', display: 'flex', gap: '12px', background: 'var(--color-bg-secondary)' }}>
          <input
            id="ai-question-input"
            className="input"
            style={{ flex: 1, fontSize: '0.88rem' }}
            placeholder="Ask Gemma AI about the case, evidence logs, attack path, or suspicious users..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            disabled={isLoading}
          />
          <button
            id="ai-send-btn"
            className="btn btn-primary"
            onClick={() => handleSend()}
            disabled={!question.trim() || isLoading}
            style={{ background: 'var(--gradient-accent)', fontWeight: 700, padding: '0 20px' }}
          >
            <Send size={18} /> Send
          </button>
        </div>
      </div>
    </div>
  )
}
