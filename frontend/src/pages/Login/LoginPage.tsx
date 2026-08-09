import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, EyeOff, LogIn, KeyRound, UserCheck } from 'lucide-react'
import { authApi } from '@/api/client'
import { useAuthStore } from '@/store/authStore'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const setAuth = useAuthStore((s) => s.setAuth)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim() || !password) {
      toast.error('Please enter email and password')
      return
    }

    setLoading(true)
    try {
      const res = await authApi.login(email.trim(), password)
      setAuth(res.data.access_token, res.data.user)
      toast.success(`Welcome back, ${res.data.user.name}!`)
      navigate('/dashboard')
    } catch (err: any) {
      const detail = err.response?.data?.detail
      if (typeof detail === 'string') {
        toast.error(detail)
      } else if (Array.isArray(detail)) {
        toast.error(detail[0]?.msg || 'Invalid login details')
      } else {
        toast.error('Login failed. Please check backend connection.')
      }
    } finally {
      setLoading(false)
    }
  }

  const fillCredentials = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail)
    setPassword(demoPass)
    toast.success(`Loaded credentials for ${demoEmail}`)
  }

  return (
    <div className="animate-slide-in">
      <div style={{ marginBottom: '32px' }}>
        <h2 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '8px' }}>Sign In</h2>
        <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
          Enter your credentials to access the platform
        </p>
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div className="input-group">
          <label htmlFor="login-email" className="input-label">Email Address</label>
          <input
            id="login-email"
            name="email"
            className="input"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="investigator@cybertrace.ai"
            required
            autoComplete="email"
            autoFocus
          />
        </div>

        <div className="input-group">
          <label htmlFor="login-password" className="input-label">Password</label>
          <div style={{ position: 'relative' }}>
            <input
              id="login-password"
              name="password"
              className="input"
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              autoComplete="current-password"
              style={{ paddingRight: '44px' }}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              title={showPassword ? 'Hide password' : 'Show password'}
              style={{
                position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)',
                background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)',
                display: 'flex', alignItems: 'center', padding: '4px',
              }}
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
        </div>

        <button
          id="login-submit"
          type="submit"
          className="btn btn-primary btn-lg"
          disabled={loading}
          style={{ width: '100%', justifyContent: 'center', marginTop: '8px' }}
        >
          {loading ? <div className="spinner" style={{ width: '18px', height: '18px' }} /> : <LogIn size={18} />}
          {loading ? 'Signing in...' : 'Sign In'}
        </button>
      </form>

      {/* Quick Click Demo credentials */}
      <div style={{
        marginTop: '28px',
        padding: '16px',
        background: 'var(--color-bg-elevated)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--color-border)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
          <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', fontWeight: 600, margin: 0 }}>
            Demo Credentials (Click to auto-fill)
          </p>
          <KeyRound size={14} className="text-muted" />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <button
            type="button"
            onClick={() => fillCredentials('admin@cybertrace.ai', 'Admin@123')}
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '8px 12px', background: 'var(--color-bg-card)', border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)', cursor: 'pointer', color: 'var(--color-text-primary)',
              fontSize: '0.8rem', fontFamily: 'var(--font-mono)', textAlign: 'left', transition: 'all 0.2s',
            }}
            onMouseOver={(e) => (e.currentTarget.style.borderColor = 'var(--color-accent)')}
            onMouseOut={(e) => (e.currentTarget.style.borderColor = 'var(--color-border)')}
          >
            <div>
              <span style={{ color: 'var(--color-accent-light)', fontWeight: 600 }}>[Admin]</span> admin@cybertrace.ai
            </div>
            <UserCheck size={14} color="var(--color-cyan)" />
          </button>

          <button
            type="button"
            onClick={() => fillCredentials('investigator@cybertrace.ai', 'Admin@123')}
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '8px 12px', background: 'var(--color-bg-card)', border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)', cursor: 'pointer', color: 'var(--color-text-primary)',
              fontSize: '0.8rem', fontFamily: 'var(--font-mono)', textAlign: 'left', transition: 'all 0.2s',
            }}
            onMouseOver={(e) => (e.currentTarget.style.borderColor = 'var(--color-accent)')}
            onMouseOut={(e) => (e.currentTarget.style.borderColor = 'var(--color-border)')}
          >
            <div>
              <span style={{ color: 'var(--color-emerald)', fontWeight: 600 }}>[Investigator]</span> investigator@cybertrace.ai
            </div>
            <UserCheck size={14} color="var(--color-cyan)" />
          </button>
        </div>
      </div>
    </div>
  )
}

