import api from '../../utils/api'

// Thin wrappers over /api/explorer (backend/app/routes/explorer.py).
export const fetchStats = () => api.get('/explorer/stats').then((r) => r.data)

export const fetchBlocks = (params) =>
  api.get('/explorer/blocks', { params }).then((r) => r.data)

export const fetchBlock = (seq) => api.get(`/explorer/blocks/${seq}`).then((r) => r.data)

// Walks the whole chain server-side; allow longer than the default timeout.
export const verifyChain = () => api.get('/explorer/verify', { timeout: 120000 }).then((r) => r.data)

export const errorMessage = (err, fallback = 'Request failed') =>
  err?.response?.data?.error || err?.message || fallback
