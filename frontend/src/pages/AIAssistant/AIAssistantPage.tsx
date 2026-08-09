import { useState } from 'react'
import { Bot, Send, Sparkles, RefreshCw } from 'lucide-react'
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
      content: "👋 Hello! I'm CyberTrace AI, your digital forensics investigation assistant. Select a case and ask me anything about the evidence, suspicious activities, or get a full investigation report.",
      timestamp: new Date(),
    }
  ])

  const { data: casesData } = useQuery({
    queryKey: ['cases'],
    queryFn: () => casesApi.list({ limit: 50 }),
    select: (res) => res.data?.cases || [],
  })

  const analyzeMutation = useMutation({
    mutationFn: () => aiApi.analyze(selectedCase!, question),
    onSuccess: (res) => {
      setMessages((prev) => [
        ...prev,
        { role: 'ai', content: res.data.analysis, timestamp: new Date() }
      ])
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || 'AI analysis failed'),
  })

  const reportMutation = useMutation({
    mutationFn: () => aiApi.generateReport(selectedCase!),
    onSuccess: (res) => {
      setMessages((prev) => [
        ...prev,
        { role: 'ai', content: `📄 **Investigation Report Generated**\n\n${res.data.report}`, timestamp: new Date() }
      ])
      toast.success('Report generated!')
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || 'Report generation failed'),
  })

  const handleSend = () => {
    if (!question.trim()) return
    if (!selectedCase) { toast.error('Please select a case first'); return }

    setMessages((prev) => [...prev, { role: 'user', content: question, timestamp: new Date() }])
    analyzeMutation.mutate()
    setQuestion('')
  }

  const isLoading = analyzeMutation.isPending || reportMutation.isPending

  return (
    <div className="animate-slide-in" style={{ height: 'calc(100vh - 112px)', display: 'flex', flexDirection: 'column' }}>
      <div className="page-header" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '42px', height: '42px', background: 'var(--gradient-accent)', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Bot size={22} color="white" />
          </div>
          <div>
            <h1 className="page-title">AI Investigation Assistant</h1>
            <p className="page-subtitle">Powered by GPT-4o • Evidence-grounded analysis</p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <select
            id="ai-case-select"
            className="input"
            value={selectedCase || ''}
            onChange={(e) => setSelectedCase(Number(e.target.value) || null)}
            style={{ maxWidth: '260px' }}
          >
            <option value="">— Select a case —</option>
            {casesData?.map((c: any) => (
              <option key={c.id} value={c.id}>{c.title}</option>
            ))}
          </select>

          {selectedCase && (
            <button className="btn btn-secondary btn-sm" onClick={() => reportMutation.mutate()} disabled={isLoading}>
              <Sparkles size={16} /> Generate Report
            </button>
          )}
        </div>
      </div>

      {/* Chat Window */}
      <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
        {/* Messages */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {messages.map((msg, i) => (
            <div key={i} className={`chat-bubble ${msg.role}`}>
              {msg.role === 'ai' && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px', fontSize: '0.75rem', color: 'var(--color-accent-light)', fontWeight: 600 }}>
                  <Bot size={14} /> CyberTrace AI
                </div>
              )}
              <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.7 }}>{msg.content}</div>
              <div style={{ fontSize: '0.7rem', opacity: 0.6, marginTop: '8px' }}>
                {msg.timestamp.toLocaleTimeString()}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="chat-bubble ai">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-text-muted)' }}>
                <RefreshCw size={14} style={{ animation: 'spin 1s linear infinite' }} />
                Analyzing evidence...
              </div>
            </div>
          )}
        </div>

        {/* Quick Prompts */}
        <div style={{ padding: '12px 20px', borderTop: '1px solid var(--color-border)', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {[
            'Summarize suspicious activities',
            'What is the likely attack vector?',
            'Identify the timeline of compromise',
            'What are the recommended next steps?',
          ].map((prompt) => (
            <button key={prompt} className="btn btn-ghost btn-sm" style={{ fontSize: '0.8rem' }} onClick={() => setQuestion(prompt)}>
              {prompt}
            </button>
          ))}
        </div>

        {/* Input Area */}
        <div style={{ padding: '16px 20px', borderTop: '1px solid var(--color-border)', display: 'flex', gap: '12px', background: 'var(--color-bg-secondary)' }}>
          <input
            id="ai-question-input"
            className="input"
            style={{ flex: 1 }}
            placeholder="Ask about the evidence, attack patterns, or request analysis..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            disabled={isLoading}
          />
          <button
            id="ai-send-btn"
            className="btn btn-primary"
            onClick={handleSend}
            disabled={!question.trim() || isLoading}
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  )
}
