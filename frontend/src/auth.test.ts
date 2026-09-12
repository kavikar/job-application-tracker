import { afterEach, describe, expect, it } from 'vitest'
import { clearApiKey, getApiKey, setApiKey } from './auth'

afterEach(() => {
  localStorage.clear()
})

describe('auth', () => {
  it('returns null when nothing is stored', () => {
    expect(getApiKey()).toBeNull()
  })

  it('round-trips a stored key', () => {
    setApiKey('my-secret-key')
    expect(getApiKey()).toBe('my-secret-key')
  })

  it('clearApiKey removes the stored key', () => {
    setApiKey('my-secret-key')
    clearApiKey()
    expect(getApiKey()).toBeNull()
  })
})
