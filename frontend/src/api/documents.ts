import { API_BASE_URL, parseJsonResponse } from './client'

export interface DocumentsStatus {
  loaded: boolean
  files: string[]
}

export async function getStatus(): Promise<DocumentsStatus> {
  const response = await fetch(`${API_BASE_URL}/api/status`)
  return parseJsonResponse<DocumentsStatus>(response)
}

export async function uploadPdfs(files: File[]): Promise<DocumentsStatus> {
  const formData = new FormData()
  for (const file of files) {
    formData.append('files', file)
  }
  const response = await fetch(`${API_BASE_URL}/api/upload`, {
    method: 'POST',
    body: formData,
  })
  return parseJsonResponse<DocumentsStatus>(response)
}
