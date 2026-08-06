export interface ChatRequest {
  threadId?: string
  message: string
}

export interface ChatStreamResult {
  threadId: string
}

export async function streamChat(request: ChatRequest, onChunk: (content: string) => void): Promise<ChatStreamResult> {
  const response = await fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ thread_id: request.threadId, message: request.message }),
  })

  if (!response.ok || !response.body) {
    throw new Error(`Chat request failed with status ${response.status}`)
  }

  const threadId = response.headers.get('X-Thread-Id')
  if (!threadId) {
    throw new Error('Chat response is missing the X-Thread-Id header')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  const consumeLine = (line: string) => {
    if (!line) return
    const parsed = JSON.parse(line) as { content: string }
    onChunk(parsed.content)
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    let newlineIndex = buffer.indexOf('\n')
    while (newlineIndex !== -1) {
      consumeLine(buffer.slice(0, newlineIndex))
      buffer = buffer.slice(newlineIndex + 1)
      newlineIndex = buffer.indexOf('\n')
    }
  }

  consumeLine(buffer)

  return { threadId }
}
