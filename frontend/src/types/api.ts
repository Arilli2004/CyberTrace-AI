/**
 * API Type Definitions for CyberTrace AI
 * Strongly typed response models matching backend schemas
 */

// ─── Case Types ──────────────────────────────────────────────────────────────
export interface CaseItem {
  id: number
  uuid_id?: string
  title: string
  description?: string | null
  investigator_id?: number
  status: string
  priority: string
  is_deleted?: boolean
  created_at?: string | null
  updated_at?: string | null
}

export interface CaseListResponse {
  cases: CaseItem[]
  total: number
  skip?: number
  limit?: number
}

export interface DashboardActivityFeedItem {
  id: number
  action: string
  time: string
  details?: Record<string, unknown>
  severity: string
}

export interface DashboardStatsResponse {
  total_cases: number
  total_evidence: number
  active_alerts: number
  timelines_built: number
  activity_feed: DashboardActivityFeedItem[]
}

// ─── Evidence Types ───────────────────────────────────────────────────────────
export interface EvidenceItem {
  id: number
  uuid_id?: string
  case_id: number
  filename: string
  original_filename?: string
  storage_path?: string
  extension?: string
  mime_type?: string
  size?: number
  sha256?: string
  sha1?: string | null
  md5?: string | null
  file_type?: string
  uploaded_by?: number | null
  uploaded_at?: string | null
  parser_status?: string
  verification_status?: string
  normalization_status?: string
  graph_status?: string
  csp_status?: string
  correlation_status?: string
  timeline_status?: string
  ai_ready?: boolean
  processing_stage?: string
  description?: string | null
  tags?: string[] | null
  chain_of_custody_status?: string
  is_parsed?: boolean
  parse_status?: string
  event_count?: number
  is_deleted?: boolean
  created_at?: string | null
  updated_at?: string | null
}

export interface EvidenceListResponse {
  evidence: EvidenceItem[]
  total: number
  skip?: number
  limit?: number
}

export interface ChainOfCustodyLog {
  id: number
  uuid_id?: string
  evidence_id: number
  user_id?: number | null
  action: string
  details?: Record<string, unknown> | null
  timestamp?: string | null
}

export interface CustodyResponse {
  evidence_id: number
  history: ChainOfCustodyLog[]
}

// ─── Parser & Normalization Types ─────────────────────────────────────────────
export interface ParserStatusResponse {
  evidence_id: number
  filename?: string | null
  parser_status: string
  processing_stage: string
  event_count: number
  is_parsed: boolean
}

export interface EventItem {
  id: number
  uuid_id: string
  evidence_id: number
  case_id?: number | null
  timestamp: string
  source?: string | null
  event_type?: string | null
  event_id?: string | null
  user?: string | null
  host?: string | null
  ip_address?: string | null
  process?: string | null
  file_path?: string | null
  severity: string
  description?: string | null
  raw_data?: unknown
  is_suspicious?: boolean
  confidence_score?: number
  created_at?: string | null
}

export interface EventListResponse {
  events: EventItem[]
  total: number
  skip?: number
  limit?: number
}

export interface NormalizationStatusResponse {
  evidence_id: number
  filename?: string | null
  normalization_status: string
  processing_stage: string
  event_count: number
}

export interface NormalizedEventItem {
  id: number
  uuid_id: string
  event_id?: number | null
  case_id: number
  evidence_id: number
  timestamp_utc: string
  hostname?: string | null
  device_name?: string | null
  username?: string | null
  domain?: string | null
  ip_address?: string | null
  mac_address?: string | null
  process_name?: string | null
  process_id?: string | null
  parent_process?: string | null
  command_line?: string | null
  event_type?: string | null
  event_category?: string
  severity: string
  action: string
  object_name?: string | null
  file_path?: string | null
  registry_key?: string | null
  network_protocol?: string | null
  destination_ip?: string | null
  destination_port?: number | null
  source?: string | null
  confidence_score?: number
  parser_source?: string | null
  normalized?: boolean
  created_at?: string | null
}

export interface NormalizedEventListResponse {
  events: NormalizedEventItem[]
  total: number
  skip?: number
  limit?: number
}

// ─── Knowledge Graph Types ────────────────────────────────────────────────────
export interface GraphNode {
  id?: string
  uuid_id: string
  type: string
  label: string
  properties?: Record<string, unknown>
}

export interface GraphEdge {
  id?: string
  uuid_id?: string
  source: string
  target: string
  type?: string
  relationship?: string
  weight?: number
  confidence?: number
  timestamp?: string | null
  properties?: Record<string, unknown>
}

export interface GraphMetadata {
  case_id?: number
  node_count?: number
  edge_count?: number
  density?: number
  connected_components?: number
}

export interface GraphPayloadResponse {
  case_id?: number
  nodes: GraphNode[]
  edges: GraphEdge[]
  metadata?: GraphMetadata
}

export interface GraphStatisticsResponse {
  case_id?: number
  node_count: number
  edge_count: number
  density?: number
  connected_components?: number
  nodes_by_type?: Record<string, number>
  edges_by_type?: Record<string, number>
}

export interface GraphBuildResponse {
  case_id: number
  status: string
  node_count: number
  edge_count: number
  processing_stage?: string
}

// ─── CSP Reasoning Engine Types ───────────────────────────────────────────────
export interface CSPStatus {
  case_id?: number
  validation_status: string
  validation_score: number
  violations_count: number
  resolved_count: number
  confidence_score: number
}

export interface GraphViolation {
  id: number
  status: string
  violation_reason?: string | null
  resolution_details?: string | null
  confidence: number
}

export interface CSPResultsResponse {
  case_id?: number
  result: CSPStatus
  violations: GraphViolation[]
}

export interface CSPValidateResponse {
  case_id: number
  validation_status: string
  validation_score: number
  violations_count: number
  resolved_count: number
  confidence_score: number
}

// ─── Timeline Types ───────────────────────────────────────────────────────────
export interface TimelineResponse {
  case_id: number
  total: number
  events: EventItem[]
}

// ─── AI Assistant Types ───────────────────────────────────────────────────────
export interface AIAnalyzeResponse {
  case_id: number
  analysis: string
  model?: string
}

export interface AIReportResponse {
  case_id: number
  report: string
  report_id?: number
  model?: string
}

export interface AIChatHistoryResponse {
  case_id: number
  history: Array<{ role: string; content: string; timestamp: string }>
}

// ─── Reports Types ────────────────────────────────────────────────────────────
export interface ReportItem {
  id: number
  case_id: number
  title?: string
  summary?: string
  risk_level?: string
  created_at?: string
}
