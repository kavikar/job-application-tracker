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

  it('addStatusEvent POSTs status and occurred_at to the events sub-resource', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ id: 9, status: 'rejected' }), { status: 201 }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await api.addStatusEvent(3, { status: 'rejected', occurred_at: '2026-09-17T00:00:00Z' })

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/applications/3/events')
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({
      status: 'rejected',
      occurred_at: '2026-09-17T00:00:00Z',
    })
  })

  it('createTargetCompany POSTs the payload as JSON', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ id: 1, company: 'Toast', tier: 'A' }), { status: 201 }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await api.createTargetCompany({ company: 'Toast', tier: 'A' })

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/target-companies')
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({ company: 'Toast', tier: 'A' })
  })

  it('deleteTargetCompany DELETEs the given id', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }))
    vi.stubGlobal('fetch', fetchMock)

    await api.deleteTargetCompany(7)

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toContain('/target-companies/7')
    expect(options.method).toBe('DELETE')
  })

  it('throws with status and body text on a non-ok response', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response('company is required', { status: 422 }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(api.listApplications()).rejects.toThrow(/422/)
  })
})
