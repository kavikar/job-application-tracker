import { useState, type FormEvent } from 'react'
import { api } from '../api'
import type { Application } from '../types'

interface Props {
  onCreated: (application: Application) => void
}

export function ManualEntryForm({ onCreated }: Props) {
  const [company, setCompany] = useState('')
  const [role, setRole] = useState('')
  const [jobUrl, setJobUrl] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const created = await api.createApplication({
        company,
        role,
        job_url: jobUrl || undefined,
      })
      onCreated(created)
      setCompany('')
      setRole('')
      setJobUrl('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save application')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div>
        <label htmlFor="company" className="block text-sm font-medium">
          Company
        </label>
        <input
          id="company"
          value={company}
          onChange={(e) => setCompany(e.target.value)}
          required
          className="mt-1 w-full rounded border px-2 py-1"
        />
      </div>
      <div>
        <label htmlFor="role" className="block text-sm font-medium">
          Role
        </label>
        <input
          id="role"
          value={role}
          onChange={(e) => setRole(e.target.value)}
          required
          className="mt-1 w-full rounded border px-2 py-1"
        />
      </div>
      <div>
        <label htmlFor="job_url" className="block text-sm font-medium">
          Job URL (optional)
        </label>
        <input
          id="job_url"
          value={jobUrl}
          onChange={(e) => setJobUrl(e.target.value)}
          className="mt-1 w-full rounded border px-2 py-1"
        />
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <button
        type="submit"
        disabled={submitting}
        className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
      >
        {submitting ? 'Saving…' : 'Log application'}
      </button>
    </form>
  )
}
