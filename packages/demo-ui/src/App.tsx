import { Header } from './components/Header'
import { Chat } from './components/Chat'
import { useChat } from './hooks/useChat'
import './App.css'

function App() {
  const { messages, sending, error, sendMessage, resetChat } = useChat()

  return (
    <div className="app">
      <Header onNewChat={resetChat} newChatDisabled={sending || messages.length === 0} />
      <Chat messages={messages} sending={sending} error={error} sendMessage={sendMessage} />
    </div>
  )
}

export default App
