import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { Application } from '../types'
import { FunnelView } from './FunnelView'

function makeApp(current_status: Application['current_status']): Application {
  return {
    id: Math.random(),
    company: 'Acme',
    role: 'SDET',
    applied_via: null,
    job_url: null,
    created_at: new Date().toISOString(),
    current_status,
  }
}

describe('FunnelView', () => {
  it('counts applications per current status', () => {
    const applications = [
      makeApp('applied'),
      makeApp('applied'),
      makeApp('interview_invite'),
      makeApp('rejected'),
    ]

    render(<FunnelView applications={applications} />)

    expect(screen.getByTestId('funnel-count-applied')).toHaveTextContent('2')
    expect(screen.getByTestId('funnel-count-interview_invite')).toHaveTextContent('1')
    expect(screen.getByTestId('funnel-count-rejected')).toHaveTextContent('1')
    expect(screen.getByTestId('funnel-count-offer')).toHaveTextContent('0')
  })

  it('renders zero counts for every stage with no applications', () => {
    render(<FunnelView applications={[]} />)
    expect(screen.getByTestId('funnel-count-applied')).toHaveTextContent('0')
  })
})
