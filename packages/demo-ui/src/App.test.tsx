import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import App from './App'

function makeHealthResponse(): Response {
  return {
    ok: true,
    status: 200,
    json: () => Promise.resolve({ success: true }),
  } as unknown as Response
}

function makeChatResponse(lines: string[], threadId: string): Response {
  const fullText = lines.map((line) => JSON.stringify({ content: line }) + '\n').join('')
  const bytes = new TextEncoder().encode(fullText)
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(bytes)
      controller.close()
    },
  })

  return {
    ok: true,
    status: 200,
    body: stream,
    headers: new Headers({ 'X-Thread-Id': threadId }),
  } as unknown as Response
}

afterEach(() => {
  vi.unstubAllGlobals()
})

async function sendMessage(text: string) {
  const input = screen.getByPlaceholderText('Ask a question...')
  fireEvent.change(input, { target: { value: text } })
  fireEvent.click(screen.getByText('Send'))
}

describe('App', () => {
  it('clears the conversation and forgets the thread_id when New Chat is clicked', async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL, _init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url === '/health') return Promise.resolve(makeHealthResponse())
      return Promise.resolve(makeChatResponse(['Hi back'], 'thread-abc'))
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)

    await sendMessage('Hello')
    await waitFor(() => expect(screen.getByText('Hi back')).toBeDefined())

    const newChatButton = screen.getByText('New chat')
    await waitFor(() => expect((newChatButton as HTMLButtonElement).disabled).toBe(false))
    fireEvent.click(newChatButton)

    expect(screen.queryByText('Hello')).toBeNull()
    expect(screen.queryByText('Hi back')).toBeNull()

    await sendMessage('Second conversation')
    await waitFor(() => expect(screen.getByText('Second conversation')).toBeDefined())

    const chatCalls = fetchMock.mock.calls.filter(([input]) => {
      const url = typeof input === 'string' ? input : (input as URL).toString()
      return url === '/chat'
    })
    const secondChatCall = chatCalls[1]
    const secondChatCallBody = JSON.parse(secondChatCall![1]!.body as string)
    expect(secondChatCallBody.thread_id).toBeUndefined()
  })
})
