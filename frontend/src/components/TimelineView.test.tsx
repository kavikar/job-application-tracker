import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { StatusEvent } from '../types'
import { TimelineView } from './TimelineView'

describe('TimelineView', () => {
  it('shows an empty state with no events', () => {
    render(<TimelineView events={[]} />)
    expect(screen.getByText(/no events yet/i)).toBeInTheDocument()
  })

  it('renders events in the order given (chronological, set by the API)', () => {
    const events: StatusEvent[] = [
      { id: 1, status: 'applied', source: 'manual', raw_email_id: null, created_at: '2026-01-01T00:00:00Z' },
      { id: 2, status: 'interview_invite', source: 'gmail', raw_email_id: 'm1', created_at: '2026-01-05T00:00:00Z' },
    ]

    render(<TimelineView events={events} />)

    const items = screen.getAllByRole('listitem')
    expect(items).toHaveLength(2)
    expect(items[0]).toHaveTextContent('Applied')
    expect(items[1]).toHaveTextContent('Interview invite')
  })
})
