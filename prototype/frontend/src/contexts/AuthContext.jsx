import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { api, setToken, getToken } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setTokenState] = useState(getToken())
  const [loading, setLoading] = useState(true)

  // Rehydrate from stored token on mount.
  useEffect(() => {
    const stored = getToken()
    if (!stored) {
      setLoading(false)
      return
    }
    api
      .getMe()
      .then((u) => {
        if (u && u.id) setUser(u)
        else logout()
      })
      .catch(() => logout())
      .finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const login = useCallback(async (email, password) => {
    const res = await api.login(email, password)
    if (res.token) {
      setToken(res.token)
      setTokenState(res.token)
      setUser(res.user)
      return { ok: true }
    }
    return { ok: false, error: res.detail || 'Login failed' }
  }, [])

  const register = useCallback(async (email, displayName, password) => {
    const res = await api.register(email, displayName, password)
    if (res.token) {
      setToken(res.token)
      setTokenState(res.token)
      setUser(res.user)
      return { ok: true }
    }
    return { ok: false, error: res.detail || 'Registration failed' }
  }, [])

  const logout = useCallback(() => {
    setToken(null)
    setTokenState(null)
    setUser(null)
  }, [])

  const value = { user, setUser, token, loading, login, register, logout }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
