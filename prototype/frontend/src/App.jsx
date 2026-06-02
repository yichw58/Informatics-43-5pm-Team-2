import { useState, useEffect, useRef, useCallback } from 'react'
import MapView from './components/MapView'
import FilterPanel from './components/FilterPanel'
import UserProfileModal from './components/UserProfileModal'
import OwnProfileModal from './components/OwnProfileModal'
import ChatSidebar from './components/ChatSidebar'
import ConnectionRequestModal from './components/ConnectionRequestModal'
import RequestInbox from './components/RequestInbox'
import LeaderboardModal from './components/LeaderboardModal'
import AuthScreen from './components/AuthScreen'
import StatusToggle from './components/StatusToggle'
import { api, wsUrl } from './api/client'
import { useAuth } from './contexts/AuthContext'
import './App.css'

function initials(name) {
  return name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()
}

export default function App() {
  const { user, setUser, loading, token } = useAuth()
  const [guest, setGuest] = useState(false)

  const [mapUsers, setMapUsers] = useState([])
  const [selectedUser, setSelectedUser] = useState(null)
  const [filters, setFilters] = useState({ tags: [], status: 'all' })
  const [filterOpen, setFilterOpen] = useState(false)
  const [allTags, setAllTags] = useState([])

  const [chatOpen, setChatOpen] = useState(false)
  const [chatFocusThread, setChatFocusThread] = useState(null)
  const [incomingMessage, setIncomingMessage] = useState(null)

  const [ownProfileOpen, setOwnProfileOpen] = useState(false)
  const [leaderboardOpen, setLeaderboardOpen] = useState(false)
  const [inboxOpen, setInboxOpen] = useState(false)
  const [connectTarget, setConnectTarget] = useState(null)

  // connection lookups: { connectedIds: Set<threadId by userId>, pendingIds: Set }
  const [connections, setConnections] = useState({ byUser: {}, pending: new Set() })
  const [inboxCount, setInboxCount] = useState(0)

  const wsRef = useRef(null)

  const refreshConnections = useCallback(() => {
    if (!user) return
    api.getConnections().then((d) => {
      if (d?.error) return
      const byUser = {}
      ;(d.connections || []).forEach((c) => {
        byUser[c.user.id] = c.threadId
      })
      setConnections({ byUser, pending: new Set(d.pendingTo || []) })
    })
  }, [user])

  const refreshInbox = useCallback(() => {
    if (!user) return
    api.getInbox().then((d) => setInboxCount(d?.requests?.length || 0))
  }, [user])

  // Load tags once.
  useEffect(() => {
    api.getTags().then((d) => setAllTags(d.tags || []))
  }, [])

  // Load map + connection state when authenticated or filters change.
  useEffect(() => {
    if (!user) {
      setMapUsers([])
      return
    }
    api.getMapUsers(filters).then((d) => setMapUsers(d.users || []))
  }, [filters, user])

  useEffect(() => {
    refreshConnections()
    refreshInbox()
  }, [refreshConnections, refreshInbox])

  // WebSocket lifecycle — only when authenticated.
  useEffect(() => {
    if (!user || !token) return
    let ws
    try {
      ws = new WebSocket(wsUrl(user.id))
      ws.onmessage = (e) => {
        let msg
        try {
          msg = JSON.parse(e.data)
        } catch {
          return
        }
        switch (msg.event) {
          case 'status_update':
            setMapUsers((prev) =>
              prev.map((u) => (u.id === msg.userId ? { ...u, status: msg.status } : u))
            )
            break
          case 'location_update':
            setMapUsers((prev) =>
              prev.map((u) =>
                u.id === msg.userId ? { ...u, lat: msg.lat, lng: msg.lng } : u
              )
            )
            break
          case 'user_offline':
            setMapUsers((prev) => prev.filter((u) => u.id !== msg.userId))
            break
          case 'connection_request':
            refreshInbox()
            break
          case 'connection_accepted':
            refreshConnections()
            setChatFocusThread(msg.threadId)
            break
          case 'connection_declined':
            refreshConnections()
            break
          case 'chat_message':
            setIncomingMessage({ ...msg, _ts: Date.now() })
            break
          default:
            break
        }
      }
      ws.onerror = () => {}
    } catch {
      /* backend may not be running */
    }
    wsRef.current = ws
    return () => ws?.close()
  }, [user, token, refreshConnections, refreshInbox])

  const handleStatusToggle = async (newStatus) => {
    const res = await api.updateStatus(user.id, newStatus)
    if (!res.error) setUser({ ...user, status: newStatus })
  }

  const connectionStateFor = (u) => {
    if (connections.byUser[u.id]) {
      return { status: 'connected', threadId: connections.byUser[u.id] }
    }
    if (connections.pending.has(u.id)) return { status: 'pending' }
    return { status: 'none' }
  }

  const openChatThread = (threadId) => {
    setSelectedUser(null)
    setChatFocusThread(threadId)
    setChatOpen(true)
  }

  // ── Auth gate ──
  if (loading) {
    return <div className="auth-loading">Loading…</div>
  }

  if (!user && !guest) {
    return <AuthScreen onGuest={() => setGuest(true)} />
  }

  const isGuest = !user && guest

  return (
    <div className="app">
      <header className="app-header">
        <span className="app-logo">MINGLE</span>
        <div className="header-right">
          {!isGuest && (
            <>
              <button
                className="nav-icon-btn"
                title="Messages"
                onClick={() => {
                  setChatFocusThread(null)
                  setChatOpen((v) => !v)
                }}
              >
                💬
              </button>
              <button
                className={`nav-icon-btn ${inboxCount > 0 ? 'has-badge' : ''}`}
                title="Requests"
                onClick={() => setInboxOpen(true)}
              >
                🔔
                {inboxCount > 0 && <span className="nav-badge">{inboxCount}</span>}
              </button>
              <StatusToggle status={user.status} onChange={handleStatusToggle} />
            </>
          )}
          <button
            className={`filter-toggle-btn ${filterOpen ? 'active' : ''}`}
            onClick={() => setFilterOpen((v) => !v)}
          >
            {filterOpen ? '✕ Filters' : '⚙ Filters'}
          </button>
          {!isGuest && (
            <>
              <button
                className="nav-icon-btn"
                title="Leaderboard"
                onClick={() => setLeaderboardOpen(true)}
              >
                🏆
              </button>
              <button
                className="nav-avatar"
                title="Profile"
                onClick={() => setOwnProfileOpen(true)}
              >
                {user.photoUrl ? (
                  <img
                    className="avatar-img"
                    src={`http://localhost:8000${user.photoUrl}`}
                    alt=""
                  />
                ) : (
                  initials(user.displayName)
                )}
              </button>
            </>
          )}
        </div>
      </header>

      <div className="app-body">
        {filterOpen && (
          <FilterPanel tags={allTags} filters={filters} onChange={setFilters} />
        )}

        <div className="map-wrapper">
          <MapView
            currentUser={isGuest ? null : user}
            users={mapUsers}
            onUserClick={isGuest ? () => {} : setSelectedUser}
          />
          {isGuest && (
            <div className="guest-banner">
              Sign in to see nearby users and connect.
            </div>
          )}
        </div>

        {chatOpen && !isGuest && (
          <ChatSidebar
            focusThreadId={chatFocusThread}
            incomingMessage={incomingMessage}
            onClose={() => setChatOpen(false)}
          />
        )}
      </div>

      {selectedUser && !isGuest && (
        <UserProfileModal
          user={selectedUser}
          allTags={allTags}
          connectionState={connectionStateFor(selectedUser)}
          onClose={() => setSelectedUser(null)}
          onConnect={(u) => {
            setSelectedUser(null)
            setConnectTarget(u)
          }}
          onOpenChat={openChatThread}
        />
      )}

      {connectTarget && (
        <ConnectionRequestModal
          target={connectTarget}
          onClose={() => setConnectTarget(null)}
          onSent={() => refreshConnections()}
        />
      )}

      {inboxOpen && !isGuest && (
        <RequestInbox
          onClose={() => {
            setInboxOpen(false)
            refreshInbox()
          }}
          onResolved={() => {
            refreshConnections()
            refreshInbox()
          }}
        />
      )}

      {ownProfileOpen && !isGuest && (
        <OwnProfileModal allTags={allTags} onClose={() => setOwnProfileOpen(false)} />
      )}

      {leaderboardOpen && (
        <LeaderboardModal onClose={() => setLeaderboardOpen(false)} />
      )}
    </div>
  )
}
