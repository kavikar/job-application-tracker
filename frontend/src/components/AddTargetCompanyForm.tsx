import { useState, type FormEvent } from 'react'
import { api } from '../api'
import type { TargetCompany, Tier } from '../types'

interface Props {
  onAdded: (target: TargetCompany) => void
}

const TIERS: Tier[] = ['A', 'B', 'C', 'D']

export function AddTargetCompanyForm({ onAdded }: Props) {
  const [company, setCompany] = useState('')
  const [tier, setTier] = useState<Tier>('A')
  const [category, setCategory] = useState('')
  const [notes, setNotes] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const created = await api.createTargetCompany({
        company,
        tier,
        category: category || undefined,
        notes: notes || undefined,
      })
      onAdded(created)
      setCompany('')
      setCategory('')
      setNotes('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add target company')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-2">
      <div>
        <label htmlFor="target-company" className="block text-sm font-medium">
          Company
        </label>
        <input
          id="target-company"
          value={company}
          onChange={(e) => setCompany(e.target.value)}
          required
          className="mt-1 rounded border px-2 py-1"
        />
      </div>
      <div>
        <label htmlFor="target-tier" className="block text-sm font-medium">
          Tier
        </label>
        <select
          id="target-tier"
          value={tier}
          onChange={(e) => setTier(e.target.value as Tier)}
          className="mt-1 rounded border px-2 py-1"
        >
          {TIERS.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="target-category" className="block text-sm font-medium">
          Category (optional)
        </label>
        <input
          id="target-category"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="mt-1 rounded border px-2 py-1"
        />
      </div>
      <div>
        <label htmlFor="target-notes" className="block text-sm font-medium">
          Notes (optional)
        </label>
        <input
          id="target-notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          className="mt-1 rounded border px-2 py-1"
        />
      </div>
      {error && <p className="w-full text-sm text-red-600">{error}</p>}
      <button
        type="submit"
        disabled={submitting}
        className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
      >
        {submitting ? 'Adding…' : 'Add target'}
      </button>
    </form>
  )
}
