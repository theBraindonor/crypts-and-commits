import { useState, type FormEvent } from 'react'
import { useChat } from '../hooks/useChat'
import './Chat.css'

export function Chat() {
  const { messages, sending, error, sendMessage } = useChat()
  const [draft, setDraft] = useState('')

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    const text = draft.trim()
    if (!text || sending) return
    setDraft('')
    void sendMessage(text)
  }

  return (
    <section className="chat">
      <div className="chat__messages">
        {messages.length === 0 && <p className="chat__note">Chat coming soon.</p>}
        {messages.map((message, index) => (
          <div key={index} className={`chat__message chat__message--${message.role}`}>
            {message.content}
          </div>
        ))}
        {error && <p className="chat__error">{error}</p>}
      </div>
      <form className="chat__input-row" onSubmit={handleSubmit}>
        <input
          type="text"
          className="chat__input"
          placeholder="Ask a question..."
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          disabled={sending}
        />
        <button type="submit" className="chat__send" disabled={sending || !draft.trim()}>
          Send
        </button>
      </form>
    </section>
  )
}
