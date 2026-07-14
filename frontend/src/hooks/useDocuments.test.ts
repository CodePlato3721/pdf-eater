import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useDocuments } from './useDocuments'

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function stubFetchRoutes(routes: Record<string, () => Response | Promise<Response>>) {
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

const pdfFile = new File(['%PDF-1.4'], 'little-women.pdf', {
  type: 'application/pdf',
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('useDocuments', () => {
  it('loads the uploaded-file list from the backend on mount', async () => {
    stubFetchRoutes({
      '/api/status': () => jsonResponse({ loaded: true, files: ['little-women.pdf'] }),
    })

    const { result } = renderHook(() => useDocuments())

    await waitFor(() => {
      expect(result.current.files).toEqual(['little-women.pdf'])
    })
    expect(result.current.uploading).toBe(false)
    expect(result.current.uploadError).toBeNull()
  })

  it('keeps the file list empty when the status fetch fails', async () => {
    stubFetchRoutes({
      '/api/status': () => jsonResponse({ detail: 'boom' }, 500),
    })

    const { result } = renderHook(() => useDocuments())

    await waitFor(() => {
      expect(result.current.files).toEqual([])
    })
    expect(result.current.uploadError).toBeNull()
  })

  it('updates the file list after a successful upload', async () => {
    stubFetchRoutes({
      '/api/status': () => jsonResponse({ loaded: false, files: [] }),
      '/api/upload': () => jsonResponse({ loaded: true, files: ['little-women.pdf'] }),
    })

    const { result } = renderHook(() => useDocuments())

    await act(async () => {
      await result.current.uploadFiles([pdfFile])
    })

    expect(result.current.files).toEqual(['little-women.pdf'])
    expect(result.current.uploading).toBe(false)
    expect(result.current.uploadError).toBeNull()
  })

  it('reports uploading while the upload is in flight', async () => {
    let resolveUpload!: (response: Response) => void
    stubFetchRoutes({
      '/api/status': () => jsonResponse({ loaded: false, files: [] }),
      '/api/upload': () =>
        new Promise<Response>((resolve) => {
          resolveUpload = resolve
        }),
    })

    const { result } = renderHook(() => useDocuments())

    act(() => {
      void result.current.uploadFiles([pdfFile])
    })

    await waitFor(() => {
      expect(result.current.uploading).toBe(true)
    })

    act(() => {
      resolveUpload(jsonResponse({ loaded: true, files: ['little-women.pdf'] }))
    })

    await waitFor(() => {
      expect(result.current.uploading).toBe(false)
    })
    expect(result.current.files).toEqual(['little-women.pdf'])
  })

  it('exposes the backend detail message when the upload fails', async () => {
    stubFetchRoutes({
      '/api/status': () => jsonResponse({ loaded: false, files: [] }),
      '/api/upload': () =>
        jsonResponse({ detail: 'Could not read PDF: little-women.pdf' }, 422),
    })

    const { result } = renderHook(() => useDocuments())

    await act(async () => {
      await result.current.uploadFiles([pdfFile])
    })

    expect(result.current.uploadError).toBe('Could not read PDF: little-women.pdf')
    expect(result.current.uploading).toBe(false)
    expect(result.current.files).toEqual([])
  })

  it('ignores an empty selection without contacting the backend', async () => {
    stubFetchRoutes({
      '/api/status': () => jsonResponse({ loaded: false, files: [] }),
    })

    const { result } = renderHook(() => useDocuments())

    await act(async () => {
      await result.current.uploadFiles([])
    })

    expect(result.current.uploading).toBe(false)
    expect(result.current.uploadError).toBeNull()
    expect(result.current.files).toEqual([])
  })
})
