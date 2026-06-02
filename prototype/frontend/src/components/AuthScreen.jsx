import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import LoginModal from './LoginModal'

export default function AuthScreen({ onGuest }) {
  const { register } = useAuth()
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [showLogin, setShowLogin] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    if (!displayName.trim()) return setError('Display name is required.')
    if (password.length < 6) return setError('Password must be at least 6 characters.')
    if (password !== confirm) return setError('Passwords do not match.')
    setBusy(true)
    const res = await register(email.trim(), displayName.trim(), password)
    setBusy(false)
    if (!res.ok) setError(res.error)
  }

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <div className="auth-logo">MINGLE</div>
        <div className="auth-subtitle">Discover people nearby</div>

        <form onSubmit={submit} className="auth-form">
          <label className="auth-label">Display name</label>
          <input
            className="auth-input"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="Your name"
          />

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
            placeholder="At least 6 characters"
            required
          />

          <label className="auth-label">Confirm password</label>
          <input
            className="auth-input"
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder="Re-enter password"
            required
          />

          {error && <div className="auth-error">{error}</div>}

          <button className="auth-submit" type="submit" disabled={busy}>
            {busy ? 'Creating account…' : 'CREATE ACCOUNT'}
          </button>
        </form>

        <div className="auth-switch">
          Already a member?{' '}
          <button className="auth-link" onClick={() => setShowLogin(true)}>
            LOG IN
          </button>
        </div>
      </div>

      {showLogin && (
        <LoginModal onClose={() => setShowLogin(false)} onGuest={onGuest} />
      )}
    </div>
  )
}
