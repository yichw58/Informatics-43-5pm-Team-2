import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useAuth } from '../contexts/AuthContext'

function initials(name) {
  return name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()
}

export default function LeaderboardModal({ onClose }) {
  const { user } = useAuth()
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getLeaderboard().then((d) => {
      setEntries(d?.leaderboard || [])
      setLoading(false)
    })
  }, [])

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal leaderboard-modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>
          ✕
        </button>
        <div className="modal-name" style={{ marginBottom: 16 }}>
          🏆 Leaderboard
        </div>

        {loading ? (
          <div className="empty-tags">Loading…</div>
        ) : entries.length === 0 ? (
          <div className="empty-tags">No streaks yet. Start chatting!</div>
        ) : (
          <div className="leaderboard-list">
            {entries.map((e) => (
              <div
                key={e.id}
                className={`leaderboard-row ${user && e.id === user.id ? 'is-me' : ''}`}
              >
                <span className="lb-rank">#{e.rank}</span>
                <span className="lb-avatar">
                  {e.photoUrl ? (
                    <img
                      className="avatar-img"
                      src={`http://localhost:8000${e.photoUrl}`}
                      alt=""
                    />
                  ) : (
                    initials(e.displayName)
                  )}
                </span>
                <span className="lb-name">{e.displayName}</span>
                <span className="lb-streak">🔥 {e.streak}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
