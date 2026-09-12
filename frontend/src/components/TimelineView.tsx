import type { StatusEvent } from '../types'

interface Props {
  events: StatusEvent[]
}

const STATUS_LABELS: Record<string, string> = {
  applied: 'Applied',
  application_received: 'Application received',
  interview_invite: 'Interview invite',
  rejected: 'Rejected',
  offer: 'Offer',
}

export function TimelineView({ events }: Props) {
  if (events.length === 0) {
    return <p className="text-sm text-gray-500">No events yet.</p>
  }

  return (
    <ol className="space-y-3">
      {events.map((event) => (
        <li key={event.id} className="flex items-start gap-3">
          <div className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-blue-500" />
          <div>
            <p className="text-sm font-medium">{STATUS_LABELS[event.status] ?? event.status}</p>
            <p className="text-xs text-gray-500">
              {new Date(event.created_at).toLocaleString()} · {event.source}
            </p>
          </div>
        </li>
      ))}
    </ol>
  )
}
