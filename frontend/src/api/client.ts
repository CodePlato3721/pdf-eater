export const API_BASE_URL = 'http://localhost:8000'

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function extractErrorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown }
    if (typeof body.detail === 'string') {
      return body.detail
    }
  } catch {
    // Non-JSON error body — fall through to the generic message.
  }
  return `Request failed with status ${response.status}`
}

export async function parseJsonResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new ApiError(await extractErrorMessage(response), response.status)
  }
  return (await response.json()) as T
}
