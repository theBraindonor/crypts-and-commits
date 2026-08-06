import { act, renderHook, waitFor } from '@testing-library/react'
import { useChat } from './useChat'

function makeStreamResponse(lines: string[], threadId: string): Response {
  const fullText = lines.map((line) => JSON.stringify({ content: line }) + '\n').join('')
  const bytes = new TextEncoder().encode(fullText)

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

describe('useChat resetChat', () => {
  it('clears messages and error', async () => {
    const fetchMock = vi.fn().mockRejectedValue(new Error('network down'))
    vi.stubGlobal('fetch', fetchMock)

    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('hello')
    })

    expect(result.current.messages.length).toBe(1)
    expect(result.current.error).toBe('network down')

    act(() => {
      result.current.resetChat()
    })

    expect(result.current.messages).toEqual([])
    expect(result.current.error).toBeNull()
  })

  it('forgets the thread_id so the next request omits it', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(makeStreamResponse(['First reply'], 'thread-abc'))
      .mockResolvedValueOnce(makeStreamResponse(['Second reply'], 'thread-xyz'))
    vi.stubGlobal('fetch', fetchMock)

    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('first')
    })
    await waitFor(() => expect(result.current.messages.at(-1)?.content).toBe('First reply'))

    act(() => {
      result.current.resetChat()
    })
    expect(result.current.messages).toEqual([])

    await act(async () => {
      await result.current.sendMessage('second')
    })

    const secondCallBody = JSON.parse(fetchMock.mock.calls[1][1].body as string)
    expect(secondCallBody.thread_id).toBeUndefined()
  })
})
