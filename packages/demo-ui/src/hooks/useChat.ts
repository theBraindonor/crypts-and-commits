import { useCallback, useRef, useState } from 'react'
import { streamChat } from '../api/chat'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const threadIdRef = useRef<string | undefined>(undefined)

  const sendMessage = useCallback(async (text: string) => {
    setError(null)
    setMessages((prev) => [...prev, { role: 'user', content: text }, { role: 'assistant', content: '' }])
    setSending(true)

    try {
      const result = await streamChat({ threadId: threadIdRef.current, message: text }, (chunk) => {
        setMessages((prev) => {
          const next = [...prev]
          const last = next[next.length - 1]
          next[next.length - 1] = { ...last, content: last.content + chunk }
          return next
        })
      })
      threadIdRef.current = result.threadId
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong sending your message.')
      setMessages((prev) => prev.slice(0, -1))
    } finally {
      setSending(false)
    }
  }, [])

  return { messages, sending, error, sendMessage }
}
