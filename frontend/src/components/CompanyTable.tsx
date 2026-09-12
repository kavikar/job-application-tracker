import type { Application } from '../types'

interface Props {
  applications: Application[]
  onSelect?: (application: Application) => void
}

const STATUS_LABELS: Record<string, string> = {
  applied: 'Applied',
  application_received: 'Received',
  interview_invite: 'Interview',
  rejected: 'Rejected',
  offer: 'Offer',
}

export function CompanyTable({ applications, onSelect }: Props) {
  if (applications.length === 0) {
    return <p className="text-sm text-gray-500">No applications logged yet.</p>
  }

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b text-left text-gray-500">
          <th className="py-2">Company</th>
          <th>Role</th>
          <th>Status</th>
          <th>Applied</th>
        </tr>
      </thead>
      <tbody>
        {applications.map((application) => (
          <tr
            key={application.id}
            className="cursor-pointer border-b last:border-0 hover:bg-gray-50"
            onClick={() => onSelect?.(application)}
          >
            <td className="py-2 font-medium">{application.company}</td>
            <td>{application.role}</td>
            <td>{STATUS_LABELS[application.current_status] ?? application.current_status}</td>
            <td>{new Date(application.created_at).toLocaleDateString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
