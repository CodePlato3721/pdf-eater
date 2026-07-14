import ChatArea from './components/ChatArea'
import Sidebar from './components/Sidebar'
import { useChat } from './hooks/useChat'
import { useDocuments } from './hooks/useDocuments'
import './App.css'

export default function App() {
  const { files, uploading, uploadError, uploadFiles } = useDocuments()
  const { messages, thinking, askError, ask, clearChat } = useChat()

  return (
    <div className="app-layout">
      <Sidebar files={files} />
      <ChatArea
        uploading={uploading}
        uploadError={uploadError}
        onUpload={uploadFiles}
        messages={messages}
        thinking={thinking}
        askError={askError}
        hasDocuments={files.length > 0}
        onAsk={ask}
        onClearHistory={clearChat}
      />
    </div>
  )
}
