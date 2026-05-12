import { API_BASE_PATH } from './apiBase'

export interface ResumeSummaryPayload {
  id: number
  title: string
  updatedAt?: string | null
}

export interface ResumePayload {
  id?: number | null
  title: string
  content: Record<string, unknown>
  updatedAt?: string | null
}

export function listResumes(signal?: AbortSignal): Promise<Response> {
  return fetch(`${API_BASE_PATH}/resumes`, {
    method: 'GET',
    credentials: 'include',
    headers: { Accept: 'application/json' },
    signal,
  })
}

export function createResume(payload: { title: string; content: Record<string, unknown> }, signal?: AbortSignal): Promise<Response> {
  return fetch(`${API_BASE_PATH}/resumes`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(payload),
    signal,
  })
}

export function getResumeById(resumeId: number, signal?: AbortSignal): Promise<Response> {
  return fetch(`${API_BASE_PATH}/resumes/${resumeId}`, {
    method: 'GET',
    credentials: 'include',
    headers: { Accept: 'application/json' },
    signal,
  })
}

export function updateResumeById(resumeId: number, payload: { title: string; content: Record<string, unknown> }, signal?: AbortSignal): Promise<Response> {
  return fetch(`${API_BASE_PATH}/resumes/${resumeId}`, {
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

export function deleteResumeById(resumeId: number, signal?: AbortSignal): Promise<Response> {
  return fetch(`${API_BASE_PATH}/resumes/${resumeId}`, {
    method: 'DELETE',
    credentials: 'include',
    signal,
  })
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
