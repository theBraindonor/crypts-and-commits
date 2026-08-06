import { fireEvent, render, screen } from '@testing-library/react'
import { Chat } from './Chat'
import type { ChatMessage } from '../hooks/useChat'

describe('Chat', () => {
  it('renders provided messages in order', () => {
    const messages: ChatMessage[] = [
      { role: 'user', content: 'Hi there' },
      { role: 'assistant', content: 'Hello, world!' },
    ]
    render(<Chat messages={messages} sending={false} error={null} sendMessage={vi.fn()} />)

    expect(screen.getByText('Hi there')).toBeDefined()
    expect(screen.getByText('Hello, world!')).toBeDefined()
  })

  it('shows no placeholder note when there are no messages', () => {
    render(<Chat messages={[]} sending={false} error={null} sendMessage={vi.fn()} />)

    expect(screen.queryByText(/coming soon/i)).toBeNull()
  })

  it('disables the input and send button while sending', () => {
    render(<Chat messages={[]} sending={true} error={null} sendMessage={vi.fn()} />)

    const input = screen.getByPlaceholderText('Ask a question...') as HTMLInputElement
    const send = screen.getByText('Send') as HTMLButtonElement
    expect(input.disabled).toBe(true)
    expect(send.disabled).toBe(true)
  })

  it('renders an inline error message', () => {
    render(<Chat messages={[]} sending={false} error="network down" sendMessage={vi.fn()} />)

    expect(screen.getByText('network down')).toBeDefined()
  })

  it('calls sendMessage with the trimmed draft on submit', () => {
    const sendMessage = vi.fn()
    render(<Chat messages={[]} sending={false} error={null} sendMessage={sendMessage} />)

    const input = screen.getByPlaceholderText('Ask a question...')
    fireEvent.change(input, { target: { value: '  hello  ' } })
    fireEvent.click(screen.getByText('Send'))

    expect(sendMessage).toHaveBeenCalledWith('hello')
  })

  it('does not call sendMessage for a blank draft', () => {
    const sendMessage = vi.fn()
    render(<Chat messages={[]} sending={false} error={null} sendMessage={sendMessage} />)

    fireEvent.click(screen.getByText('Send'))

    expect(sendMessage).not.toHaveBeenCalled()
  })
})
