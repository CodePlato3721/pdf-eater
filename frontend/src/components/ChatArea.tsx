export default function ChatArea() {
  return (
    <section className="chat-area" aria-label="Chat">
      <div className="chat-messages">
        <p className="chat-empty">Upload a PDF and ask a question to get started.</p>
      </div>
      <form className="chat-input-row">
        <input
          className="chat-input"
          type="text"
          placeholder="Ask a question about your PDFs…"
          disabled
        />
        <button className="chat-send" type="submit" disabled>
          Send
        </button>
      </form>
    </section>
  )
}
