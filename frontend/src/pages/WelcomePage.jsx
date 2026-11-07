import { motion, useReducedMotion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, BarChart3, Cpu, Lock, MessageSquare, Shield } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { getRoleMeta } from '../utils/roles'
import SiteHeader from '../components/SiteHeader'
import { useRef } from 'react'
import { fadeIn, heroLine, revealIn, useHeroParallax } from '../utils/motion'
import './landing.css'

const ROLE_COPY = {
  admin: { badge: 'Admin access', tagline: 'Full system access · Audit logs · Governance controls' },
  hr: { badge: 'HR access', tagline: 'People data · Compliance workflows · PII-safe AI' },
  intern: { badge: 'Intern access', tagline: 'Governed AI access · Company knowledge · Secure comms' },
}

const FEATURE_CARDS = [
  { icon: Cpu, label: 'AI Chatbot', desc: 'Policy-grounded answers, governed by role-based access.', to: '/chat' },
  { icon: Lock, label: 'Zero Trust', desc: 'Every request is filtered by role before it is answered.', to: '/my-dashboard' },
  { icon: MessageSquare, label: 'Secure Messages', desc: 'Private, real-time internal communication.', to: '/messages' },
  { icon: BarChart3, label: 'Audit Trail', desc: 'Every query and decision is logged and traceable.', to: '/my-dashboard' },
]


export default function WelcomePage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const reduce = useReducedMotion()
  const heroRef = useRef(null)
  useHeroParallax(heroRef)
  const role = user?.role || 'intern'
  const roleMeta = getRoleMeta(role)
  const copy = ROLE_COPY[role] || { badge: `${roleMeta.label} access`, tagline: `${roleMeta.desc} · Secure comms · Governed AI` }
  const name = user?.username || 'there'

  const lines = [
    ['Welcome', 'ink'],
    ['back,', 'ink'],
    [`${name}.`, 'green'],
  ]

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="sa">
      <SiteHeader
        links={[
          { label: 'Welcome', to: '/welcome', active: true },
          { label: 'My dashboard', to: '/my-dashboard' },
          { label: 'Assistant', to: '/chat' },
          { label: 'Messages', to: '/messages' },
          { label: 'Sign out', onClick: handleLogout, tone: 'end' },
        ]}
      />
      <main>
        <section ref={heroRef} className="sa-hero" aria-labelledby="welcome-title">
          <div className="sa-hero__art" aria-hidden="true"><Shield strokeWidth={0.75} /></div>
          <div className="sa-hero__inner">
            <div className="sa-hero__copy">
              <motion.span className="sa-eyebrow" {...fadeIn(0.2, { y: 10, duration: 1.2 })}>
                {copy.badge}
              </motion.span>
              <h1 id="welcome-title" className="sa-hero__title">
                {lines.map(([line, tone], i) => (
                  <span className="sa-line" key={i}>
                    <motion.span
                      className={`sa-line__inner ${tone === 'green' ? 'is-green' : ''}`}
                      {...heroLine(i, reduce)}
                    >
                      {line}
                    </motion.span>
                  </span>
                ))}
              </h1>
              <motion.p className="sa-hero__lead" {...fadeIn(1)}>
                SecureAI Governance Platform — {copy.tagline}.
              </motion.p>
              <motion.div className="sa-hero__ctas" {...fadeIn(1.2)}>
                <button type="button" className="sa-btn sa-btn--primary sa-btn--lg" onClick={() => navigate('/my-dashboard', { replace: true })}>
                  Get started <span className="sa-btn__badge"><ArrowRight size={16} /></span>
                </button>
                <button type="button" className="sa-btn sa-btn--ghost sa-btn--lg" onClick={() => navigate('/chat')}>
                  Ask the assistant
                </button>
              </motion.div>
            </div>
          </div>
          <div className="sa-hero__bar">
            <span><Shield size={14} /> Signed in as {roleMeta.label}</span>
            <span className="sa-hide-sm">RBAC governed · Zero trust · Audit logged</span>
            <span className="sa-hide-sm">{user?.email}</span>
          </div>
        </section>

        <section className="sa-section">
          <div className="sa-shell">
            <div className="sa-head">
              <span className="sa-eyebrow">Your workspace</span>
              <h2 className="sa-h2">Everything you need, <span className="is-green">governed.</span></h2>
            </div>
            <div className="sa-features">
              {FEATURE_CARDS.map(({ icon: Icon, label, desc, to }, i) => (
                <motion.button
                  type="button"
                  key={label}
                  className="sa-feature sa-feature--link"
                  onClick={() => navigate(to)}
                  {...revealIn(i * 0.12)}
                >
                  <span className="sa-feature__icon"><Icon size={18} /></span>
                  <span className="sa-mono sa-feature__num">0{i + 1}</span>
                  <h3>{label}</h3>
                  <p>{desc}</p>
                </motion.button>
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
