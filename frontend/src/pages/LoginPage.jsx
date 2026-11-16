import { useRef, useState } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { AlertCircle, ArrowRight, EyeOff, KeyRound, Shield } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'
import SiteHeader from '../components/SiteHeader'
import { fadeIn, heroLine, panelIn, useHeroParallax } from '../utils/motion'
import './landing.css'

const DEMO_CREDS = [
  { role: 'admin', username: 'admin', loginCode: 'ADMINCODE1' },
  { role: 'hr', username: 'hr_jane', loginCode: 'HRCODE0001' },
  { role: 'intern', username: 'intern_bob', loginCode: 'INTCODE001' },
  { role: 'data engineer', username: 'de_arjun', loginCode: 'DENGCODE01' },
  { role: 'data analyst', username: 'da_meera', loginCode: 'DANACODE01' },
]

const LINES = [
  ['Sign in', 'ink'],
  ['to your', 'ink'],
  ['account.', 'green'],
]

export default function LoginPage() {
  const { login } = useAuth()
  const reduce = useReducedMotion()
  const heroRef = useRef(null)
  useHeroParallax(heroRef)
  const [form, setForm] = useState({ username: '', loginCode: '' })
  const [showCode, setShowCode] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(form.username, form.loginCode)
      toast.success('Welcome back!')
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const quickLogin = async (username, loginCode) => {
    setForm({ username, loginCode })
    setLoading(true)
    setError('')
    try {
      await login(username, loginCode)
      toast.success('Signed in!')
    } catch {
      setError('Quick login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="sa">
      <SiteHeader
        links={[
          { label: 'Home', to: '/landing' },
          { label: 'Log in', to: '/login', active: true, tone: 'end' },
        ]}
      />
      <section ref={heroRef} className="sa-hero sa-login" aria-labelledby="login-title">
        <div className="sa-hero__art" aria-hidden="true"><Shield strokeWidth={0.75} /></div>
        <div className="sa-hero__inner sa-login__inner">
          <div className="sa-hero__copy">
            <motion.span className="sa-eyebrow" {...fadeIn(0.2, { y: 10, duration: 1.2 })}>
              Enterprise governance platform
            </motion.span>
            <h1 id="login-title" className="sa-hero__title">
              {LINES.map(([line, tone], i) => (
                <span className="sa-line" key={line}>
                  <motion.span
                    className={`sa-line__inner ${tone === 'green' ? 'is-green' : ''}`}
                    {...heroLine(i, reduce)}
                  >
                    {line}
                  </motion.span>
                </span>
              ))}
            </h1>
            <motion.p className="sa-hero__lead" {...fadeIn(0.9)}>
              Use the employee code issued by your admin as your password.
            </motion.p>
          </div>

          <motion.div className="sa-panel sa-form" {...panelIn(0.55)}>
            <span className="sa-eyebrow">Account access</span>
            <h2 className="sa-form__title">Sign in</h2>

            {error && (
              <div className="sa-form__error" role="alert"><AlertCircle size={14} /> {error}</div>
            )}

            <form onSubmit={handleSubmit} className="sa-form__fields">
              <label className="sa-field">
                <span>Username</span>
                <input
                  type="text"
                  value={form.username}
                  onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
                  placeholder="your_username"
                  autoComplete="username"
                  required
                />
              </label>
              <label className="sa-field">
                <span>Employee code</span>
                <div className="sa-field__wrap">
                  <input
                    type={showCode ? 'text' : 'password'}
                    value={form.loginCode}
                    onChange={(e) => setForm((f) => ({ ...f, loginCode: e.target.value.toUpperCase() }))}
                    placeholder="YOURCODE01"
                    autoComplete="current-password"
                    className="is-code"
                    required
                  />
                  <button type="button" className="sa-field__eye" onClick={() => setShowCode((v) => !v)} aria-label={showCode ? 'Hide code' : 'Show code'}>
                    {showCode ? <EyeOff size={15} /> : <KeyRound size={15} />}
                  </button>
                </div>
              </label>
              <button type="submit" disabled={loading} className="sa-btn sa-btn--primary sa-btn--lg sa-btn--block">
                {loading ? 'Authenticating…' : 'Sign in'} <span className="sa-btn__badge"><ArrowRight size={16} /></span>
              </button>
            </form>

            <div className="sa-demo">
              <span className="sa-mono sa-demo__label">Quick demo access</span>
              <div className="sa-demo__grid">
                {DEMO_CREDS.map(({ role, username, loginCode }) => (
                  <button type="button" key={role} className="sa-demo__btn" onClick={() => quickLogin(username, loginCode)} disabled={loading}>
                    <b>{role}</b>
                    <span className="sa-mono">{username}</span>
                  </button>
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  )
}
