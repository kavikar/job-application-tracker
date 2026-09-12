import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ManualEntryForm } from './ManualEntryForm'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('ManualEntryForm', () => {
  it('submits company/role and calls onCreated with the API response', async () => {
    const created = {
      id: 1,
      company: 'Acme',
      role: 'SDET',
      applied_via: null,
      job_url: null,
      created_at: '2026-01-01T00:00:00Z',
      current_status: 'applied' as const,
    }
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(created), { status: 201 }))
    vi.stubGlobal('fetch', fetchMock)
    const onCreated = vi.fn()

    render(<ManualEntryForm onCreated={onCreated} />)
    await userEvent.type(screen.getByLabelText(/company/i), 'Acme')
    await userEvent.type(screen.getByLabelText(/role/i), 'SDET')
    await userEvent.click(screen.getByRole('button', { name: /log application/i }))

    expect(onCreated).toHaveBeenCalledWith(created)
    // Form clears after a successful submit.
    expect(screen.getByLabelText(/company/i)).toHaveValue('')
  })

  it('shows an error message and does not clear the form on failure', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('company is required', { status: 422 }))
    vi.stubGlobal('fetch', fetchMock)
    const onCreated = vi.fn()

    render(<ManualEntryForm onCreated={onCreated} />)
    await userEvent.type(screen.getByLabelText(/company/i), 'Acme')
    await userEvent.type(screen.getByLabelText(/role/i), 'SDET')
    await userEvent.click(screen.getByRole('button', { name: /log application/i }))

    expect(await screen.findByText(/failed|422/i)).toBeInTheDocument()
    expect(onCreated).not.toHaveBeenCalled()
    expect(screen.getByLabelText(/company/i)).toHaveValue('Acme')
  })
})
