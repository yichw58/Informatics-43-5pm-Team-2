const BASE = 'http://localhost:8000'

async function get(path) {
  const res = await fetch(`${BASE}${path}`)
  return res.json()
}

async function patch(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return res.json()
}

export const api = {
  getTags: () => get('/api/tags'),

  getMapUsers: (filters = {}) => {
    const params = new URLSearchParams()
    if (filters.tags?.length) params.set('tags', filters.tags.join(','))
    if (filters.status && filters.status !== 'all') params.set('status', filters.status)
    const qs = params.toString()
    return get(`/api/map/users${qs ? '?' + qs : ''}`)
  },

  getUser: (id) => get(`/api/users/${id}`),

  updateStatus: (id, status) => patch(`/api/users/${id}/status`, { status }),
}
