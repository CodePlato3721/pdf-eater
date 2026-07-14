import type { ChatMessage } from '../hooks/useChat'
import { usePdfAttachment } from '../hooks/usePdfAttachment'
import { useQuestionForm } from '../hooks/useQuestionForm'

interface ChatAreaProps {
  uploading: boolean
  uploadError: string | null
  onUpload: (files: File[]) => void
  messages: ChatMessage[]
  thinking: boolean
  askError: string | null
  hasDocuments: boolean
  onAsk: (question: string) => void
  onClearHistory: () => void
}

export default function ChatArea({
  uploading,
  uploadError,
  onUpload,
  messages,
  thinking,
  askError,
  hasDocuments,
  onAsk,
  onClearHistory,
}: ChatAreaProps) {
  const { inputRef, openPicker, onFilesSelected } = usePdfAttachment(onUpload)
  const { question, onQuestionChange, onSubmit } = useQuestionForm(onAsk)

  return (
    <section className="chat-area" aria-label="Chat">
      <div className="chat-toolbar">
        <button
          className="chat-clear"
          type="button"
          onClick={onClearHistory}
          disabled={messages.length === 0 || thinking}
        >
          Clear history
        </button>
      </div>
      <div className="chat-messages">
        {messages.length === 0 && !thinking ? (
          <p className="chat-empty">Upload a PDF and ask a question to get started.</p>
        ) : (
          <ul className="chat-message-list" aria-label="Conversation">
            {messages.map((message, index) => (
              <li
                key={index}
                className={`chat-message chat-message-${message.role}`}
              >
                {message.text}
              </li>
            ))}
          </ul>
        )}
        {thinking && (
          <p className="chat-thinking" role="status">
            Thinking…
          </p>
        )}
      </div>
      {uploading && (
        <p className="upload-status" role="status">
          Uploading…
        </p>
      )}
      {uploadError && (
        <p className="upload-error" role="alert">
          {uploadError}
        </p>
      )}
      {askError && (
        <p className="ask-error" role="alert">
          {askError}
        </p>
      )}
      <form className="chat-input-row" onSubmit={onSubmit}>
        <input
          ref={inputRef}
          className="chat-attach-input"
          type="file"
          accept="application/pdf"
          multiple
          aria-label="Attach PDFs"
          onChange={onFilesSelected}
        />
        <button
          className="chat-attach"
          type="button"
          onClick={openPicker}
          disabled={uploading}
        >
          📎 Attach PDFs
        </button>
        <input
          className="chat-input"
          type="text"
          placeholder="Ask a question about your PDFs…"
          aria-label="Question"
          value={question}
          onChange={onQuestionChange}
          disabled={!hasDocuments || thinking}
        />
        <button
          className="chat-send"
          type="submit"
          disabled={!hasDocuments || thinking}
        >
          Send
        </button>
      </form>
    </section>
  )
}
