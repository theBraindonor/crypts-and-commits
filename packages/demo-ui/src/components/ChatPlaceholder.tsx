import './ChatPlaceholder.css'

export function ChatPlaceholder() {
  return (
    <section className="chat-placeholder">
      <div className="chat-placeholder__messages">
        <p className="chat-placeholder__note">Chat coming soon.</p>
      </div>
      <form className="chat-placeholder__input-row" onSubmit={(e) => e.preventDefault()}>
        <input
          type="text"
          className="chat-placeholder__input"
          placeholder="Ask a question..."
          disabled
        />
        <button type="submit" className="chat-placeholder__send" disabled>
          Send
        </button>
      </form>
    </section>
  )
}
