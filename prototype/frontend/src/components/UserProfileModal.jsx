function initials(name) {
  return name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()
}

export default function UserProfileModal({
  user,
  allTags,
  connectionState,
  onClose,
  onConnect,
  onOpenChat,
}) {
  const tagMap = Object.fromEntries(allTags.map((t) => [t.id, t]))

  // connectionState: { status: 'none' | 'pending' | 'connected', threadId? }
  const status = connectionState?.status || 'none'

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>
          ✕
        </button>

        <div className="modal-avatar">
          {user.photoUrl ? (
            <img className="avatar-img" src={`http://localhost:8000${user.photoUrl}`} alt="" />
          ) : (
            initials(user.displayName)
          )}
        </div>

        <div className="modal-name">{user.displayName}</div>

        <div style={{ textAlign: 'center', marginBottom: 14 }}>
          <span className={`status-badge ${user.status}`}>
            {user.status === 'open' ? '🟢 Open to Meet' : '⚫ Busy'}
          </span>
        </div>

        <div className="connection-action">
          {status === 'connected' ? (
            <>
              <button className="conn-btn connected" disabled>
                ✓ Connected
              </button>
              <button
                className="conn-btn open-chat"
                onClick={() => onOpenChat?.(connectionState.threadId)}
              >
                Open Chat
              </button>
            </>
          ) : status === 'pending' ? (
            <button className="conn-btn pending" disabled>
              🕓 Request Sent
            </button>
          ) : (
            <button className="conn-btn connect" onClick={() => onConnect?.(user)}>
              ＋ Connect
            </button>
          )}
        </div>

        <div className="filter-title" style={{ marginBottom: 6 }}>
          Bio
        </div>
        <div className="modal-bio">
          {user.bio || 'This user has not written a bio yet.'}
        </div>

        <div className="filter-title" style={{ marginBottom: 8 }}>
          Interests
        </div>
        <div className="modal-tags">
          {user.tags.length === 0 ? (
            <span className="empty-tags">No interests added.</span>
          ) : (
            user.tags.map((id) => {
              const tag = tagMap[id]
              return tag ? (
                <span key={id} className="tag-chip">
                  {tag.emoji} #{tag.name}
                </span>
              ) : null
            })
          )}
        </div>
      </div>
    </div>
  )
}
