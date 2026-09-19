import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { TargetCompany } from '../types'
import { TargetCompaniesTab } from './TargetCompaniesTab'

afterEach(() => {
  vi.unstubAllGlobals()
})

const TARGETS: TargetCompany[] = [
  {
    id: 1,
    company: 'Toast',
    tier: 'A',
    category: 'Restaurant-tech & POS',
    notes: null,
    created_at: '2026-01-01T00:00:00Z',
    already_applied: false,
  },
  {
    id: 2,
    company: 'Square',
    tier: 'A',
    category: 'Restaurant-tech & POS',
    notes: null,
    created_at: '2026-01-01T00:00:00Z',
    already_applied: true,
  },
  {
    id: 3,
    company: 'OpenAI',
    tier: 'D',
    category: null,
    notes: 'opportunistic',
    created_at: '2026-01-01T00:00:00Z',
    already_applied: false,
  },
]

function mockFetchReturning(targets: TargetCompany[]) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue(new Response(JSON.stringify(targets), { status: 200 })),
  )
}

describe('TargetCompaniesTab', () => {
  it('groups companies by tier and category, and marks already-applied ones', async () => {
    mockFetchReturning(TARGETS)
    render(<TargetCompaniesTab />)

    expect(await screen.findByText('Tier A')).toBeInTheDocument()
    expect(screen.getByText('Restaurant-tech & POS')).toBeInTheDocument()
    expect(screen.getByText('Toast')).toBeInTheDocument()
    expect(screen.getByText('Square')).toBeInTheDocument()
    expect(screen.getByText('Tier D')).toBeInTheDocument()
    expect(screen.getByText('OpenAI')).toBeInTheDocument()
    expect(screen.getByText('(opportunistic)')).toBeInTheDocument()

    // Square is already applied -- shown, but flagged.
    const appliedLabels = screen.getAllByText('applied');
    expect(appliedLabels).toHaveLength(1)
  })

  it('shows an empty state with no targets', async () => {
    mockFetchReturning([])
    render(<TargetCompaniesTab />)
    expect(await screen.findByText(/no target companies yet/i)).toBeInTheDocument()
  })

  it('removing a target calls the delete API and refreshes the list', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(TARGETS), { status: 200 })) // initial load
      .mockResolvedValueOnce(new Response(null, { status: 204 })) // delete
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 })) // refresh
    vi.stubGlobal('fetch', fetchMock)

    render(<TargetCompaniesTab />)
    await screen.findByText('Toast')

    const removeButtons = screen.getAllByRole('button', { name: /remove/i })
    await userEvent.click(removeButtons[0])

    expect(await screen.findByText(/no target companies yet/i)).toBeInTheDocument()
    const deleteCall = fetchMock.mock.calls.find(([, options]) => options?.method === 'DELETE')
    expect(deleteCall).toBeDefined()
  })
})
