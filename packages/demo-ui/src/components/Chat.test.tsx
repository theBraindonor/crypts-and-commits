import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { Chat } from './Chat'

function makeStreamResponse(lines: string[], threadId: string): Response {
  const fullText = lines.map((line) => JSON.stringify({ content: line }) + '\n').join('')
  const bytes = new TextEncoder().encode(fullText)

  // Split into several chunks, deliberately not aligned to line boundaries,
  // to exercise the reader's cross-chunk buffering.
  const chunkCount = 3
  const chunkSize = Math.max(1, Math.ceil(bytes.length / chunkCount))
  const chunks: Uint8Array[] = []
  for (let i = 0; i < bytes.length; i += chunkSize) {
    chunks.push(bytes.slice(i, i + chunkSize))
  }

  let index = 0
  const stream = new ReadableStream<Uint8Array>({
    pull(controller) {
      if (index < chunks.length) {
        controller.enqueue(chunks[index])
        index += 1
      } else {
        controller.close()
      }
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

describe('Chat', () => {
  it('sends a message and renders the streamed assistant reply', async () => {
    const fetchMock = vi.fn().mockResolvedValue(makeStreamResponse(['Hello', ', ', 'world!'], 'thread-1'))
    vi.stubGlobal('fetch', fetchMock)

    render(<Chat />)
    await sendMessage('Hi there')

    expect(screen.getByText('Hi there')).toBeDefined()
    await waitFor(() => expect(screen.getByText('Hello, world!')).toBeDefined())
  })

  it('reuses the captured thread_id on the next message', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(makeStreamResponse(['First reply'], 'thread-abc'))
      .mockResolvedValueOnce(makeStreamResponse(['Second reply'], 'thread-abc'))
    vi.stubGlobal('fetch', fetchMock)

    render(<Chat />)
    await sendMessage('first')
    await waitFor(() => expect(screen.getByText('First reply')).toBeDefined())

    await sendMessage('second')
    await waitFor(() => expect(screen.getByText('Second reply')).toBeDefined())

    const secondCallBody = JSON.parse(fetchMock.mock.calls[1][1].body as string)
    expect(secondCallBody.thread_id).toBe('thread-abc')
  })

  it('shows an inline error and re-enables the input on failure', async () => {
    const fetchMock = vi.fn().mockRejectedValue(new Error('network down'))
    vi.stubGlobal('fetch', fetchMock)

    render(<Chat />)
    await sendMessage('hello')

    await waitFor(() => expect(screen.getByText('network down')).toBeDefined())
    const input = screen.getByPlaceholderText('Ask a question...') as HTMLInputElement
    expect(input.disabled).toBe(false)
  })
})
