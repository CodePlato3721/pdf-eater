import { API_BASE_URL, parseJsonResponse } from './client'

export type HistoryPair = [question: string, answer: string]

interface HistoryResponse {
  history: HistoryPair[]
}

interface AskResponse {
  answer: string
}

export async function askQuestion(question: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })
  const body = await parseJsonResponse<AskResponse>(response)
  return body.answer
}

export async function getHistory(): Promise<HistoryPair[]> {
  const response = await fetch(`${API_BASE_URL}/api/history`)
  const body = await parseJsonResponse<HistoryResponse>(response)
  return body.history
}

export async function clearHistory(): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/history`, {
    method: 'DELETE',
  })
  await parseJsonResponse<HistoryResponse>(response)
}
