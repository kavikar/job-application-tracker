import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Application, StatusEvent } from '../types'
import { UnmatchedEvents } from './UnmatchedEvents'

afterEach(() => {
  vi.unstubAllGlobals()
})

const ACME: Application = {
  id: 1,
  company: 'Acme',
  role: 'SDET',
  applied_via: null,
  job_url: null,
  created_at: '2026-01-01T00:00:00Z',
  current_status: 'applied',
}

const EVENT: StatusEvent = {
  id: 10,
  status: 'interview_invite',
  source: 'gmail',
  raw_email_id: 'msg-abc',
  created_at: '2026-01-01T00:00:00Z',
}

describe('UnmatchedEvents', () => {
  it('shows an empty state with no unmatched events', () => {
    render(<UnmatchedEvents events={[]} applications={[]} onLinked={vi.fn()} />)
    expect(screen.getByText(/nothing unmatched/i)).toBeInTheDocument()
  })

  it('renders a Gmail link built from raw_email_id', () => {
    render(<UnmatchedEvents events={[EVENT]} applications={[ACME]} onLinked={vi.fn()} />)
    const link = screen.getByRole('link', { name: /open in gmail/i })
    expect(link).toHaveAttribute('href', 'https://mail.google.com/mail/u/0/#all/msg-abc')
  })

  it('disables Link until an application is picked, then calls the API and onLinked', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify({ ...EVENT, application_id: 1 }), { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)
    const onLinked = vi.fn()

    render(<UnmatchedEvents events={[EVENT]} applications={[ACME]} onLinked={onLinked} />)

    const linkButton = screen.getByRole('button', { name: /^link$/i })
    expect(linkButton).toBeDisabled()

    await userEvent.selectOptions(
      screen.getByLabelText(/link event 10 to application/i),
      'Acme',
    )
    expect(linkButton).toBeEnabled()

    await userEvent.click(linkButton)

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/events/10/link')
    expect(JSON.parse(options.body)).toEqual({ application_id: 1 })
    expect(onLinked).toHaveBeenCalled()
  })
})
