import { render, screen } from '@testing-library/react'
import App from '../../src/App'

describe('App layout shell', () => {
  it('renders the documents sidebar', () => {
    render(<App />)

    const sidebar = screen.getByRole('complementary', { name: 'Uploaded documents' })
    expect(sidebar).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Documents' })).toBeInTheDocument()
  })

  it('renders the chat area with a question input', () => {
    render(<App />)

    const chatArea = screen.getByRole('region', { name: 'Chat' })
    expect(chatArea).toBeInTheDocument()
    expect(
      screen.getByPlaceholderText('Ask a question about your PDFs…'),
    ).toBeInTheDocument()
  })
})
