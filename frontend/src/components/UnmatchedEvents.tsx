import { useState } from 'react'
import { api } from '../api'
import type { Application, StatusEvent } from '../types'

interface Props {
  events: StatusEvent[]
  applications: Application[]
  onLinked: (event: StatusEvent) => void
}

// raw_email_id is the Gmail message id -- status_events deliberately
// doesn't store the email's subject/sender (see the schema's locked
// column list in DESIGN.md), so a direct Gmail permalink is the only
// way to give a reviewer the context to judge which application an
// unmatched event actually belongs to.
function gmailLink(messageId: string): string {
  return `https://mail.google.com/mail/u/0/#all/${messageId}`
}

export function UnmatchedEvents({ events, applications, onLinked }: Props) {
  const [selected, setSelected] = useState<Record<number, string>>({})
  const [linkingId, setLinkingId] = useState<number | null>(null)

  if (events.length === 0) {
    return <p className="text-sm text-gray-500">Nothing unmatched.</p>
  }

  async function handleLink(eventId: number) {
    const applicationId = Number(selected[eventId])
    if (!applicationId) return
    setLinkingId(eventId)
    try {
      const updated = await api.linkEvent(eventId, applicationId)
      onLinked(updated)
    } finally {
      setLinkingId(null)
    }
  }

  return (
    <ul className="space-y-2">
      {events.map((event) => (
        <li key={event.id} className="flex items-center gap-2 text-sm">
          <span className="flex-1">
            {event.status}
            {event.raw_email_id && (
              <>
                {' — '}
                <a
                  href={gmailLink(event.raw_email_id)}
                  target="_blank"
                  rel="noreferrer"
                  className="text-blue-600 underline"
                >
                  open in Gmail
                </a>
              </>
            )}
          </span>
          <select
            aria-label={`Link event ${event.id} to application`}
            value={selected[event.id] ?? ''}
            onChange={(e) => setSelected((prev) => ({ ...prev, [event.id]: e.target.value }))}
            className="rounded border px-1 py-0.5"
          >
            <option value="">Link to…</option>
            {applications.map((application) => (
              <option key={application.id} value={application.id}>
                {application.company}
              </option>
            ))}
          </select>
          <button
            onClick={() => handleLink(event.id)}
            disabled={!selected[event.id] || linkingId === event.id}
            className="rounded bg-gray-800 px-2 py-0.5 text-white disabled:opacity-50"
          >
            Link
          </button>
        </li>
      ))}
    </ul>
  )
}
