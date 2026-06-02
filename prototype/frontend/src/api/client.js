const BASE = 'http://localhost:8000'
const TOKEN_KEY = 'mingle_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

function authHeaders(extra = {}) {
  const token = getToken()
  const headers = { ...extra }
  if (token) headers['Authorization'] = `Bearer ${token}`
  return headers
}

async function request(path, { method = 'GET', body, isForm = false } = {}) {
  const headers = authHeaders(isForm ? {} : { 'Content-Type': 'application/json' })
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: isForm ? body : body !== undefined ? JSON.stringify(body) : undefined,
  })
  let data = null
  try {
    data = await res.json()
  } catch {
    data = null
  }
  if (!res.ok) {
    // Normalize FastAPI error shape so callers can read `.detail`.
    return { error: true, status: res.status, detail: data?.detail || 'Request failed' }
  }
  return data
}

export const api = {
  // ── Auth ──
  register: (email, displayName, password) =>
    request('/api/auth/register', { method: 'POST', body: { email, displayName, password } }),
  login: (email, password) =>
    request('/api/auth/login', { method: 'POST', body: { email, password } }),

  // ── Profile ──
  getMe: () => request('/api/users/me'),
  updateMe: (patch) => request('/api/users/me', { method: 'PATCH', body: patch }),
  uploadPhoto: (file) => {
    const form = new FormData()
    form.append('file', file)
    return request('/api/users/me/photo', { method: 'POST', body: form, isForm: true })
  },
  getUser: (id) => request(`/api/users/${id}`),
  updateStatus: (id, status) =>
    request(`/api/users/${id}/status`, { method: 'PATCH', body: { status } }),

  // ── Tags ──
  getTags: () => request('/api/tags'),
  subscribeTag: (tagId) => request('/api/users/me/tags', { method: 'POST', body: { tagId } }),
  unsubscribeTag: (tagId) =>
    request(`/api/users/me/tags/${tagId}`, { method: 'DELETE' }),

  // ── Map / Location ──
  getMapUsers: (filters = {}) => {
    const params = new URLSearchParams()
    if (filters.tags?.length) params.set('tags', filters.tags.join(','))
    if (filters.status && filters.status !== 'all') params.set('status', filters.status)
    const qs = params.toString()
    return request(`/api/map/users${qs ? '?' + qs : ''}`)
  },
  updateLocation: (lat, lng, visible) =>
    request('/api/users/me/location', { method: 'PATCH', body: { lat, lng, visible } }),

  // ── Privacy ──
  getBlackoutZones: () => request('/api/privacy/blackout'),
  addBlackoutZone: (zone) => request('/api/privacy/blackout', { method: 'POST', body: zone }),
  deleteBlackoutZone: (id) =>
    request(`/api/privacy/blackout/${id}`, { method: 'DELETE' }),
  getSchedule: () => request('/api/privacy/schedule'),
  putSchedule: (schedule) => request('/api/privacy/schedule', { method: 'PUT', body: schedule }),

  // ── Connections ──
  requestConnection: (toUserId, introMessage = '') =>
    request('/api/connections/request', { method: 'POST', body: { toUserId, introMessage } }),
  getInbox: () => request('/api/connections/requests/inbox'),
  decideRequest: (requestId, accepted) =>
    request(`/api/connections/requests/${requestId}`, { method: 'PATCH', body: { accepted } }),
  getConnections: () => request('/api/connections'),

  // ── Chat ──
  getThreads: () => request('/api/chat/threads'),
  getMessages: (threadId) => request(`/api/chat/threads/${threadId}/messages`),
  sendMessage: (threadId, body) =>
    request(`/api/chat/threads/${threadId}/messages`, { method: 'POST', body: { body } }),

  // ── Streaks / Leaderboard ──
  getStreaks: () => request('/api/streaks'),
  getLeaderboard: () => request('/api/leaderboard'),
}

export function wsUrl(userId) {
  const token = getToken()
  return `ws://localhost:8000/ws/${userId}?token=${encodeURIComponent(token || '')}`
}
