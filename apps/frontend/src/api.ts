import type { ArticleType, ResultResponse, StatusResponse, UploadResponse } from '@shared/types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function uploadCsv(file: File): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: 'POST',
    body: formData
  })

  if (!response.ok) {
    throw new Error('Upload failed')
  }

  return response.json()
}

export async function fetchStatus(runId: string): Promise<StatusResponse> {
  const response = await fetch(`${API_BASE_URL}/status/${runId}`)
  if (!response.ok) {
    throw new Error('Status fetch failed')
  }
  return response.json()
}

export async function fetchResult(runId: string): Promise<ResultResponse> {
  const response = await fetch(`${API_BASE_URL}/result/${runId}`)
  if (!response.ok) {
    throw new Error('Result fetch failed')
  }
  return response.json()
}

export function resultDownloadUrl(runId: string): string {
  return `${API_BASE_URL}/result/${runId}?format=md`
}

export async function clearDatabase(): Promise<{ message: string; deleted_runs: number }> {
  const response = await fetch(`${API_BASE_URL}/clear`, {
    method: 'POST'
  })
  if (!response.ok) {
    throw new Error('Clear database failed')
  }
  return response.json()
}

export type DebugResponse = {
  run_id: string
  status: Record<string, unknown>
  stages: Record<string, unknown>
  output: Record<string, unknown> | null
}

export async function fetchDebug(runId: string): Promise<DebugResponse> {
  const response = await fetch(`${API_BASE_URL}/debug/${runId}`)
  if (!response.ok) {
    throw new Error('Debug fetch failed')
  }
  return response.json()
}

export async function fetchArticleTypes(): Promise<ArticleType[]> {
  const response = await fetch(`${API_BASE_URL}/article-types`)
  if (!response.ok) {
    throw new Error('Failed to fetch article types')
  }
  return response.json()
}

export async function createArticleType(name: string, definition: string): Promise<ArticleType> {
  const response = await fetch(`${API_BASE_URL}/article-types`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ name, definition }),
  })
  if (!response.ok) {
    throw new Error('Failed to create article type')
  }
  return response.json()
}

export async function updateArticleType(id: number, name: string, definition: string): Promise<ArticleType> {
  const response = await fetch(`${API_BASE_URL}/article-types/${id}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ name, definition }),
  })
  if (!response.ok) {
    throw new Error('Failed to update article type')
  }
  return response.json()
}

export async function deleteArticleType(id: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/article-types/${id}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    throw new Error('Failed to delete article type')
  }
}
