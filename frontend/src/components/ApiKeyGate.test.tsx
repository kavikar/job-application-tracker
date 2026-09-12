import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { getApiKey } from '../auth'
import { ApiKeyGate } from './ApiKeyGate'

afterEach(() => {
  localStorage.clear()
  vi.unstubAllGlobals()
})

describe('ApiKeyGate', () => {
  it('shows the prompt and not the children when no key is stored', () => {
    render(
      <ApiKeyGate>
        <p>secret dashboard</p>
      </ApiKeyGate>,
    )
    expect(screen.getByLabelText(/api key/i)).toBeInTheDocument()
    expect(screen.queryByText('secret dashboard')).not.toBeInTheDocument()
  })

  it('unlocks and stores the key once the backend accepts it', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('[]', { status: 200 })))

    render(
      <ApiKeyGate>
        <p>secret dashboard</p>
      </ApiKeyGate>,
    )
    await userEvent.type(screen.getByLabelText(/api key/i), 'correct-key')
    await userEvent.click(screen.getByRole('button', { name: /unlock/i }))

    expect(await screen.findByText('secret dashboard')).toBeInTheDocument()
    expect(getApiKey()).toBe('correct-key')
  })

  it('shows an error and stays locked when the backend rejects the key', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response('Invalid or missing API key', { status: 401 })),
    )

    render(
      <ApiKeyGate>
        <p>secret dashboard</p>
      </ApiKeyGate>,
    )
    await userEvent.type(screen.getByLabelText(/api key/i), 'wrong-key')
    await userEvent.click(screen.getByRole('button', { name: /unlock/i }))

    expect(await screen.findByText(/invalid api key/i)).toBeInTheDocument()
    expect(screen.queryByText('secret dashboard')).not.toBeInTheDocument()
    expect(getApiKey()).toBeNull() // rejected key must not be left in storage
  })
})
