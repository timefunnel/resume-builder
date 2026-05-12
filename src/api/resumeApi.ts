import { API_BASE_PATH } from './apiBase'

export interface ResumePayload {
  id?: number | null
  title: string
  content: Record<string, unknown>
  updatedAt?: string | null
}

export function getCurrentResume(signal?: AbortSignal): Promise<Response> {
  return fetch(`${API_BASE_PATH}/resumes/current`, {
    method: 'GET',
    credentials: 'include',
    headers: { Accept: 'application/json' },
    signal,
  })
}

export function putCurrentResume(payload: { title: string; content: Record<string, unknown> }, signal?: AbortSignal): Promise<Response> {
  return fetch(`${API_BASE_PATH}/resumes/current`, {
    method: 'PUT',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(payload),
    signal,
  })
}
