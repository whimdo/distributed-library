export type DataRow = Record<string, unknown>

export interface QueryEvent {
  query_id: string
  timestamp: string
  source: string
  event_type: string
  message: string
  details: Record<string, unknown>
}

export interface PhysicalQuery {
  target: string
  sql: string
}

export interface QueryResponse {
  query_id: string
  columns: string[]
  rows: DataRow[]
  row_count: number
  selected_sites: number[]
  physical_queries: PhysicalQuery[]
  events: QueryEvent[]
}

export interface LogicalTable {
  logical_name: string
  location: 'coordinator' | 'fragmented'
  columns: string[]
}

export interface HealthResult {
  service: string
  database: string
  status: string
  site_id?: number
}

export interface NodeDefinition {
  key: string
  name: string
  shortName: string
  api: string
  color: string
}

export type UserRole = 'STUDENT' | 'SITE_ADMIN' | 'ADMIN'

export interface AuthUser {
  account_id: number
  username: string
  display_name: string
  role: UserRole
  reader_id: number | null
  home_site_id: number | null
  managed_site_id: number | null
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: AuthUser
}

export interface AdminListResponse {
  site_ids: number[]
  rows: DataRow[]
  row_count: number
}
