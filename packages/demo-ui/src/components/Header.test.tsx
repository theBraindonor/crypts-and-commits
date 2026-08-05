import { render, screen, waitFor } from '@testing-library/react'
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
    render(<Header />)
    expect(screen.getByText('Crypts and Commits Demo Chatbot')).toBeDefined()
  })

  it('shows checking before the health check resolves', () => {
    mockFetchOnce({ ok: true, body: { success: true } })
    render(<Header />)
    expect(screen.getByText('Checking...')).toBeDefined()
  })

  it('shows online after a successful health check', async () => {
    mockFetchOnce({ ok: true, body: { success: true } })
    render(<Header />)
    await waitFor(() => expect(screen.getByText('Online')).toBeDefined())
  })

  it('shows offline after a failed health check', async () => {
    mockFetchOnce(new Error('network error'))
    render(<Header />)
    await waitFor(() => expect(screen.getByText('Offline')).toBeDefined())
  })

  it('shows offline after a non-2xx health check response', async () => {
    mockFetchOnce({ ok: false })
    render(<Header />)
    await waitFor(() => expect(screen.getByText('Offline')).toBeDefined())
  })
})
