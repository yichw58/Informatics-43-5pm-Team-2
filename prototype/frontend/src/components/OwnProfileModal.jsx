import { useRef, useState } from 'react'
import { api } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import LocationPrivacyModal from './LocationPrivacyModal'

function initials(name) {
  return name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()
}

export default function OwnProfileModal({ allTags, onClose }) {
  const { user, setUser, logout } = useAuth()
  const fileRef = useRef(null)
  const [editingName, setEditingName] = useState(false)
  const [editingBio, setEditingBio] = useState(false)
  const [nameDraft, setNameDraft] = useState(user.displayName)
  const [bioDraft, setBioDraft] = useState(user.bio || '')
  const [showTagPicker, setShowTagPicker] = useState(false)
  const [showPrivacy, setShowPrivacy] = useState(false)

  const tagMap = Object.fromEntries(allTags.map((t) => [t.id, t]))
  const available = allTags.filter((t) => !user.tags.includes(t.id))

  const saveName = async () => {
    const updated = await api.updateMe({ displayName: nameDraft.trim() })
    if (!updated.error) setUser(updated)
    setEditingName(false)
  }

  const saveBio = async () => {
    const updated = await api.updateMe({ bio: bioDraft })
    if (!updated.error) setUser(updated)
    setEditingBio(false)
  }

  const onPhoto = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    const res = await api.uploadPhoto(file)
    if (!res.error) {
      // Cache-bust so the new image shows immediately.
      setUser({ ...user, photoUrl: `${res.photoUrl}?t=${Date.now()}` })
    }
  }

  const addTag = async (tagId) => {
    const res = await api.subscribeTag(tagId)
    if (!res.error) setUser({ ...user, tags: res.tags })
  }

  const removeTag = async (tagId) => {
    const res = await api.unsubscribeTag(tagId)
    if (!res.error) setUser({ ...user, tags: res.tags })
  }

  const toggleVisibility = async () => {
    const next = !user.locationVisible
    const res = await api.updateLocation(user.lat, user.lng, next)
    if (!res.error) setUser(res)
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal own-profile" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>
          ✕
        </button>

        <div className="own-photo-wrap">
          <div className="modal-avatar own-avatar">
            {user.photoUrl ? (
              <img className="avatar-img" src={`http://localhost:8000${user.photoUrl}`} alt="" />
            ) : (
              initials(user.displayName)
            )}
          </div>
          <button className="photo-add-btn" onClick={() => fileRef.current?.click()}>
            ＋
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            onChange={onPhoto}
          />
        </div>

        <div className="own-name-row">
          {editingName ? (
            <>
              <input
                className="inline-edit-input"
                value={nameDraft}
                onChange={(e) => setNameDraft(e.target.value)}
              />
              <button className="inline-save" onClick={saveName}>
                Save
              </button>
            </>
          ) : (
            <>
              <span className="modal-name" style={{ margin: 0 }}>
                {user.displayName}
              </span>
              <button className="pencil-btn" onClick={() => setEditingName(true)}>
                ✎
              </button>
            </>
          )}
        </div>

        <div className="own-section">
          <div className="own-section-head">
            <span className="filter-title">Bio</span>
            {!editingBio && (
              <button className="pencil-btn" onClick={() => setEditingBio(true)}>
                ✎
              </button>
            )}
          </div>
          {editingBio ? (
            <>
              <textarea
                className="bio-edit"
                value={bioDraft}
                onChange={(e) => setBioDraft(e.target.value)}
                maxLength={500}
              />
              <button className="inline-save" onClick={saveBio}>
                Save bio
              </button>
            </>
          ) : (
            <div className="modal-bio">
              {user.bio || 'Add a short bio so people know what you’re into.'}
            </div>
          )}
        </div>

        <div className="own-section">
          <div className="own-section-head">
            <span className="filter-title">Interests</span>
            <button className="pencil-btn" onClick={() => setShowTagPicker((v) => !v)}>
              ＋
            </button>
          </div>
          <div className="modal-tags">
            {user.tags.length === 0 ? (
              <span className="empty-tags">No interests yet.</span>
            ) : (
              user.tags.map((id) => {
                const tag = tagMap[id]
                return tag ? (
                  <span key={id} className="tag-chip removable">
                    {tag.emoji} #{tag.name}
                    <button className="tag-x" onClick={() => removeTag(id)}>
                      ✕
                    </button>
                  </span>
                ) : null
              })
            )}
          </div>
          {showTagPicker && (
            <div className="tag-picker">
              {available.length === 0 ? (
                <span className="empty-tags">All interests added.</span>
              ) : (
                available.map((t) => (
                  <button key={t.id} className="tag-chip" onClick={() => addTag(t.id)}>
                    {t.emoji} #{t.name}
                  </button>
                ))
              )}
            </div>
          )}
        </div>

        <div className="own-section">
          <div className="own-section-head">
            <span className="filter-title">Location sharing</span>
            <label className="switch">
              <input
                type="checkbox"
                checked={!!user.locationVisible}
                onChange={toggleVisibility}
              />
              <span className="slider" />
            </label>
          </div>
          <button className="link-btn" onClick={() => setShowPrivacy(true)}>
            Privacy & blackout zones →
          </button>
        </div>

        <button className="logout-btn" onClick={logout}>
          Log out
        </button>
      </div>

      {showPrivacy && <LocationPrivacyModal onClose={() => setShowPrivacy(false)} />}
    </div>
  )
}
