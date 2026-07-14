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

// Routes are keyed as 'METHOD /path' because GET and DELETE share /api/history.
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

const pdfFile = new File(['%PDF-1.4'], 'little-women.pdf', {
  type: 'application/pdf',
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('App layout shell', () => {
  it('renders the documents sidebar', async () => {
    stubFetchRoutes({
      'GET /api/status': () => jsonResponse({ loaded: false, files: [] }),
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
      'GET /api/status': () => jsonResponse({ loaded: false, files: [] }),
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
      'GET /api/status': () =>
        jsonResponse({ loaded: true, files: ['little-women.pdf', 'moby-dick.pdf'] }),
    })

    render(<App />)

    expect(await screen.findByText('little-women.pdf')).toBeInTheDocument()
    expect(screen.getByText('moby-dick.pdf')).toBeInTheDocument()
    expect(screen.queryByText('No documents uploaded yet.')).not.toBeInTheDocument()
  })

  it('uploads an attached PDF and refreshes the sidebar', async () => {
    stubFetchRoutes({
      'GET /api/status': () => jsonResponse({ loaded: false, files: [] }),
      'POST /api/upload': () => jsonResponse({ loaded: true, files: ['little-women.pdf'] }),
    })

    render(<App />)

    await userEvent.upload(screen.getByLabelText('Attach PDFs'), pdfFile)

    expect(await screen.findByText('little-women.pdf')).toBeInTheDocument()
    expect(screen.queryByText('No documents uploaded yet.')).not.toBeInTheDocument()
  })

  it('shows an uploading indicator and disables attaching while the upload is in flight', async () => {
    let resolveUpload!: (response: Response) => void
    stubFetchRoutes({
      'GET /api/status': () => jsonResponse({ loaded: false, files: [] }),
      'POST /api/upload': () =>
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
      'GET /api/status': () => jsonResponse({ loaded: false, files: [] }),
      'POST /api/upload': () =>
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

describe('Chat Q&A view', () => {
  it('renders the restored conversation history in the chat window', async () => {
    stubFetchRoutes({
      'GET /api/status': () =>
        jsonResponse({ loaded: true, files: ['little-women.pdf'] }),
      'GET /api/history': () =>
        jsonResponse({ history: [['Where does Jo first appear?', 'Chapter 1.']] }),
    })

    render(<App />)

    expect(await screen.findByText('Where does Jo first appear?')).toBeInTheDocument()
    expect(screen.getByText('Chapter 1.')).toBeInTheDocument()
    expect(
      screen.queryByText('Upload a PDF and ask a question to get started.'),
    ).not.toBeInTheDocument()
  })

  it('disables the question input while no document is loaded', async () => {
    stubFetchRoutes({
      'GET /api/status': () => jsonResponse({ loaded: false, files: [] }),
      'GET /api/history': () => jsonResponse({ history: [] }),
    })

    render(<App />)

    expect(await screen.findByText('No documents uploaded yet.')).toBeInTheDocument()
    expect(screen.getByLabelText('Question')).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Send' })).toBeDisabled()
    expect(
      screen.getByText('Upload a PDF and ask a question to get started.'),
    ).toBeInTheDocument()
  })

  it('sends a question and shows the answer in the chat window', async () => {
    stubFetchRoutes({
      'GET /api/status': () =>
        jsonResponse({ loaded: true, files: ['little-women.pdf'] }),
      'GET /api/history': () => jsonResponse({ history: [] }),
      'POST /api/ask': () => jsonResponse({ answer: 'Chapter 1, at the fireplace.' }),
    })

    render(<App />)
    await screen.findByText('little-women.pdf')

    await userEvent.type(
      screen.getByLabelText('Question'),
      'Where does Jo first appear?',
    )
    await userEvent.click(screen.getByRole('button', { name: 'Send' }))

    expect(await screen.findByText('Chapter 1, at the fireplace.')).toBeInTheDocument()
    expect(screen.getByText('Where does Jo first appear?')).toBeInTheDocument()
    expect(screen.getByLabelText('Question')).toHaveValue('')
  })

  it('shows a thinking indicator and disables sending while the answer is in flight', async () => {
    let resolveAsk!: (response: Response) => void
    stubFetchRoutes({
      'GET /api/status': () =>
        jsonResponse({ loaded: true, files: ['little-women.pdf'] }),
      'GET /api/history': () => jsonResponse({ history: [] }),
      'POST /api/ask': () =>
        new Promise<Response>((resolve) => {
          resolveAsk = resolve
        }),
    })

    render(<App />)
    await screen.findByText('little-women.pdf')

    await userEvent.type(
      screen.getByLabelText('Question'),
      'Where does Jo first appear?',
    )
    await userEvent.click(screen.getByRole('button', { name: 'Send' }))

    expect(await screen.findByRole('status')).toHaveTextContent('Thinking…')
    expect(screen.getByRole('button', { name: 'Send' })).toBeDisabled()

    resolveAsk(jsonResponse({ answer: 'Chapter 1.' }))

    expect(await screen.findByText('Chapter 1.')).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.queryByRole('status')).not.toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: 'Send' })).toBeEnabled()
  })

  it('shows the backend error message when the ask fails', async () => {
    stubFetchRoutes({
      'GET /api/status': () =>
        jsonResponse({ loaded: true, files: ['little-women.pdf'] }),
      'GET /api/history': () => jsonResponse({ history: [] }),
      'POST /api/ask': () =>
        jsonResponse({ detail: 'No document loaded. Upload a PDF first.' }, 409),
    })

    render(<App />)
    await screen.findByText('little-women.pdf')

    await userEvent.type(
      screen.getByLabelText('Question'),
      'Where does Jo first appear?',
    )
    await userEvent.click(screen.getByRole('button', { name: 'Send' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No document loaded. Upload a PDF first.',
    )
    expect(screen.getByText('Where does Jo first appear?')).toBeInTheDocument()
  })

  it('clears the conversation via the clear-history action', async () => {
    stubFetchRoutes({
      'GET /api/status': () =>
        jsonResponse({ loaded: true, files: ['little-women.pdf'] }),
      'GET /api/history': () =>
        jsonResponse({ history: [['Where does Jo first appear?', 'Chapter 1.']] }),
      'DELETE /api/history': () => jsonResponse({ history: [] }),
    })

    render(<App />)
    await screen.findByText('Where does Jo first appear?')

    await userEvent.click(screen.getByRole('button', { name: 'Clear history' }))

    await waitFor(() => {
      expect(screen.queryByText('Where does Jo first appear?')).not.toBeInTheDocument()
    })
    expect(
      screen.getByText('Upload a PDF and ask a question to get started.'),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Clear history' })).toBeDisabled()
  })
})
