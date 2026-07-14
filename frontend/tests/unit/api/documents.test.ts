import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../../../src/api/client'
import { getStatus, uploadPdfs } from '../../../src/api/documents'

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

describe('getStatus', () => {
  it('returns the loaded flag and file list from the backend', async () => {
    stubFetchRoutes({
      '/api/status': () =>
        jsonResponse({ loaded: true, files: ['little-women.pdf'] }),
    })

    const status = await getStatus()

    expect(status).toEqual({ loaded: true, files: ['little-women.pdf'] })
  })

  it('throws an ApiError with the backend detail message on failure', async () => {
    stubFetchRoutes({
      '/api/status': () => jsonResponse({ detail: 'boom' }, 500),
    })

    await expect(getStatus()).rejects.toThrowError(
      expect.objectContaining({ name: 'ApiError', message: 'boom', status: 500 }),
    )
  })

  it('throws a generic ApiError when the error body is not JSON', async () => {
    stubFetchRoutes({
      '/api/status': () => new Response('gateway exploded', { status: 502 }),
    })

    await expect(getStatus()).rejects.toThrowError(
      expect.objectContaining({
        name: 'ApiError',
        message: 'Request failed with status 502',
        status: 502,
      }),
    )
  })
})

describe('uploadPdfs', () => {
  const pdfFile = new File(['%PDF-1.4'], 'little-women.pdf', {
    type: 'application/pdf',
  })

  it('returns the updated status after a successful upload', async () => {
    stubFetchRoutes({
      '/api/upload': () =>
        jsonResponse({ loaded: true, files: ['little-women.pdf'] }),
    })

    const status = await uploadPdfs([pdfFile])

    expect(status).toEqual({ loaded: true, files: ['little-women.pdf'] })
  })

  it('throws an ApiError with the backend detail when the PDF is unreadable', async () => {
    stubFetchRoutes({
      '/api/upload': () =>
        jsonResponse({ detail: 'Could not read PDF: little-women.pdf' }, 422),
    })

    await expect(uploadPdfs([pdfFile])).rejects.toThrowError(
      expect.objectContaining({
        name: 'ApiError',
        message: 'Could not read PDF: little-women.pdf',
        status: 422,
      }),
    )
  })

  it('exposes errors as ApiError instances so callers can branch on status', async () => {
    stubFetchRoutes({
      '/api/upload': () => jsonResponse({ detail: 'nope' }, 422),
    })

    const error = await uploadPdfs([pdfFile]).catch((caught: unknown) => caught)

    expect(error).toBeInstanceOf(ApiError)
  })
})
