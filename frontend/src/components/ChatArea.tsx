import { usePdfAttachment } from '../hooks/usePdfAttachment'

interface ChatAreaProps {
  uploading: boolean
  uploadError: string | null
  onUpload: (files: File[]) => void
}

export default function ChatArea({ uploading, uploadError, onUpload }: ChatAreaProps) {
  const { inputRef, openPicker, onFilesSelected } = usePdfAttachment(onUpload)

  return (
    <section className="chat-area" aria-label="Chat">
      <div className="chat-messages">
        <p className="chat-empty">Upload a PDF and ask a question to get started.</p>
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
      <form className="chat-input-row">
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
          disabled
        />
        <button className="chat-send" type="submit" disabled>
          Send
        </button>
      </form>
    </section>
  )
}
