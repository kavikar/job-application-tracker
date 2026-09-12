import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { Application } from '../types'
import { CompanyTable } from './CompanyTable'

const ACME: Application = {
  id: 1,
  company: 'Acme',
  role: 'SDET',
  applied_via: null,
  job_url: null,
  created_at: '2026-01-01T00:00:00Z',
  current_status: 'interview_invite',
}

describe('CompanyTable', () => {
  it('shows an empty state with no applications', () => {
    render(<CompanyTable applications={[]} />)
    expect(screen.getByText(/no applications logged yet/i)).toBeInTheDocument()
  })

  it('renders one row per application with a human-readable status', () => {
    render(<CompanyTable applications={[ACME]} />)
    expect(screen.getByText('Acme')).toBeInTheDocument()
    expect(screen.getByText('SDET')).toBeInTheDocument()
    expect(screen.getByText('Interview')).toBeInTheDocument()
  })

  it('calls onSelect with the clicked application', async () => {
    const onSelect = vi.fn()
    render(<CompanyTable applications={[ACME]} onSelect={onSelect} />)

    await userEvent.click(screen.getByText('Acme'))

    expect(onSelect).toHaveBeenCalledWith(ACME)
  })
})
