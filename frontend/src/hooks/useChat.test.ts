import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useChat } from './useChat'

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function stubFetchRoutes(routes: Record<string, () => Response | Promise<Response>>) {
  vi.stubGlobal('fetch', async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input)
    const method = init?.method ?? 'GET'
    for (const [key, respond] of Object.entries(routes)) {
      const [routeMethod, path] = key.split(' ')
      if (method === routeMethod && url.endsWith(path)) {
        return respond()
      }
    }
    return new Response('Not Found', { status: 404 })
  })
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('useChat', () => {
  it('loads the conversation history from the backend on mount', async () => {
    stubFetchRoutes({
      'GET /api/history': () =>
        jsonResponse({ history: [['Where does Jo first appear?', 'Chapter 1.']] }),
    })

    const { result } = renderHook(() => useChat())

    await waitFor(() => {
      expect(result.current.messages).toEqual([
        { role: 'user', text: 'Where does Jo first appear?' },
        { role: 'assistant', text: 'Chapter 1.' },
      ])
    })
    expect(result.current.thinking).toBe(false)
    expect(result.current.askError).toBeNull()
  })

  it('starts with an empty conversation when the history fetch fails', async () => {
    stubFetchRoutes({
      'GET /api/history': () => jsonResponse({ detail: 'boom' }, 500),
    })

    const { result } = renderHook(() => useChat())

    await waitFor(() => {
      expect(result.current.messages).toEqual([])
    })
    expect(result.current.askError).toBeNull()
  })

  it('appends the question and answer after a successful ask', async () => {
    stubFetchRoutes({
      'GET /api/history': () => jsonResponse({ history: [] }),
      'POST /api/ask': () => jsonResponse({ answer: 'Chapter 1.' }),
    })

    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.ask('Where does Jo first appear?')
    })

    expect(result.current.messages).toEqual([
      { role: 'user', text: 'Where does Jo first appear?' },
      { role: 'assistant', text: 'Chapter 1.' },
    ])
    expect(result.current.thinking).toBe(false)
    expect(result.current.askError).toBeNull()
  })

  it('reports thinking while the answer is in flight', async () => {
    let resolveAsk!: (response: Response) => void
    stubFetchRoutes({
      'GET /api/history': () => jsonResponse({ history: [] }),
      'POST /api/ask': () =>
        new Promise<Response>((resolve) => {
          resolveAsk = resolve
        }),
    })

    const { result } = renderHook(() => useChat())

    act(() => {
      void result.current.ask('Where does Jo first appear?')
    })

    await waitFor(() => {
      expect(result.current.thinking).toBe(true)
    })
    expect(result.current.messages).toEqual([
      { role: 'user', text: 'Where does Jo first appear?' },
    ])

    act(() => {
      resolveAsk(jsonResponse({ answer: 'Chapter 1.' }))
    })

    await waitFor(() => {
      expect(result.current.thinking).toBe(false)
    })
    expect(result.current.messages).toEqual([
      { role: 'user', text: 'Where does Jo first appear?' },
      { role: 'assistant', text: 'Chapter 1.' },
    ])
  })

  it('exposes the backend detail message when the ask fails', async () => {
    stubFetchRoutes({
      'GET /api/history': () => jsonResponse({ history: [] }),
      'POST /api/ask': () =>
        jsonResponse({ detail: 'No document loaded. Upload a PDF first.' }, 409),
    })

    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.ask('Where does Jo first appear?')
    })

    expect(result.current.askError).toBe('No document loaded. Upload a PDF first.')
    expect(result.current.thinking).toBe(false)
    expect(result.current.messages).toEqual([
      { role: 'user', text: 'Where does Jo first appear?' },
    ])
  })

  it('ignores a blank question without contacting the backend', async () => {
    stubFetchRoutes({
      'GET /api/history': () => jsonResponse({ history: [] }),
    })

    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.ask('   ')
    })

    expect(result.current.messages).toEqual([])
    expect(result.current.thinking).toBe(false)
    expect(result.current.askError).toBeNull()
  })

  it('resets the conversation when the history is cleared', async () => {
    stubFetchRoutes({
      'GET /api/history': () =>
        jsonResponse({ history: [['Where does Jo first appear?', 'Chapter 1.']] }),
      'DELETE /api/history': () => jsonResponse({ history: [] }),
    })

    const { result } = renderHook(() => useChat())

    await waitFor(() => {
      expect(result.current.messages).toHaveLength(2)
    })

    await act(async () => {
      await result.current.clearChat()
    })

    expect(result.current.messages).toEqual([])
    expect(result.current.askError).toBeNull()
  })

  it('keeps the conversation and reports an error when clearing fails', async () => {
    stubFetchRoutes({
      'GET /api/history': () =>
        jsonResponse({ history: [['Where does Jo first appear?', 'Chapter 1.']] }),
      'DELETE /api/history': () => jsonResponse({ detail: 'nope' }, 500),
    })

    const { result } = renderHook(() => useChat())

    await waitFor(() => {
      expect(result.current.messages).toHaveLength(2)
    })

    await act(async () => {
      await result.current.clearChat()
    })

    expect(result.current.messages).toHaveLength(2)
    expect(result.current.askError).toBe('nope')
  })
})
