import { useEffect, useState } from 'react'
import { api } from './api'
import { CompanyTable } from './components/CompanyTable'
import { FunnelView } from './components/FunnelView'
import { ManualEntryForm } from './components/ManualEntryForm'
import { TargetCompaniesTab } from './components/TargetCompaniesTab'
import { TimelineView } from './components/TimelineView'
import { UnmatchedEvents } from './components/UnmatchedEvents'
import type { Application, StatusEvent } from './types'

type Tab = 'applications' | 'targets'

function App() {
  const [tab, setTab] = useState<Tab>('applications')
  const [applications, setApplications] = useState<Application[]>([])
  const [unmatched, setUnmatched] = useState<StatusEvent[]>([])
  const [selected, setSelected] = useState<Application | null>(null)
  const [timeline, setTimeline] = useState<StatusEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  async function refresh() {
    setLoading(true)
    setLoadError(null)
    try {
      const [apps, events] = await Promise.all([api.listApplications(), api.getUnmatchedEvents()])
      setApplications(apps)
      setUnmatched(events)
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  useEffect(() => {
    if (!selected) {
      setTimeline([])
      return
    }
    api.getApplicationEvents(selected.id).then(setTimeline)
  }, [selected])

  return (
    <div className="mx-auto max-w-4xl space-y-8 px-4 py-8">
      <h1 className="text-2xl font-semibold">Job Application Tracker</h1>

      <div className="flex gap-4 border-b">
        <button
          onClick={() => setTab('applications')}
          className={`pb-2 text-sm font-medium ${
            tab === 'applications'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-gray-500'
          }`}
        >
          Applications
        </button>
        <button
          onClick={() => setTab('targets')}
          className={`pb-2 text-sm font-medium ${
            tab === 'targets' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'
          }`}
        >
          Target Companies
        </button>
      </div>

      {tab === 'targets' && <TargetCompaniesTab />}

      {tab === 'applications' && (
        <>
          {loadError && <p className="text-sm text-red-600">{loadError}</p>}
          {loading ? (
            <p className="text-sm text-gray-500">Loading…</p>
          ) : (
            <>
              <section>
                <h2 className="mb-3 text-lg font-medium">Funnel</h2>
                <FunnelView applications={applications} />
              </section>

              <section>
                <h2 className="mb-3 text-lg font-medium">Applications</h2>
                <CompanyTable applications={applications} onSelect={setSelected} />
              </section>

              {selected && (
                <section>
                  <h2 className="mb-3 text-lg font-medium">Timeline — {selected.company}</h2>
                  <TimelineView events={timeline} />
                </section>
              )}

              <section>
                <h2 className="mb-3 text-lg font-medium">Unmatched emails</h2>
                <UnmatchedEvents events={unmatched} applications={applications} onLinked={refresh} />
              </section>

              <section>
                <h2 className="mb-3 text-lg font-medium">Log an application</h2>
                <ManualEntryForm onCreated={refresh} />
              </section>
            </>
          )}
        </>
      )}
    </div>
  )
}

export default App
