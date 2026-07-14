import ChatArea from './components/ChatArea'
import Sidebar from './components/Sidebar'
import { useDocuments } from './hooks/useDocuments'
import './App.css'

export default function App() {
  const { files, uploading, uploadError, uploadFiles } = useDocuments()

  return (
    <div className="app-layout">
      <Sidebar files={files} />
      <ChatArea uploading={uploading} uploadError={uploadError} onUpload={uploadFiles} />
    </div>
  )
}
