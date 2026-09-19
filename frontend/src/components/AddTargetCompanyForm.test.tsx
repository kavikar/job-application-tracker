import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AddTargetCompanyForm } from './AddTargetCompanyForm'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('AddTargetCompanyForm', () => {
  it('submits company/tier and calls onAdded, then clears the form', async () => {
    const created = {
      id: 1,
      company: 'Toast',
      tier: 'A' as const,
      category: null,
      notes: null,
      created_at: '2026-01-01T00:00:00Z',
      already_applied: false,
    }
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(created), { status: 201 }))
    vi.stubGlobal('fetch', fetchMock)
    const onAdded = vi.fn()

    render(<AddTargetCompanyForm onAdded={onAdded} />)
    await userEvent.type(screen.getByLabelText(/^company$/i), 'Toast')
    await userEvent.click(screen.getByRole('button', { name: /add target/i }))

    expect(onAdded).toHaveBeenCalledWith(created)
    expect(screen.getByLabelText(/^company$/i)).toHaveValue('')

    const [, options] = fetchMock.mock.calls[0]
    expect(JSON.parse(options.body)).toEqual({ company: 'Toast', tier: 'A' })
  })

  it('shows an error and keeps the form filled on failure', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response('company is required', { status: 422 })),
    )
    const onAdded = vi.fn()

    render(<AddTargetCompanyForm onAdded={onAdded} />)
    await userEvent.type(screen.getByLabelText(/^company$/i), 'Toast')
    await userEvent.click(screen.getByRole('button', { name: /add target/i }))

    expect(await screen.findByText(/failed|422/i)).toBeInTheDocument()
    expect(onAdded).not.toHaveBeenCalled()
    expect(screen.getByLabelText(/^company$/i)).toHaveValue('Toast')
  })
})
