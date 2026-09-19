import { getApiKey } from './auth'
import type {
  Application,
  ApplicationCreateInput,
  StatusEvent,
  StatusEventCreateInput,
  TargetCompany,
  TargetCompanyCreateInput,
} from './types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  headers.set('Content-Type', 'application/json')
  // Read at request time, not a module-level constant -- this must
  // never be a build-time env var (see auth.ts): it's whatever the
  // user entered into ApiKeyGate and stored in their own browser.
  const apiKey = getApiKey()
  if (apiKey) headers.set('Authorization', `Bearer ${apiKey}`)

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
  addStatusEvent: (applicationId: number, data: StatusEventCreateInput) =>
    request<StatusEvent>(`/applications/${applicationId}/events`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getUnmatchedEvents: () => request<StatusEvent[]>('/events/unmatched'),
  linkEvent: (eventId: number, applicationId: number) =>
    request<StatusEvent>(`/events/${eventId}/link`, {
      method: 'PATCH',
      body: JSON.stringify({ application_id: applicationId }),
    }),
  listTargetCompanies: () => request<TargetCompany[]>('/target-companies'),
  createTargetCompany: (data: TargetCompanyCreateInput) =>
    request<TargetCompany>('/target-companies', { method: 'POST', body: JSON.stringify(data) }),
  deleteTargetCompany: (id: number) =>
    request<void>(`/target-companies/${id}`, { method: 'DELETE' }),
}
