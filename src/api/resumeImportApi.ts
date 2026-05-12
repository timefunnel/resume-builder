import { API_BASE_PATH } from './apiBase'

export interface ResumeImportAiResponse {
  title: string
  content: Record<string, unknown>
  extractedText: string
}

export async function importResumeWithAi(file: File, signal?: AbortSignal): Promise<Response> {
  const form = new FormData()
  form.append('file', file)
  return fetch(`${API_BASE_PATH}/resumes/import-ai`, {
    method: 'POST',
    credentials: 'include',
    body: form,
    signal,
  })
}
