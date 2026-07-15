import { expect, test, type Page } from '@playwright/test'

// Resolved against the working directory, which is frontend/ because the
// Playwright config lives there.
const PDF_FIXTURE_PATH = 'tests/e2e/fixtures/little-women.pdf'
const PDF_FILE_NAME = 'little-women.pdf'
const QUESTION = 'Where does Jo first appear?'
const ANSWER = 'Chapter 1, grumbling by the fireplace.'

// The frontend calls the backend cross-origin (5173 → 8000), so fulfilled
// responses need CORS headers and preflights an explicit OPTIONS answer.
const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
}

// Stubs the FastAPI backend so the suite drives the real frontend in a real
// browser without a running backend or an OpenAI key.
async function stubBackend(page: Page) {
  await page.route('http://localhost:8000/api/**', async (route) => {
    const request = route.request()
    const method = request.method()
    const path = new URL(request.url()).pathname

    if (method === 'OPTIONS') {
      return route.fulfill({ status: 204, headers: CORS_HEADERS })
    }

    const respondJson = (body: unknown) =>
      route.fulfill({
        status: 200,
        headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

    if (method === 'GET' && path === '/api/status') {
      return respondJson({ loaded: false, files: [] })
    }
    if (method === 'POST' && path === '/api/upload') {
      return respondJson({ loaded: true, files: [PDF_FILE_NAME] })
    }
    if (method === 'GET' && path === '/api/history') {
      return respondJson({ history: [] })
    }
    if (method === 'POST' && path === '/api/ask') {
      return respondJson({ answer: ANSWER })
    }
    if (method === 'DELETE' && path === '/api/history') {
      return respondJson({ history: [] })
    }
    return route.fulfill({ status: 404, headers: CORS_HEADERS, body: 'Not Found' })
  })
}

test('main flow: upload a PDF, ask a question, clear the history', async ({ page }) => {
  await stubBackend(page)
  await page.goto('/')

  // Starts with no document loaded: empty sidebar, question input disabled.
  await expect(page.getByText('No documents uploaded yet.')).toBeVisible()
  await expect(page.getByLabel('Question')).toBeDisabled()

  // Attach a PDF from the chat input area.
  const fileChooserPromise = page.waitForEvent('filechooser')
  await page.getByRole('button', { name: '📎 Attach PDFs' }).click()
  const fileChooser = await fileChooserPromise
  await fileChooser.setFiles(PDF_FIXTURE_PATH)

  // The sidebar refreshes with the uploaded file.
  const sidebar = page.getByRole('complementary', { name: 'Uploaded documents' })
  await expect(sidebar.getByText(PDF_FILE_NAME)).toBeVisible()
  await expect(sidebar.getByText('No documents uploaded yet.')).not.toBeVisible()

  // Ask a question; both it and the answer appear in the chat window.
  await page.getByLabel('Question').fill(QUESTION)
  await page.getByRole('button', { name: 'Send' }).click()
  const conversation = page.getByRole('list', { name: 'Conversation' })
  await expect(conversation.getByText(QUESTION)).toBeVisible()
  await expect(conversation.getByText(ANSWER)).toBeVisible()

  // Clear history resets the conversation to the empty state.
  await page.getByRole('button', { name: 'Clear history' }).click()
  await expect(conversation.getByText(QUESTION)).not.toBeVisible()
  await expect(
    page.getByText('Upload a PDF and ask a question to get started.'),
  ).toBeVisible()
})
