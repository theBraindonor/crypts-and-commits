import { useState, type FormEvent } from 'react'
import ReactMarkdown, { type Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { ChatMessage } from '../hooks/useChat'
import './Chat.css'

export interface ChatProps {
  messages: ChatMessage[]
  sending: boolean
  error: string | null
  sendMessage: (text: string) => void
}

const markdownComponents: Components = {
  a: ({ children, ...props }) => (
    <a {...props} target="_blank" rel="noopener noreferrer">
      {children}
    </a>
  ),
}

export function Chat({ messages, sending, error, sendMessage }: ChatProps) {
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
        {messages.map((message, index) => (
          <div key={index} className={`chat__message chat__message--${message.role}`}>
            {message.role === 'assistant' ? (
              <div className="chat__message-content">
                <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                  {message.content}
                </ReactMarkdown>
              </div>
            ) : (
              message.content
            )}
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
