// author: jf
import { API_BASE_PATH } from './apiBase'
import type { InterviewTurnRequest } from '@/services/interview/types'

export function getInterviewTurnStreamEndpoint(): string {
  return `${API_BASE_PATH}/ai/interview/turn/stream`
}

export function getInterviewSessionsEndpoint(limit?: number, resumeId?: number | null): string {
  const params = new URLSearchParams()
  if (typeof limit === 'number' && Number.isFinite(limit)) params.set('limit', String(Math.max(1, Math.floor(limit))))
  if (typeof resumeId === 'number' && Number.isFinite(resumeId) && resumeId > 0) params.set('resumeId', String(Math.floor(resumeId)))
  const query = params.toString() ? `?${params.toString()}` : ''
  return `${API_BASE_PATH}/ai/interview/sessions${query}`
}

export function getInterviewSessionDetailEndpoint(sessionId: string): string {
  return `${API_BASE_PATH}/ai/interview/sessions/${encodeURIComponent(sessionId)}`
}

export async function postInterviewTurnStream(
  requestBody: InterviewTurnRequest,
  signal?: AbortSignal
): Promise<Response> {
  return fetch(getInterviewTurnStreamEndpoint(), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/x-ndjson',
    },
    body: JSON.stringify(requestBody),
    signal,
    credentials: 'include',
  })
}

export async function getInterviewSessions(limit = 20, resumeId?: number | null, signal?: AbortSignal): Promise<Response> {
  return fetch(getInterviewSessionsEndpoint(limit, resumeId), {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
    signal,
    credentials: 'include',
  })
}

export async function getInterviewSessionDetail(sessionId: string, signal?: AbortSignal): Promise<Response> {
  return fetch(getInterviewSessionDetailEndpoint(sessionId), {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
    signal,
    credentials: 'include',
  })
}
