import { useEffect, useState } from 'react'
import { fetchHealth } from '../api/health'

export type HealthStatus = 'checking' | 'online' | 'offline'

const POLL_INTERVAL_MS = 15_000

export function useHealthStatus(): HealthStatus {
  const [status, setStatus] = useState<HealthStatus>('checking')

  useEffect(() => {
    let cancelled = false

    const check = async () => {
      try {
        const result = await fetchHealth()
        if (!cancelled) {
          setStatus(result.success ? 'online' : 'offline')
        }
      } catch {
        if (!cancelled) {
          setStatus('offline')
        }
      }
    }

    check()
    const intervalId = setInterval(check, POLL_INTERVAL_MS)

    return () => {
      cancelled = true
      clearInterval(intervalId)
    }
  }, [])

  return status
}
