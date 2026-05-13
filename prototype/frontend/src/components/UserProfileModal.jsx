function initials(name) {
  return name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()
}

export default function UserProfileModal({ user, allTags, onClose }) {
  const tagMap = Object.fromEntries(allTags.map((t) => [t.id, t]))

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>✕</button>

        <div className="modal-avatar">{initials(user.displayName)}</div>

        <div className="modal-name">{user.displayName}</div>

        <div style={{ textAlign: 'center', marginBottom: 14 }}>
          <span className={`status-badge ${user.status}`}>
            {user.status === 'open' ? '🟢 Open to Meet' : '⚫ Busy'}
          </span>
        </div>

        <div className="filter-title" style={{ marginBottom: 6 }}>Bio</div>
        <div className="modal-bio">
          {user.bio || 'This user has not written a bio yet.'}
        </div>

        <div className="filter-title" style={{ marginBottom: 8 }}>Interests</div>
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
