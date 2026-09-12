import type { Application, ApplicationCreateInput, StatusEvent } from './types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
// Not checked by the backend until Phase 7 -- attaching it now is a
// no-op until then, same reasoning as the GitHub Actions workflow in
// Phase 5 referencing secrets that don't exist yet.
const API_KEY = import.meta.env.VITE_API_KEY

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  headers.set('Content-Type', 'application/json')
  if (API_KEY) headers.set('Authorization', `Bearer ${API_KEY}`)

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })
  if (!response.ok) {
    const body = await response.text()
    throw new Error(`${options.method ?? 'GET'} ${path} failed: ${response.status} ${body}`)
  }
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export const api = {
  listApplications: () => request<Application[]>('/applications'),
  createApplication: (data: ApplicationCreateInput) =>
    request<Application>('/applications', { method: 'POST', body: JSON.stringify(data) }),
  getApplicationEvents: (applicationId: number) =>
    request<StatusEvent[]>(`/applications/${applicationId}/events`),
  getUnmatchedEvents: () => request<StatusEvent[]>('/events/unmatched'),
  linkEvent: (eventId: number, applicationId: number) =>
    request<StatusEvent>(`/events/${eventId}/link`, {
      method: 'PATCH',
      body: JSON.stringify({ application_id: applicationId }),
    }),
}
