import ChatArea from './components/ChatArea'
import Sidebar from './components/Sidebar'
import './App.css'

export default function App() {
  return (
    <div className="app-layout">
      <Sidebar />
      <ChatArea />
    </div>
  )
}
