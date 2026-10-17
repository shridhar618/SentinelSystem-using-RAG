import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

const token = localStorage.getItem('token')
if (token) {
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

// Phase 21: the backend now expires JWTs after a configurable window
// (previously they never expired at all). Without this, a token expiring
// mid-session would fail silently wherever the next request happened to be
// made, with no clear path back to a working state for the user. Login
// itself is excluded -- a wrong-password 401 there is a normal login
// failure, not a session expiring, and should surface as a form error
// rather than force a redirect loop back to the login page.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const isLoginRequest = error.config?.url?.includes('/auth/login')
    if (error.response?.status === 401 && !isLoginRequest) {
      localStorage.removeItem('token')
      delete api.defaults.headers.common['Authorization']
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api
