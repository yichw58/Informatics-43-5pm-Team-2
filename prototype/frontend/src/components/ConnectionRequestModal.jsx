import { useState } from 'react'
import { api } from '../api/client'

function initials(name) {
  return name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()
}

const MAX = 100

export default function ConnectionRequestModal({ target, onClose, onSent }) {
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const send = async () => {
    setError('')
    setBusy(true)
    const res = await api.requestConnection(target.id, message)
    setBusy(false)
    if (res.error) {
      setError(res.detail)
      return
    }
    onSent?.(res)
    onClose()
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>
          ✕
        </button>

        <div className="modal-avatar">
          {target.photoUrl ? (
            <img className="avatar-img" src={`http://localhost:8000${target.photoUrl}`} alt="" />
          ) : (
            initials(target.displayName)
          )}
        </div>
        <div className="modal-name">{target.displayName}</div>

        <div className="filter-title" style={{ marginBottom: 6 }}>
          Add a message (optional)
        </div>
        <textarea
          className="intro-textarea"
          value={message}
          maxLength={MAX}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Hey! Want to grab coffee?"
        />
        <div className="char-counter">
          {message.length}/{MAX}
        </div>

        {error && <div className="auth-error">{error}</div>}

        <button className="connect-send-btn" onClick={send} disabled={busy}>
          {busy ? 'Sending…' : 'Send Request'}
        </button>
      </div>
    </div>
  )
}
