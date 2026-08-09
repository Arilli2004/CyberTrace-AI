import { FileText, Download, Sparkles } from 'lucide-react'

const MOCK_REPORTS = [
  { id: 1, case: 'Ransomware Investigation - ACME Corp', type: 'Full Investigation', risk: 'critical', date: '2026-08-02', summary: 'Ransomware attack via phishing email. Lateral movement detected across 5 hosts. 3 TB data encrypted.' },
  { id: 2, case: 'Data Exfiltration - Finance Dept', type: 'Executive Summary', risk: 'high', date: '2026-08-01', summary: 'Unauthorized data transfer of 14GB. Credential theft via keylogger. Source IP: 185.220.101.45.' },
  { id: 3, case: 'Unauthorized Access - HR Systems', type: 'Summary', risk: 'medium', date: '2026-07-31', summary: 'Brute force attack followed by successful login. 2 internal systems accessed without authorization.' },
]

export default function ReportsPage() {
  return (
    <div className="animate-slide-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Investigation Reports</h1>
          <p className="page-subtitle">AI-generated forensic investigation reports</p>
        </div>
        <button className="btn btn-primary btn-sm">
          <Sparkles size={16} /> Generate New Report
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {MOCK_REPORTS.map((report) => (
          <div key={report.id} className="card" style={{ display: 'flex', gap: '20px', alignItems: 'flex-start' }}>
            <div style={{ width: '52px', height: '52px', background: 'rgba(59,130,246,0.1)', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <FileText size={24} color="var(--color-accent)" />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
                <h3 style={{ margin: 0, fontSize: '1rem' }}>{report.case}</h3>
                <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{report.date}</span>
              </div>
              <p style={{ fontSize: '0.875rem', margin: '0 0 12px', lineHeight: 1.6 }}>{report.summary}</p>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <span className="badge badge-info">{report.type}</span>
                <span className={`badge badge-${report.risk}`}>Risk: {report.risk}</span>
              </div>
            </div>
            <button className="btn btn-secondary btn-sm" style={{ flexShrink: 0 }}>
              <Download size={16} /> Download
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
