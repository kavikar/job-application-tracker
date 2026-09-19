import { useEffect, useState } from 'react'
import { api } from '../api'
import type { TargetCompany, Tier } from '../types'
import { AddTargetCompanyForm } from './AddTargetCompanyForm'

const TIER_INFO: Record<Tier, { label: string; blurb: string }> = {
  A: { label: 'Tier A', blurb: 'Apply now' },
  B: { label: 'Tier B', blurb: 'Apply in parallel' },
  C: { label: 'Tier C', blurb: 'After 8-10 weeks of DSA' },
  D: { label: 'Tier D', blurb: 'Opportunistic AI evaluation' },
}

const TIER_ORDER: Tier[] = ['A', 'B', 'C', 'D']

const UNCATEGORIZED = Symbol('uncategorized')

function groupByCategory(companies: TargetCompany[]): Map<string | typeof UNCATEGORIZED, TargetCompany[]> {
  const groups = new Map<string | typeof UNCATEGORIZED, TargetCompany[]>()
  for (const company of companies) {
    const key = company.category ?? UNCATEGORIZED
    const group = groups.get(key)
    if (group) {
      group.push(company)
    } else {
      groups.set(key, [company])
    }
  }
  return groups
}

export function TargetCompaniesTab() {
  const [targets, setTargets] = useState<TargetCompany[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function refresh() {
    setLoading(true)
    setError(null)
    try {
      setTargets(await api.listTargetCompanies())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load target companies')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  async function handleDelete(id: number) {
    await api.deleteTargetCompany(id)
    refresh()
  }

  if (loading) return <p className="text-sm text-gray-500">Loading…</p>

  return (
    <div className="space-y-8">
      {error && <p className="text-sm text-red-600">{error}</p>}

      {targets.length === 0 && (
        <p className="text-sm text-gray-500">No target companies yet.</p>
      )}

      {TIER_ORDER.map((tier) => {
        const inTier = targets.filter((t) => t.tier === tier)
        if (inTier.length === 0) return null

        return (
          <section key={tier}>
            <h2 className="text-lg font-medium">
              {TIER_INFO[tier].label}{' '}
              <span className="text-sm font-normal text-gray-500">
                — {TIER_INFO[tier].blurb}
              </span>
            </h2>
            {[...groupByCategory(inTier).entries()].map(([category, companies]) => (
              <div key={typeof category === 'string' ? category : 'uncategorized'} className="mt-3">
                {typeof category === 'string' && (
                  <h3 className="text-sm font-semibold text-gray-600">{category}</h3>
                )}
                <ul className="mt-1 divide-y">
                  {companies.map((target) => (
                    <li key={target.id} className="flex items-center gap-2 py-1.5 text-sm">
                      <span className={target.already_applied ? 'text-gray-400 line-through' : ''}>
                        {target.company}
                      </span>
                      {target.already_applied && (
                        <span className="text-xs font-medium text-green-600">applied</span>
                      )}
                      {target.notes && (
                        <span className="text-xs text-gray-500">({target.notes})</span>
                      )}
                      <button
                        onClick={() => handleDelete(target.id)}
                        className="ml-auto text-xs text-red-500 hover:underline"
                      >
                        remove
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </section>
        )
      })}

      <AddTargetCompanyForm onAdded={refresh} />
    </div>
  )
}
