export type Status =
  | 'applied'
  | 'application_received'
  | 'interview_invite'
  | 'rejected'
  | 'offer'

export interface Application {
  id: number
  company: string
  role: string
  applied_via: string | null
  job_url: string | null
  created_at: string
  current_status: Status
}

export interface StatusEvent {
  id: number
  status: Status
  source: 'manual' | 'gmail'
  raw_email_id: string | null
  created_at: string
}

export interface ApplicationCreateInput {
  company: string
  role: string
  applied_via?: string
  job_url?: string
  applied_at?: string
}

export interface StatusEventCreateInput {
  status: Status
  occurred_at?: string
}
