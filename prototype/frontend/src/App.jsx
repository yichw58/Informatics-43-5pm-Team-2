import { useState, useEffect, useRef, useCallback } from 'react'
import MapView from './components/MapView'
import FilterPanel from './components/FilterPanel'
import UserProfileModal from './components/UserProfileModal'
import StatusToggle from './components/StatusToggle'
import { api } from './api/client'
import './App.css'

const ME = 'usr_me'

export default function App() {
  const [currentUser, setCurrentUser]   = useState(null)
  const [mapUsers, setMapUsers]         = useState([])
  const [selectedUser, setSelectedUser] = useState(null)
  const [filters, setFilters]           = useState({ tags: [], status: 'all' })
  const [filterOpen, setFilterOpen]     = useState(false)
  const [allTags, setAllTags]           = useState([])
  const wsRef = useRef(null)

  // Initial load
  useEffect(() => {
    api.getUser(ME).then(setCurrentUser)
    api.getTags().then((d) => setAllTags(d.tags || []))
  }, [])

  // Re-fetch map users when filters change
  useEffect(() => {
    api.getMapUsers(filters).then((d) => setMapUsers(d.users || []))
  }, [filters])

  // WebSocket — live status updates
  useEffect(() => {
    let ws
    try {
      ws = new WebSocket(`ws://localhost:8000/ws/${ME}`)
      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data)
        if (msg.event === 'status_update') {
          setMapUsers((prev) =>
            prev.map((u) => (u.id === msg.userId ? { ...u, status: msg.status } : u))
          )
        }
      }
      ws.onerror = () => {} // silent fail — backend may not be running yet
    } catch (_) {}
    wsRef.current = ws
    return () => ws?.close()
  }, [])

  const handleStatusToggle = async (newStatus) => {
    await api.updateStatus(ME, newStatus)
    setCurrentUser((prev) => ({ ...prev, status: newStatus }))
  }

  const noResults = mapUsers.length === 0 &&
    (filters.tags.length > 0 || filters.status !== 'all')

  return (
    <div className="app">
      <header className="app-header">
        <span className="app-logo">MINGLE</span>
        <div className="header-right">
          {currentUser && (
            <StatusToggle status={currentUser.status} onChange={handleStatusToggle} />
          )}
          <button
            className={`filter-toggle-btn ${filterOpen ? 'active' : ''}`}
            onClick={() => setFilterOpen((v) => !v)}
          >
            {filterOpen ? '✕ Filters' : '⚙ Filters'}
          </button>
        </div>
      </header>

      <div className="app-body">
        {filterOpen && (
          <FilterPanel tags={allTags} filters={filters} onChange={setFilters} />
        )}
        <div className="map-wrapper">
          <MapView
            currentUser={currentUser}
            users={mapUsers}
            onUserClick={setSelectedUser}
          />
          {noResults && (
            <div className="no-results-banner">
              No users match your filters nearby.
            </div>
          )}
        </div>
      </div>

      {selectedUser && (
        <UserProfileModal
          user={selectedUser}
          allTags={allTags}
          onClose={() => setSelectedUser(null)}
        />
      )}
    </div>
  )
}
