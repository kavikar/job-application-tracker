import type { Application, Status } from '../types'

const STAGES: { key: Status; label: string }[] = [
  { key: 'applied', label: 'Applied' },
  { key: 'application_received', label: 'Received' },
  { key: 'interview_invite', label: 'Interview' },
  { key: 'offer', label: 'Offer' },
  { key: 'rejected', label: 'Rejected' },
]

interface Props {
  applications: Application[]
}

export function FunnelView({ applications }: Props) {
  const counts = STAGES.map((stage) => ({
    ...stage,
    count: applications.filter((a) => a.current_status === stage.key).length,
  }))
  const max = Math.max(1, ...counts.map((c) => c.count))

  return (
    <div className="space-y-2">
      {counts.map((stage) => (
        <div key={stage.key} className="flex items-center gap-3">
          <span className="w-24 text-sm text-gray-600">{stage.label}</span>
          <div className="h-6 flex-1 overflow-hidden rounded bg-gray-100">
            <div
              className="h-full bg-blue-500"
              style={{ width: `${(stage.count / max) * 100}%` }}
            />
          </div>
          <span
            className="w-8 text-right text-sm font-medium"
            data-testid={`funnel-count-${stage.key}`}
          >
            {stage.count}
          </span>
        </div>
      ))}
    </div>
  )
}
