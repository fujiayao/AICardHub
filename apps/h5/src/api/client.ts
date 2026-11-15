import type { Identity } from './tokens'
import axios from 'axios'
import { mapAssetPaths, withAppBase } from '@/utils/app-path'
import { clearToken, getToken } from './tokens'
export class ApiError extends Error {
 constructor(public code: string, message: string, public status = 0) { super(message) }
}
const client = axios.create({ timeout: 30000 })
export async function request<T>(method: string, path: string, body: unknown, identity: Identity, query?: Record<string, unknown>): Promise<T> {
 try {
  const token = getToken(identity)
  const response = await client.request<T>({ method, url: withAppBase(path), data: mapAssetPaths(body, 'storage'), params: query,
   headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  })
  return mapAssetPaths(response.data)
 } catch (error) {
  if (axios.isAxiosError<{ code?: string, message?: string }>(error)) {
   const status = error.response?.status || 0
   if (status === 401 && identity !== 'public') {
    clearToken(identity)
    if (identity === 'staff') window.dispatchEvent(new Event('staff-session-expired'))
   }
   throw new ApiError(error.response?.data?.code || 'NETWORK_ERROR', error.response?.data?.message || '暂时无法连接服务，请检查网络后重试', status)
  }
  throw error
 }
}
export function errorMessage(error: unknown) { return error instanceof Error ? error.message : '操作失败，请重试' }
