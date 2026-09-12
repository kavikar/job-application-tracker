import { useState, type FormEvent, type ReactNode } from 'react'
import { api } from '../api'
import { clearApiKey, getApiKey, setApiKey } from '../auth'

interface Props {
  children: ReactNode
}

export function ApiKeyGate({ children }: Props) {
  const [unlocked, setUnlocked] = useState(() => Boolean(getApiKey()))
  const [input, setInput] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [checking, setChecking] = useState(false)

  if (unlocked) return <>{children}</>

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setChecking(true)
    setApiKey(input.trim())
    try {
      // Validate immediately rather than optimistically unlocking --
      // a typo'd key would otherwise only surface as a confusing
      // "failed to load data" error on the dashboard behind this gate.
      await api.listApplications()
      setUnlocked(true)
    } catch {
      clearApiKey()
      setError('Invalid API key')
    } finally {
      setChecking(false)
    }
  }

  return (
    <div className="mx-auto max-w-sm px-4 py-16">
      <h1 className="mb-4 text-xl font-semibold">Job Application Tracker</h1>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label htmlFor="api-key" className="block text-sm font-medium">
            API key
          </label>
          <input
            id="api-key"
            type="password"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            required
            className="mt-1 w-full rounded border px-2 py-1"
          />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={checking}
          className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {checking ? 'Checking…' : 'Unlock'}
        </button>
      </form>
    </div>
  )
}
