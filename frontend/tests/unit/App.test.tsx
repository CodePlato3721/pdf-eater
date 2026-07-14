import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from '../../src/App'

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

describe('App layout shell', () => {
  it('renders the documents sidebar', async () => {
    stubFetchRoutes({
      '/api/status': () => jsonResponse({ loaded: false, files: [] }),
    })

    render(<App />)

    const sidebar = screen.getByRole('complementary', { name: 'Uploaded documents' })
    expect(sidebar).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Documents' })).toBeInTheDocument()
    expect(
      await screen.findByText('No documents uploaded yet.'),
    ).toBeInTheDocument()
  })

  it('renders the chat area with a question input', () => {
    stubFetchRoutes({
      '/api/status': () => jsonResponse({ loaded: false, files: [] }),
    })

    render(<App />)

    const chatArea = screen.getByRole('region', { name: 'Chat' })
    expect(chatArea).toBeInTheDocument()
    expect(
      screen.getByPlaceholderText('Ask a question about your PDFs…'),
    ).toBeInTheDocument()
  })
})

describe('Documents view', () => {
  it('lists already-uploaded PDFs from the backend in the sidebar', async () => {
    stubFetchRoutes({
      '/api/status': () =>
        jsonResponse({ loaded: true, files: ['little-women.pdf', 'moby-dick.pdf'] }),
    })

    render(<App />)

    expect(await screen.findByText('little-women.pdf')).toBeInTheDocument()
    expect(screen.getByText('moby-dick.pdf')).toBeInTheDocument()
    expect(screen.queryByText('No documents uploaded yet.')).not.toBeInTheDocument()
  })

  it('uploads an attached PDF and refreshes the sidebar', async () => {
    stubFetchRoutes({
      '/api/status': () => jsonResponse({ loaded: false, files: [] }),
      '/api/upload': () => jsonResponse({ loaded: true, files: ['little-women.pdf'] }),
    })

    render(<App />)

    await userEvent.upload(screen.getByLabelText('Attach PDFs'), pdfFile)

    expect(await screen.findByText('little-women.pdf')).toBeInTheDocument()
    expect(screen.queryByText('No documents uploaded yet.')).not.toBeInTheDocument()
  })

  it('shows an uploading indicator and disables attaching while the upload is in flight', async () => {
    let resolveUpload!: (response: Response) => void
    stubFetchRoutes({
      '/api/status': () => jsonResponse({ loaded: false, files: [] }),
      '/api/upload': () =>
        new Promise<Response>((resolve) => {
          resolveUpload = resolve
        }),
    })

    render(<App />)

    await userEvent.upload(screen.getByLabelText('Attach PDFs'), pdfFile)

    expect(await screen.findByRole('status')).toHaveTextContent('Uploading…')
    expect(screen.getByRole('button', { name: '📎 Attach PDFs' })).toBeDisabled()

    resolveUpload(jsonResponse({ loaded: true, files: ['little-women.pdf'] }))

    await waitFor(() => {
      expect(screen.queryByRole('status')).not.toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: '📎 Attach PDFs' })).toBeEnabled()
  })

  it('shows the backend error message when the upload fails', async () => {
    stubFetchRoutes({
      '/api/status': () => jsonResponse({ loaded: false, files: [] }),
      '/api/upload': () =>
        jsonResponse({ detail: 'Could not read PDF: little-women.pdf' }, 422),
    })

    render(<App />)

    await userEvent.upload(screen.getByLabelText('Attach PDFs'), pdfFile)

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Could not read PDF: little-women.pdf',
    )
    expect(screen.getByText('No documents uploaded yet.')).toBeInTheDocument()
  })
})
