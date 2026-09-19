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

export type Tier = 'A' | 'B' | 'C' | 'D'

export interface TargetCompany {
  id: number
  company: string
  tier: Tier
  category: string | null
  notes: string | null
  created_at: string
  // Computed server-side by cross-referencing applications -- not
  // something this client sets or edits directly.
  already_applied: boolean
}

export interface TargetCompanyCreateInput {
  company: string
  tier: Tier
  category?: string
  notes?: string
}
