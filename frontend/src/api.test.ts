import { afterEach, describe, expect, it, vi } from 'vitest'
import { api } from './api'

describe('api', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('listApplications GETs /applications and returns parsed JSON', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify([{ id: 1, company: 'Acme' }]), { status: 200 }),
    )
    vi.stubGlobal('fetch', fetchMock)

    const result = await api.listApplications()

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/applications'),
      expect.objectContaining({}),
    )
    expect(result).toEqual([{ id: 1, company: 'Acme' }])
  })

  it('createApplication POSTs the payload as JSON', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ id: 1 }), { status: 201 }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await api.createApplication({ company: 'Acme', role: 'SDET' })

    const [, options] = fetchMock.mock.calls[0]
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({ company: 'Acme', role: 'SDET' })
  })

  it('linkEvent PATCHes with the application_id in the body', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ id: 5 }), { status: 200 }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await api.linkEvent(5, 2)

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/events/5/link')
    expect(options.method).toBe('PATCH')
    expect(JSON.parse(options.body)).toEqual({ application_id: 2 })
  })

  it('throws with status and body text on a non-ok response', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response('company is required', { status: 422 }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(api.listApplications()).rejects.toThrow(/422/)
  })
})
