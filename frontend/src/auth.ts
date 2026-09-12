// The API key must never be baked into the build: VITE_-prefixed env
// vars are inlined into the shipped JS bundle at build time, which
// anyone visiting the deployed site could read straight out of
// devtools. Instead it's entered by the user at runtime (ApiKeyGate)
// and kept only in their own browser's localStorage.
const STORAGE_KEY = 'job-tracker-api-key'

export function getApiKey(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY)
  } catch {
    return null
  }
}

export function setApiKey(key: string): void {
  try {
    localStorage.setItem(STORAGE_KEY, key)
  } catch {
    // localStorage unavailable (private browsing, storage disabled) --
    // the key just won't persist across reloads; not worth failing over.
  }
}

export function clearApiKey(): void {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch {
    // no-op
  }
}
