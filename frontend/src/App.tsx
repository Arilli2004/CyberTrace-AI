import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import MainLayout from '@/layouts/MainLayout'
import AuthLayout from '@/layouts/AuthLayout'
import LoginPage from '@/pages/Login/LoginPage'
import DashboardPage from '@/pages/Dashboard/DashboardPage'
import CasesPage from '@/pages/Cases/CasesPage'
import EvidencePage from '@/pages/Evidence/EvidencePage'
import TimelinePage from '@/pages/Timeline/TimelinePage'
import AlertsPage from '@/pages/Alerts/AlertsPage'
import ReportsPage from '@/pages/Reports/ReportsPage'
import AIAssistantPage from '@/pages/AIAssistant/AIAssistantPage'
import SettingsPage from '@/pages/Settings/SettingsPage'
import KnowledgeGraphPage from '@/pages/Graph/KnowledgeGraphPage'
import ValidationPage from '@/pages/Validation/ValidationPage'
import InvestigationDashboardPage from '@/pages/Investigation/InvestigationDashboardPage'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token)
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      {/* Auth Routes */}
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage />} />
      </Route>

      {/* Protected App Routes */}
      <Route
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/cases" element={<CasesPage />} />
        <Route path="/evidence" element={<EvidencePage />} />
        <Route path="/evidence/:caseId" element={<EvidencePage />} />
        <Route path="/graph" element={<KnowledgeGraphPage />} />
        <Route path="/graph/:caseId" element={<KnowledgeGraphPage />} />
        <Route path="/investigation" element={<InvestigationDashboardPage />} />
        <Route path="/investigation/:caseId" element={<InvestigationDashboardPage />} />
        <Route path="/validation" element={<ValidationPage />} />
        <Route path="/validation/:caseId" element={<ValidationPage />} />
        <Route path="/timeline/:caseId" element={<TimelinePage />} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/ai-assistant" element={<AIAssistantPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
