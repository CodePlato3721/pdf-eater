import { afterEach, describe, expect, it, vi } from 'vitest'
import { askQuestion, clearHistory, getHistory } from '../../../src/api/chat'

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function stubFetchRoutes(routes: Record<string, () => Response>) {
  vi.stubGlobal('fetch', async (input: RequestInfo | URL) => {
    const url = String(input)
    for (const [path, respond] of Object.entries(routes)) {
      if (url.endsWith(path)) {
        return respond()
      }
    }
    return new Response('Not Found', { status: 404 })
  })
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('askQuestion', () => {
  it('returns the answer text from the backend', async () => {
    stubFetchRoutes({
      '/api/ask': () => jsonResponse({ answer: 'Chapter 1, at the fireplace.' }),
    })

    const answer = await askQuestion('Where does Jo first appear?')

    expect(answer).toBe('Chapter 1, at the fireplace.')
  })

  it('throws an ApiError with the backend detail when no document is loaded', async () => {
    stubFetchRoutes({
      '/api/ask': () =>
        jsonResponse({ detail: 'No document loaded. Upload a PDF first.' }, 409),
    })

    await expect(askQuestion('Where does Jo first appear?')).rejects.toThrowError(
      expect.objectContaining({
        name: 'ApiError',
        message: 'No document loaded. Upload a PDF first.',
        status: 409,
      }),
    )
  })
})

describe('getHistory', () => {
  it('returns the question/answer pairs from the backend', async () => {
    stubFetchRoutes({
      '/api/history': () =>
        jsonResponse({ history: [['Where does Jo first appear?', 'Chapter 1.']] }),
    })

    const history = await getHistory()

    expect(history).toEqual([['Where does Jo first appear?', 'Chapter 1.']])
  })

  it('throws an ApiError when the history fetch fails', async () => {
    stubFetchRoutes({
      '/api/history': () => jsonResponse({ detail: 'boom' }, 500),
    })

    await expect(getHistory()).rejects.toThrowError(
      expect.objectContaining({ name: 'ApiError', message: 'boom', status: 500 }),
    )
  })
})

describe('clearHistory', () => {
  it('resolves when the backend clears the history', async () => {
    stubFetchRoutes({
      '/api/history': () => jsonResponse({ history: [] }),
    })

    await expect(clearHistory()).resolves.toBeUndefined()
  })

  it('throws an ApiError when the clear request fails', async () => {
    stubFetchRoutes({
      '/api/history': () => jsonResponse({ detail: 'nope' }, 500),
    })

    await expect(clearHistory()).rejects.toThrowError(
      expect.objectContaining({ name: 'ApiError', message: 'nope', status: 500 }),
    )
  })
})
