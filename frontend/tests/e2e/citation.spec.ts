import { expect, test, type Page } from '@playwright/test'

// Resolved against the working directory, which is frontend/ because the
// Playwright config lives there.
const PDF_FIXTURE_PATH = 'tests/e2e/fixtures/little-women.pdf'
const PDF_FILE_NAME = 'little-women.pdf'
const QUESTION = 'Where does Jo first appear?'
const ANSWER_TEXT = 'Chapter 1, grumbling by the fireplace.'
const CITATION_PAGE = 3
const CITATION_QUOTE =
  'Jo came stalking in a moment later with her hands behind her, and a queer expression of countenance.'
// Mirrors backend/core/citation.py::CITATION_TEMPLATE, which is what the
// backend actually appends to the answer string returned by /api/ask.
const ANSWER_WITH_CITATION = `${ANSWER_TEXT}\n\n---\nSource (page ${CITATION_PAGE}):\n${CITATION_QUOTE}`

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
      return respondJson({ answer: ANSWER_WITH_CITATION })
    }
    return route.fulfill({ status: 404, headers: CORS_HEADERS, body: 'Not Found' })
  })
}

test('asking a question renders the appended source-quote citation', async ({ page }) => {
  await stubBackend(page)
  await page.goto('/')

  const fileChooserPromise = page.waitForEvent('filechooser')
  await page.getByRole('button', { name: '📎 Attach PDFs' }).click()
  const fileChooser = await fileChooserPromise
  await fileChooser.setFiles(PDF_FIXTURE_PATH)

  const sidebar = page.getByRole('complementary', { name: 'Uploaded documents' })
  await expect(sidebar.getByText(PDF_FILE_NAME)).toBeVisible()

  await page.getByLabel('Question').fill(QUESTION)
  await page.getByRole('button', { name: 'Send' }).click()

  // The rendered answer includes both the synthesized text and the appended
  // citation block: page-number separator line plus the supporting quote.
  const conversation = page.getByRole('list', { name: 'Conversation' })
  const answerMessage = conversation.getByText(ANSWER_TEXT)
  await expect(answerMessage).toBeVisible()
  await expect(answerMessage).toContainText(`Source (page ${CITATION_PAGE}):`)
  await expect(answerMessage).toContainText(CITATION_QUOTE)
})
