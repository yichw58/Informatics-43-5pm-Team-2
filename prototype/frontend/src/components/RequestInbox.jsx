import { useEffect, useState } from 'react'
import { api } from '../api/client'

function initials(name) {
  return name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()
}

export default function RequestInbox({ onClose, onResolved }) {
  const [requests, setRequests] = useState([])
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState(null)
  const [notice, setNotice] = useState('')

  const load = () => {
    setLoading(true)
    api.getInbox().then((d) => {
      setRequests(d?.requests || [])
      setLoading(false)
    })
  }

  useEffect(load, [])

  const decide = async (req, accepted) => {
    setBusyId(req.id)
    const res = await api.decideRequest(req.id, accepted)
    setBusyId(null)
    if (res.error) {
      setNotice(res.detail)
      return
    }
    setRequests((prev) => prev.filter((r) => r.id !== req.id))
    if (!accepted) {
      setNotice(`${req.fromUser.displayName} cannot request you again for 24 hours.`)
    }
    onResolved?.(req, accepted, res)
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal inbox-modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>
          ✕
        </button>
        <div className="modal-name" style={{ marginBottom: 16 }}>
          Connection Requests
        </div>

        {notice && <div className="inbox-notice">{notice}</div>}

        {loading ? (
          <div className="empty-tags">Loading…</div>
        ) : requests.length === 0 ? (
          <div className="empty-tags">No pending requests.</div>
        ) : (
          <div className="inbox-list">
            {requests.map((req) => (
              <div key={req.id} className="inbox-item">
                <div className="inbox-avatar">
                  {req.fromUser.photoUrl ? (
                    <img
                      className="avatar-img"
                      src={`http://localhost:8000${req.fromUser.photoUrl}`}
                      alt=""
                    />
                  ) : (
                    initials(req.fromUser.displayName)
                  )}
                </div>
                <div className="inbox-body">
                  <div className="inbox-name">{req.fromUser.displayName}</div>
                  {req.introMessage && (
                    <div className="inbox-message">“{req.introMessage}”</div>
                  )}
                  <div className="inbox-actions">
                    <button
                      className="inbox-accept"
                      disabled={busyId === req.id}
                      onClick={() => decide(req, true)}
                    >
                      Accept
                    </button>
                    <button
                      className="inbox-decline"
                      disabled={busyId === req.id}
                      onClick={() => decide(req, false)}
                    >
                      Decline
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
