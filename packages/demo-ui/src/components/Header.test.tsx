import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { Header } from './Header'

function mockFetchOnce(response: { ok: boolean; body?: unknown } | Error) {
  const fetchMock = vi.fn(() => {
    if (response instanceof Error) {
      return Promise.reject(response)
    }
    return Promise.resolve({
      ok: response.ok,
      status: response.ok ? 200 : 500,
      json: () => Promise.resolve(response.body ?? {}),
    } as Response)
  })
  vi.stubGlobal('fetch', fetchMock)
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('Header', () => {
  it('renders the app title', () => {
    mockFetchOnce({ ok: true, body: { success: true } })
    render(<Header onNewChat={() => {}} newChatDisabled={true} />)
    expect(screen.getByText('Crypts and Commits Demo Chatbot')).toBeDefined()
  })

  it('shows checking before the health check resolves', () => {
    mockFetchOnce({ ok: true, body: { success: true } })
    render(<Header onNewChat={() => {}} newChatDisabled={true} />)
    expect(screen.getByText('Checking...')).toBeDefined()
  })

  it('shows online after a successful health check', async () => {
    mockFetchOnce({ ok: true, body: { success: true } })
    render(<Header onNewChat={() => {}} newChatDisabled={true} />)
    await waitFor(() => expect(screen.getByText('Online')).toBeDefined())
  })

  it('shows offline after a failed health check', async () => {
    mockFetchOnce(new Error('network error'))
    render(<Header onNewChat={() => {}} newChatDisabled={true} />)
    await waitFor(() => expect(screen.getByText('Offline')).toBeDefined())
  })

  it('shows offline after a non-2xx health check response', async () => {
    mockFetchOnce({ ok: false })
    render(<Header onNewChat={() => {}} newChatDisabled={true} />)
    await waitFor(() => expect(screen.getByText('Offline')).toBeDefined())
  })

  it('calls onNewChat when the New Chat button is clicked', () => {
    mockFetchOnce({ ok: true, body: { success: true } })
    const onNewChat = vi.fn()
    render(<Header onNewChat={onNewChat} newChatDisabled={false} />)
    fireEvent.click(screen.getByText('New chat'))
    expect(onNewChat).toHaveBeenCalledTimes(1)
  })

  it('disables the New Chat button when newChatDisabled is true', () => {
    mockFetchOnce({ ok: true, body: { success: true } })
    render(<Header onNewChat={() => {}} newChatDisabled={true} />)
    const button = screen.getByText('New chat') as HTMLButtonElement
    expect(button.disabled).toBe(true)
  })

  it('renders a GitHub link to the repository', () => {
    mockFetchOnce({ ok: true, body: { success: true } })
    render(<Header onNewChat={() => {}} newChatDisabled={true} />)
    const link = screen.getByLabelText('View source on GitHub') as HTMLAnchorElement
    expect(link.href).toBe('https://github.com/theBraindonor/crypts-and-commits')
    expect(link.target).toBe('_blank')
    expect(link.rel).toBe('noopener noreferrer')
  })
})
