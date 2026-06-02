import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useAuth } from '../contexts/AuthContext'

export default function LocationPrivacyModal({ onClose }) {
  const { user, setUser } = useAuth()
  const [zones, setZones] = useState([])
  const [schedule, setSchedule] = useState({
    shareFrom: '08:00',
    shareUntil: '22:00',
    enabled: false,
  })
  const [form, setForm] = useState({ label: '', lat: '', lng: '', radius: '0.2' })
  const [error, setError] = useState('')

  useEffect(() => {
    api.getBlackoutZones().then((d) => setZones(d?.zones || []))
    api.getSchedule().then((d) => {
      if (d && !d.error) setSchedule(d)
    })
  }, [])

  const toggleShare = async () => {
    const next = !user.locationVisible
    const res = await api.updateLocation(user.lat, user.lng, next)
    if (!res.error) setUser(res)
  }

  const addZone = async () => {
    setError('')
    const lat = parseFloat(form.lat)
    const lng = parseFloat(form.lng)
    const radius = parseFloat(form.radius)
    if (Number.isNaN(lat) || Number.isNaN(lng)) {
      setError('Latitude and longitude must be numbers.')
      return
    }
    const res = await api.addBlackoutZone({
      label: form.label.trim() || 'Zone',
      centerLat: lat,
      centerLng: lng,
      radiusMiles: Number.isNaN(radius) ? 0.2 : radius,
    })
    if (res.error) {
      setError(res.detail)
      return
    }
    setZones((prev) => [...prev, res])
    setForm({ label: '', lat: '', lng: '', radius: '0.2' })
  }

  const deleteZone = async (id) => {
    const res = await api.deleteBlackoutZone(id)
    if (!res.error) setZones((prev) => prev.filter((z) => z.id !== id))
  }

  const saveSchedule = async (next) => {
    setSchedule(next)
    await api.putSchedule(next)
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal privacy-modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>
          ✕
        </button>
        <div className="modal-name" style={{ marginBottom: 18 }}>
          Location Privacy
        </div>

        <div className="own-section-head">
          <span className="filter-title">Share my location</span>
          <label className="switch">
            <input
              type="checkbox"
              checked={!!user.locationVisible}
              onChange={toggleShare}
            />
            <span className="slider" />
          </label>
        </div>

        <div className="filter-title" style={{ margin: '18px 0 8px' }}>
          Blackout zones
        </div>
        <div className="zone-list">
          {zones.length === 0 ? (
            <span className="empty-tags">No blackout zones.</span>
          ) : (
            zones.map((z) => (
              <div key={z.id} className="zone-item">
                <div>
                  <div className="zone-label">{z.label}</div>
                  <div className="zone-coords">
                    {z.centerLat.toFixed(4)}, {z.centerLng.toFixed(4)} · {z.radiusMiles} mi
                  </div>
                </div>
                <button className="zone-del" onClick={() => deleteZone(z.id)}>
                  ✕
                </button>
              </div>
            ))
          )}
        </div>

        <div className="zone-form">
          <input
            className="auth-input"
            placeholder="Label (e.g. Home)"
            value={form.label}
            onChange={(e) => setForm({ ...form, label: e.target.value })}
          />
          <div className="zone-form-row">
            <input
              className="auth-input"
              placeholder="Lat"
              value={form.lat}
              onChange={(e) => setForm({ ...form, lat: e.target.value })}
            />
            <input
              className="auth-input"
              placeholder="Lng"
              value={form.lng}
              onChange={(e) => setForm({ ...form, lng: e.target.value })}
            />
            <input
              className="auth-input"
              placeholder="Radius (mi)"
              value={form.radius}
              onChange={(e) => setForm({ ...form, radius: e.target.value })}
            />
          </div>
          {error && <div className="auth-error">{error}</div>}
          <button className="inline-save" onClick={addZone}>
            Add zone
          </button>
        </div>

        <div className="filter-title" style={{ margin: '18px 0 8px' }}>
          Time schedule
        </div>
        <div className="own-section-head">
          <span style={{ fontSize: 14 }}>Only share during set hours</span>
          <label className="switch">
            <input
              type="checkbox"
              checked={schedule.enabled}
              onChange={(e) => saveSchedule({ ...schedule, enabled: e.target.checked })}
            />
            <span className="slider" />
          </label>
        </div>
        <div className="schedule-row">
          <label>
            From
            <input
              type="time"
              className="auth-input"
              value={schedule.shareFrom}
              onChange={(e) => saveSchedule({ ...schedule, shareFrom: e.target.value })}
            />
          </label>
          <label>
            Until
            <input
              type="time"
              className="auth-input"
              value={schedule.shareUntil}
              onChange={(e) => saveSchedule({ ...schedule, shareUntil: e.target.value })}
            />
          </label>
        </div>
      </div>
    </div>
  )
}
