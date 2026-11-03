import axios from 'axios'
import { useAuthStore } from '@/store/authStore'
import type {
  CaseItem,
  CaseListResponse,
  DashboardStatsResponse,
  EvidenceItem,
  EvidenceListResponse,
  ChainOfCustodyLog,
  ParserStatusResponse,
  EventListResponse,
  EventItem,
  NormalizationStatusResponse,
  NormalizedEventListResponse,
  NormalizedEventItem,
  GraphPayloadResponse,
  GraphStatisticsResponse,
  GraphBuildResponse,
  CSPValidateResponse,
  CSPResultsResponse,
  TimelineResponse,
  AIAnalyzeResponse,
  AIReportResponse,
  AIChatHistoryResponse,
  ReportItem,
} from '@/types/api'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: { 'Content-Type': 'application/json' },
})

// Attach token to every request
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 globally
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// ─── Auth ─────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  register: (data: { name: string; email: string; password: string; role?: string }) =>
    api.post('/auth/register', data),
  profile: () => api.get('/auth/profile'),
}

// ─── Cases ────────────────────────────────────────────────────────────────────
export const casesApi = {
  getDashboardStats: () => api.get<DashboardStatsResponse>('/cases/stats/dashboard'),
  list: (params?: { skip?: number; limit?: number; status?: string }) =>
    api.get<CaseListResponse>('/cases/', { params }),
  create: (data: { title: string; description?: string; priority?: string }) =>
    api.post<CaseItem>('/cases/', data),
  get: (id: number) => api.get<CaseItem>(`/cases/${id}`),
  update: (id: number, data: Partial<{ title: string; description: string; status: string; priority: string }>) =>
    api.put<CaseItem>(`/cases/${id}`, data),
  delete: (id: number) => api.delete<{ message: string }>(`/cases/${id}`),
}

// ─── Evidence ─────────────────────────────────────────────────────────────────
export const evidenceApi = {
  upload: (caseId: number, files: File[]) => {
    const form = new FormData()
    form.append('case_id', String(caseId))
    files.forEach((f) => form.append('files', f))
    return api.post<EvidenceItem[]>('/evidence/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  list: (params?: { skip?: number; limit?: number; search?: string; file_type?: string }) =>
    api.get<EvidenceListResponse>('/evidence/', { params }),
  getCaseEvidence: (caseId: number) => api.get<EvidenceItem[]>(`/evidence/case/${caseId}`),
  get: (id: number) => api.get<EvidenceItem>(`/evidence/${id}`),
  patch: (id: number, data: { description?: string; tags?: string[]; verification_status?: string }) =>
    api.patch<EvidenceItem>(`/evidence/${id}`, data),
  delete: (id: number) => api.delete<{ message: string }>(`/evidence/${id}`),
  download: (id: number) => api.get(`/evidence/download/${id}`, { responseType: 'blob' }),
  getCustody: (id: number) => api.get<ChainOfCustodyLog[]>(`/evidence/${id}/custody`),
}

// ─── Parser & Events ──────────────────────────────────────────────────────────
export const parserApi = {
  parse: (evidenceId: number) => api.post<ParserStatusResponse>(`/parser/parse/${evidenceId}`),
  parseAll: (caseId: number) => api.post<ParserStatusResponse[]>(`/parser/parse-all/${caseId}`),
  getStatus: (evidenceId: number) => api.get<ParserStatusResponse>(`/parser/status/${evidenceId}`),
}

export const eventsApi = {
  listCaseEvents: (caseId: number, params?: { skip?: number; limit?: number; search?: string; severity?: string }) =>
    api.get<EventListResponse>(`/parser/events/case/${caseId}`, { params }),
  getDetails: (eventId: number) => api.get<EventItem>(`/parser/events/${eventId}`),
}

// ─── Normalization Engine ─────────────────────────────────────────────────────
export const normalizationApi = {
  normalize: (evidenceId: number) => api.post<NormalizationStatusResponse>(`/normalize/${evidenceId}`),
  normalizeCase: (caseId: number) => api.post<NormalizationStatusResponse[]>(`/normalize/case/${caseId}`),
  getStatus: (evidenceId: number) => api.get<NormalizationStatusResponse>(`/normalize/status/${evidenceId}`),
  listNormalizedEvents: (caseId: number, params?: { skip?: number; limit?: number; search?: string; category?: string; severity?: string }) =>
    api.get<NormalizedEventListResponse>(`/normalized-events/${caseId}`, { params }),
  getDetail: (eventId: number) => api.get<NormalizedEventItem>(`/normalized-events/detail/${eventId}`),
}

// ─── Knowledge Graph Engine ───────────────────────────────────────────────────
export const graphApi = {
  buildCase: (caseId: number) => api.post<GraphBuildResponse>(`/graph/build/${caseId}`),
  buildEvidence: (evidenceId: number) => api.post<GraphBuildResponse>(`/graph/build/evidence/${evidenceId}`),
  getCaseGraph: (caseId: number) => api.get<GraphPayloadResponse>(`/graph/${caseId}`),
  getStatistics: (caseId: number) => api.get<GraphStatisticsResponse>(`/graph/statistics/${caseId}`),
  deleteGraph: (caseId: number) => api.delete<{ message: string }>(`/graph/${caseId}`),
}

// ─── CSP Reasoning Engine ─────────────────────────────────────────────────────
export const cspApi = {
  validate: (caseId: number) => api.post<CSPValidateResponse>(`/csp/validate/${caseId}`),
  getStatus: (caseId: number) => api.get<CSPValidateResponse>(`/csp/status/${caseId}`),
  getResults: (caseId: number) => api.get<CSPResultsResponse>(`/csp/results/${caseId}`),
  getViolations: (caseId: number) => api.get<unknown[]>(`/csp/violations/${caseId}`),
}

// ─── Timeline ─────────────────────────────────────────────────────────────────
export const timelineApi = {
  get: (caseId: number, params?: { skip?: number; limit?: number; severity?: string }) =>
    api.get<TimelineResponse>(`/timeline/${caseId}`, { params }),
  getSuspicious: (caseId: number) => api.get<TimelineResponse>(`/timeline/${caseId}/suspicious`),
}

// ─── AI ───────────────────────────────────────────────────────────────────────
export const aiApi = {
  analyze: (caseId: number, question?: string) =>
    api.post<AIAnalyzeResponse>('/ai/analyze', { case_id: caseId, question }),
  generateReport: (caseId: number, reportType = 'full') =>
    api.post<AIReportResponse>('/ai/report', { case_id: caseId, report_type: reportType }),
  getChatHistory: (caseId: number) => api.get<AIChatHistoryResponse>(`/ai/chat?case_id=${caseId}`),
}

// ─── Reports ──────────────────────────────────────────────────────────────────
export const reportsApi = {
  list: (caseId: number) => api.get<ReportItem[]>(`/reports/case/${caseId}`),
  download: (reportId: number) => api.get(`/reports/${reportId}/download`, { responseType: 'blob' }),
}
