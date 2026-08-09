import { useState } from 'react'
import { User, Key, Monitor, Brain } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import toast from 'react-hot-toast'

export default function SettingsPage() {
  const { user } = useAuthStore()
  const [openaiKey, setOpenaiKey] = useState('')
  const [theme, setTheme] = useState('dark')
  const [model, setModel] = useState('gpt-4o')

  const handleSave = () => toast.success('Settings saved')

  return (
    <div className="animate-slide-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="page-subtitle">Configure platform preferences and integrations</p>
        </div>
      </div>

      <div className="grid-2" style={{ gap: '20px' }}>
        {/* Profile */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
            <User size={20} color="var(--color-accent)" />
            <h3 style={{ margin: 0 }}>Profile Settings</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div className="input-group">
              <label className="input-label">Full Name</label>
              <input id="settings-name" className="input" defaultValue={user?.name || ''} />
            </div>
            <div className="input-group">
              <label className="input-label">Email</label>
              <input id="settings-email" className="input" defaultValue={user?.email || ''} type="email" />
            </div>
            <div className="input-group">
              <label className="input-label">Role</label>
              <input className="input" value={user?.role || 'investigator'} disabled style={{ opacity: 0.6 }} />
            </div>
            <button className="btn btn-primary btn-sm" onClick={handleSave}>Save Profile</button>
          </div>
        </div>

        {/* AI Settings */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
            <Brain size={20} color="var(--color-purple)" />
            <h3 style={{ margin: 0 }}>AI Configuration</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div className="input-group">
              <label className="input-label">OpenAI API Key</label>
              <input id="settings-openai-key" className="input" type="password" value={openaiKey} onChange={(e) => setOpenaiKey(e.target.value)} placeholder="sk-..." />
            </div>
            <div className="input-group">
              <label className="input-label">AI Model</label>
              <select id="settings-ai-model" className="input" value={model} onChange={(e) => setModel(e.target.value)}>
                <option value="gpt-4o">GPT-4o (Recommended)</option>
                <option value="gpt-4-turbo">GPT-4 Turbo</option>
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
              </select>
            </div>
            <button className="btn btn-primary btn-sm" onClick={handleSave}>Save AI Settings</button>
          </div>
        </div>

        {/* Appearance */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
            <Monitor size={20} color="var(--color-cyan)" />
            <h3 style={{ margin: 0 }}>Appearance</h3>
          </div>
          <div className="input-group">
            <label className="input-label">Theme</label>
            <select id="settings-theme" className="input" value={theme} onChange={(e) => setTheme(e.target.value)}>
              <option value="dark">Dark (Cyber)</option>
              <option value="darker">Darker (Pure Black)</option>
            </select>
          </div>
        </div>

        {/* Password */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
            <Key size={20} color="var(--color-amber)" />
            <h3 style={{ margin: 0 }}>Change Password</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div className="input-group">
              <label className="input-label">Current Password</label>
              <input id="settings-current-password" className="input" type="password" placeholder="••••••••" />
            </div>
            <div className="input-group">
              <label className="input-label">New Password</label>
              <input id="settings-new-password" className="input" type="password" placeholder="••••••••" />
            </div>
            <button className="btn btn-secondary btn-sm" onClick={handleSave}>Update Password</button>
          </div>
        </div>
      </div>
    </div>
  )
}
