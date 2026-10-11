import axios from 'axios'
import type { AdminListResponse, AuthUser, DataRow, HealthResult, LogicalTable, LoginResponse, QueryEvent, QueryResponse } from '@/types'

export const coordinatorUrl = import.meta.env.VITE_COORDINATOR_API || 'http://127.0.0.1:8000'

export const nodeApis = {
  coordinator: coordinatorUrl,
  site1: import.meta.env.VITE_SITE1_API || 'http://127.0.0.1:8001',
  site2: import.meta.env.VITE_SITE2_API || 'http://127.0.0.1:8002',
  site3: import.meta.env.VITE_SITE3_API || 'http://127.0.0.1:8003',
} as const

const client = axios.create({
  baseURL: coordinatorUrl,
  timeout: 20_000,
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('library_access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export async function login(username: string, password: string): Promise<LoginResponse> {
  const { data } = await client.post<LoginResponse>('/api/auth/login', { username, password })
  return data
}

export async function getCurrentUser(): Promise<AuthUser> {
  const { data } = await client.get<AuthUser>('/api/auth/me')
  return data
}

export async function searchPublicBooks(q = '', categoryId?: number, libraryId?: number): Promise<{ rows: DataRow[]; row_count: number }> {
  const { data } = await client.get('/api/public/books', { params: { q, category_id: categoryId, library_id: libraryId } })
  return data
}

export async function getCatalogOptions(): Promise<{ categories: DataRow[]; libraries: DataRow[] }> {
  const { data } = await client.get('/api/public/catalog-options')
  return data
}

export async function getBookDetail(bookId: number): Promise<{ book: DataRow; copies: DataRow[]; schools: string[]; copy_count: number; available_count: number }> {
  const { data } = await client.get(`/api/public/books/${bookId}`)
  return data
}

export async function getPublicLibraries(): Promise<{ rows: DataRow[]; row_count: number }> {
  const { data } = await client.get('/api/public/libraries')
  return data
}

export async function getNearbyLibraries(longitude: number, latitude: number, radiusKm: number): Promise<{ rows: DataRow[]; row_count: number; radius_km: number }> {
  const { data } = await client.get('/api/public/libraries/nearby', { params: { longitude, latitude, radius_km: radiusKm } })
  return data
}

export async function getMyBorrowings(): Promise<{ rows: DataRow[]; row_count: number; reader_id: number }> {
  const { data } = await client.get('/api/portal/me/borrowings')
  return data
}

export async function getAdminOverview(siteId?: number): Promise<Record<string, number | number[]>> {
  const { data } = await client.get('/api/admin/overview', { params: siteId ? { site_id: siteId } : {} })
  return data
}

export async function getAdminGis(siteId?: number): Promise<{ site_ids: number[]; sites: DataRow[]; campuses: DataRow[]; libraries: DataRow[] }> {
  const { data } = await client.get('/api/admin/gis', { params: siteId ? { site_id: siteId } : {} })
  return data
}

export type AdminResourceKind = 'readers' | 'copies' | 'borrow-records' | 'libraries'
export async function getAdminResources(kind: AdminResourceKind, siteId?: number): Promise<AdminListResponse> {
  const { data } = await client.get<AdminListResponse>(`/api/admin/${kind}`, { params: siteId ? { site_id: siteId } : {} })
  return data
}

export async function getAdminMetadata(siteId?: number): Promise<Record<string, DataRow[] | number[]>> {
  const { data } = await client.get('/api/admin/metadata', { params: siteId ? { site_id: siteId } : {} })
  return data
}

export async function createAdminResource(kind: AdminResourceKind, siteId: number, payload: Record<string, unknown>): Promise<DataRow> {
  const { data } = await client.post(`/api/admin/${kind}`, payload, { params: { site_id: siteId } })
  return data
}

export async function updateAdminResource(kind: AdminResourceKind, id: number, siteId: number, payload: Record<string, unknown>): Promise<DataRow> {
  const { data } = await client.patch(`/api/admin/${kind}/${id}`, payload, { params: { site_id: siteId } })
  return data
}

export async function deleteAdminResource(kind: AdminResourceKind, id: number, siteId: number): Promise<DataRow> {
  const { data } = await client.delete(`/api/admin/${kind}/${id}`, { params: { site_id: siteId } })
  return data
}

export async function updateAdminReader(readerId: number, siteId: number, update: Record<string, unknown>): Promise<DataRow> {
  const { data } = await client.patch(`/api/admin/readers/${readerId}`, update, { params: { site_id: siteId } })
  return data
}

export async function updateAdminCopy(copyId: number, siteId: number, update: Record<string, unknown>): Promise<DataRow> {
  const { data } = await client.patch(`/api/admin/copies/${copyId}`, update, { params: { site_id: siteId } })
  return data
}

export async function executeSql(sql: string): Promise<QueryResponse> {
  const { data } = await client.post<QueryResponse>('/api/query', { sql })
  return data
}

export async function getLogicalSchema(): Promise<LogicalTable[]> {
  const { data } = await client.get<{ tables: LogicalTable[] }>('/api/logical-schema')
  return data.tables
}

export async function getHealth(api = coordinatorUrl): Promise<HealthResult> {
  const { data } = await axios.get<HealthResult>(`${api}/health`, { timeout: 3500 })
  return data
}

export async function getEvents(api: string): Promise<QueryEvent[]> {
  const { data } = await axios.get<QueryEvent[]>(`${api}/api/events`, { timeout: 5000 })
  return data
}

export function websocketUrl(api: string): string {
  return `${api.replace(/^http/, 'ws')}/ws/events`
}

export function apiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (error.code === 'ECONNABORTED') return '请求超时，请检查后端服务和数据库状态。'
    if (!error.response) return '无法连接后端服务，请确认服务已启动。'
    return `请求失败（HTTP ${error.response.status}）`
  }
  return error instanceof Error ? error.message : '发生未知错误。'
}
