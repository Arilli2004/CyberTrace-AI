import { Outlet } from 'react-router-dom'
import { Shield } from 'lucide-react'

export default function AuthLayout() {
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      background: 'var(--color-bg-primary)',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Animated background */}
      <div style={{
        position: 'absolute', inset: 0,
        pointerEvents: 'none',
        zIndex: 0,
        backgroundImage: `
          radial-gradient(circle at 20% 50%, rgba(59, 130, 246, 0.06) 0%, transparent 50%),
          radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.06) 0%, transparent 40%),
          radial-gradient(circle at 60% 80%, rgba(6, 182, 212, 0.04) 0%, transparent 40%)
        `,
      }} />

      {/* Left panel — Branding */}
      <div style={{
        width: '50%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        padding: '60px',
        borderRight: '1px solid var(--color-border)',
        position: 'relative',
        zIndex: 1,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '48px' }}>
          <div style={{
            width: '52px', height: '52px',
            background: 'var(--gradient-cyber)',
            borderRadius: '14px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 30px rgba(6, 182, 212, 0.3)',
          }}>
            <Shield size={26} color="white" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.6rem', fontWeight: 800, margin: 0 }}>CyberTrace AI</h1>
            <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', margin: 0 }}>Digital Forensics Platform</p>
          </div>
        </div>

        <h2 style={{ fontSize: '2.2rem', fontWeight: 700, lineHeight: 1.3, marginBottom: '20px' }}>
          Intelligent Evidence<br />
          <span style={{ background: 'var(--gradient-accent)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Reconstruction
          </span>
        </h2>

        <p style={{ color: 'var(--color-text-secondary)', lineHeight: 1.7, maxWidth: '400px', marginBottom: '40px', fontSize: '0.95rem' }}>
          AI-powered digital forensics platform that automates cyber incident investigation — from evidence collection to professional report generation.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {[
            { icon: '🔍', text: 'Parse EVTX, CSV, JSON, XML, and Linux logs' },
            { icon: '🔗', text: 'AI-powered event correlation & threat detection' },
            { icon: '📊', text: 'Interactive investigation timelines & dashboards' },
            { icon: '🤖', text: 'LLM-assisted analysis and report generation' },
          ].map(({ icon, text }) => (
            <div key={text} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '1.2rem' }}>{icon}</span>
              <span style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)' }}>{text}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Right panel — Auth form */}
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px',
        position: 'relative',
        zIndex: 1,
      }}>
        <div style={{ width: '100%', maxWidth: '420px' }}>
          <Outlet />
        </div>
      </div>
    </div>
  )
}
