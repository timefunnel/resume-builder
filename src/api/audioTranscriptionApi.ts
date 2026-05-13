import { API_BASE_PATH } from './apiBase'

export interface ChunkTranscriptionResponse {
  sessionId: string
  chunkIndex: number
  text: string
  durationMs?: number | null
  mimeType?: string | null
}

export interface FinalizeChunkPayload {
  chunkIndex: number
  text: string
}

export interface FinalizeTranscriptionResponse {
  sessionId: string
  text: string
  chunkCount: number
}

export async function postAudioTranscriptionChunk(payload: {
  sessionId: string
  chunkIndex: number
  file: Blob
  filename?: string
  durationMs?: number
}): Promise<Response> {
  const form = new FormData()
  form.set('sessionId', payload.sessionId)
  form.set('chunkIndex', String(payload.chunkIndex))
  if (typeof payload.durationMs === 'number' && Number.isFinite(payload.durationMs)) {
    form.set('durationMs', String(Math.max(0, Math.floor(payload.durationMs))))
  }
  form.set('file', payload.file, payload.filename || `chunk-${payload.chunkIndex}.webm`)

  return fetch(`${API_BASE_PATH}/ai/audio/transcriptions/chunk`, {
    method: 'POST',
    body: form,
    credentials: 'include',
  })
}

export async function postAudioTranscriptionFinalize(payload: {
  sessionId: string
  chunks: FinalizeChunkPayload[]
  metadata?: Record<string, unknown>
}): Promise<Response> {
  return fetch(`${API_BASE_PATH}/ai/audio/transcriptions/finalize`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(payload),
  })
}
