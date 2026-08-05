import { useHealthStatus } from '../hooks/useHealthStatus'
import './Header.css'

const STATUS_LABEL: Record<ReturnType<typeof useHealthStatus>, string> = {
  checking: 'Checking...',
  online: 'Online',
  offline: 'Offline',
}

export function Header() {
  const status = useHealthStatus()

  return (
    <header className="app-header">
      <h1 className="app-header__title">Crypts and Commits Demo Chatbot</h1>
      <div className="app-header__status" data-status={status}>
        <span className="app-header__status-dot" aria-hidden="true" />
        <span>{STATUS_LABEL[status]}</span>
      </div>
    </header>
  )
}
