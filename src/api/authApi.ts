import { API_BASE_PATH } from './apiBase'

export interface RegisterPayload {
  email: string
  password: string
  nickname?: string
}

export interface LoginPayload {
  email: string
  password: string
}

export interface AuthUserProfile {
  id: number
  email: string
  nickname?: string | null
  status: string
}

function withJsonHeaders(init: RequestInit = {}): RequestInit {
  return {
    ...init,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(init.headers || {}),
    },
  }
}

export function postRegister(payload: RegisterPayload, signal?: AbortSignal): Promise<Response> {
  return fetch(`${API_BASE_PATH}/auth/register`, withJsonHeaders({ method: 'POST', body: JSON.stringify(payload), signal }))
}

export function postLogin(payload: LoginPayload, signal?: AbortSignal): Promise<Response> {
  return fetch(`${API_BASE_PATH}/auth/login`, withJsonHeaders({ method: 'POST', body: JSON.stringify(payload), signal }))
}

export function postLogout(signal?: AbortSignal): Promise<Response> {
  return fetch(`${API_BASE_PATH}/auth/logout`, { method: 'POST', credentials: 'include', signal })
}

export function getMe(signal?: AbortSignal): Promise<Response> {
  return fetch(`${API_BASE_PATH}/auth/me`, { method: 'GET', credentials: 'include', headers: { Accept: 'application/json' }, signal })
}
