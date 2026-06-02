import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

export default function LoginModal({ onClose, onGuest }) {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setBusy(true)
    const res = await login(email.trim(), password)
    setBusy(false)
    if (!res.ok) setError(res.error)
    // On success AuthProvider re-renders App away from the auth screen.
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>
          ✕
        </button>
        <div className="modal-name" style={{ marginBottom: 18 }}>
          Log in
        </div>

        <form onSubmit={submit} className="auth-form">
          <label className="auth-label">Email</label>
          <input
            className="auth-input"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@uci.edu"
            required
          />

          <label className="auth-label">Password</label>
          <input
            className="auth-input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            required
          />

          {error && <div className="auth-error">{error}</div>}

          <button className="auth-submit" type="submit" disabled={busy}>
            {busy ? 'Logging in…' : 'LOG IN'}
          </button>
        </form>

        {onGuest && (
          <button
            className="auth-guest-link"
            onClick={() => {
              onGuest()
              onClose()
            }}
          >
            View map without signing in
          </button>
        )}
      </div>
    </div>
  )
}
