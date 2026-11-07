import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import { useEffect, useRef, useState } from 'react'
import { Activity, ArrowRight, Check, FileCheck2, LockKeyhole, Shield, ShieldCheck, UsersRound } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import ThemeToggle from '../components/ThemeToggle'
import { useHeroParallax } from '../utils/motion'
import './landing.css'

const NAV_LINKS = [
  { id: 'platform', label: 'Platform' },
  { id: 'features', label: 'Features' },
  { id: 'how', label: 'How it works' },
  { id: 'method', label: 'Method' },
  { id: 'start', label: 'Get started' },
]

const HERO_LINES = [
  ['Every AI', 'ink'],
  ['answer,', 'ink'],
  ['governed', 'green'],
  ['& proven.', 'green'],
]

const CAPABILITIES = [
  [LockKeyhole, 'Role-aware access', 'Permissions follow the person, so sensitive requests stay within the right boundaries.'],
  [FileCheck2, 'Policy-grounded answers', 'Approved policy sources give every response useful context and traceable evidence.'],
  [Activity, 'Risk that is visible', 'Transparent scoring turns risky patterns into signals your team can review and understand.'],
  [UsersRound, 'Human accountability', 'Governance cases, alerts, and audit trails keep important decisions in human hands.'],
]

const STEPS = [
  ['01', 'Ask', 'A request enters the governed workspace.'],
  ['02', 'Check access', 'Role and permissions are verified first.'],
  ['03', 'Evaluate risk', 'Policies and signals shape the decision.'],
  ['04', 'Answer & record', 'The response and evidence are logged.'],
]

const SLIDES = [
  ['01', 'The request', 'Start with a question.', 'Every request enters a governed workspace with the user, role, and context attached.', 'Incoming request', 'Can I share this customer data?', 'Awaiting evaluation'],
  ['02', 'Access control', 'Check who is asking.', 'Role-aware permissions establish what the user can access before an answer is considered.', 'Identity verified', 'Marketing analyst · customer-data access', 'Role verified'],
  ['03', 'Risk evaluation', 'Let policy shape the answer.', 'Approved sources and risk signals are evaluated together, with the reasoning kept visible.', 'Policy evaluation', 'Customer data handling policy · §4.2', 'Low risk · policy matched'],
  ['04', 'Decision trace', 'Answer and record.', 'The user gets a useful response while the decision, evidence, and risk outcome are recorded.', 'Final decision', 'Approved with handling guidance', 'Recorded · trace available'],
]

const AUDIT_EVENTS = [
  ['09:42:18', 'Policy match completed', 'Low risk'],
  ['09:42:19', 'Decision trace created', 'Recorded'],
  ['09:42:20', 'Response released to user', 'Approved'],
]

const ease = [0.22, 1, 0.36, 1]

function Reveal({ children, className = '', delay = 0, as = 'div' }) {
  const M = motion[as]
  return (
    <M
      className={className}
      initial={{ opacity: 0, y: 36, scale: 0.98, filter: 'blur(8px)' }}
      whileInView={{ opacity: 1, y: 0, scale: 1, filter: 'blur(0px)' }}
      viewport={{ once: true, amount: 0.2 }}
      transition={{ duration: 1.2, delay, ease }}
    >
      {children}
    </M>
  )
}

function scrollToId(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function Nav() {
  const navigate = useNavigate()
  const [active, setActive] = useState('platform')
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    if (!('IntersectionObserver' in window)) return undefined
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) if (e.isIntersecting) setActive(e.target.id)
    }, { rootMargin: '-45% 0px -50% 0px' })
    NAV_LINKS.forEach((l) => {
      const el = document.getElementById(l.id)
      if (el) io.observe(el)
    })
    return () => io.disconnect()
  }, [])

  return (
    <header className={`sa-nav ${scrolled ? 'is-scrolled' : ''}`}>
      <button type="button" className="sa-brand" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} aria-label="SecureAI — back to top">
        <span className="sa-brand__mark"><Shield size={22} strokeWidth={1.8} /></span>
        <span className="sa-brand__name">SecureAI</span>
      </button>
      <ThemeToggle className="sa-theme" size={17} />
      <nav className="sa-nav__links" aria-label="Sections">
        <ul>
          {NAV_LINKS.map((l) => (
            <li key={l.id}>
              <a href={`#${l.id}`} aria-current={active === l.id ? 'true' : undefined}
                onClick={(e) => { e.preventDefault(); scrollToId(l.id) }}>
                {l.label}
              </a>
            </li>
          ))}
          <li className="sa-nav__login">
            <a href="/login" onClick={(e) => { e.preventDefault(); navigate('/login') }}>Log in</a>
          </li>
        </ul>
      </nav>
    </header>
  )
}

function Hero() {
  const navigate = useNavigate()
  const reduce = useReducedMotion()
  const ref = useRef(null)

  useHeroParallax(ref)

  return (
    <section id="platform" ref={ref} className="sa-hero" aria-labelledby="hero-title">
      <div className="sa-hero__art" aria-hidden="true">
        <ShieldCheck strokeWidth={0.75} />
      </div>
      <div className="sa-hero__inner">
        <div className="sa-hero__copy">
          <motion.span className="sa-eyebrow" initial={{ opacity: 0, y: 10, filter: 'blur(6px)' }} animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }} transition={{ duration: 1.2, delay: 0.2, ease }}>
            Enterprise AI governance
          </motion.span>
          <h1 id="hero-title" className="sa-hero__title">
            {HERO_LINES.map(([line, tone], i) => (
              <span className="sa-line" key={line}>
                <motion.span
                  className={`sa-line__inner ${tone === 'green' ? 'is-green' : ''}`}
                  initial={reduce ? false : { y: '105%', opacity: 0, rotate: 2, filter: 'blur(10px)' }}
                  animate={{ y: 0, opacity: 1, rotate: 0, filter: 'blur(0px)' }}
                  transition={{ duration: 1.4, delay: 0.3 + i * 0.18, ease: [0.16, 1, 0.3, 1] }}
                >
                  {line}
                </motion.span>
              </span>
            ))}
          </h1>
          <motion.p className="sa-hero__lead" initial={{ opacity: 0, y: 18, filter: 'blur(6px)' }} animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }} transition={{ duration: 1.3, delay: 1, ease }}>
            Give every team useful AI with policy controls, role-aware access, visible risk, and an audit trail built in — all in one focused workspace.
          </motion.p>
          <motion.div className="sa-hero__ctas" initial={{ opacity: 0, y: 18, filter: 'blur(6px)' }} animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }} transition={{ duration: 1.3, delay: 1.2, ease }}>
            <button type="button" className="sa-btn sa-btn--primary sa-btn--lg" onClick={() => navigate('/login')}>
              Enter SecureAI <span className="sa-btn__badge"><ArrowRight size={16} /></span>
            </button>
            <button type="button" className="sa-btn sa-btn--ghost sa-btn--lg" onClick={() => scrollToId('features')}>
              Explore the platform
            </button>
          </motion.div>
        </div>
      </div>
      <div className="sa-hero__bar">
        <span><Shield size={14} /> Governance layer active</span>
        <span className="sa-hide-sm">Role-aware · policy-grounded · audited</span>
        <button type="button" onClick={() => scrollToId('statement')}>Scroll to explore <span aria-hidden="true">↓</span></button>
      </div>
    </section>
  )
}

function WorkflowCarousel() {
  const reduce = useReducedMotion()
  const [active, setActive] = useState(0)
  const [paused, setPaused] = useState(false)
  const slide = SLIDES[active]

  useEffect(() => {
    if (paused || reduce) return undefined
    const t = window.setInterval(() => setActive((c) => (c + 1) % SLIDES.length), 5200)
    return () => window.clearInterval(t)
  }, [paused, reduce])

  return (
    <div className="sa-panel sa-carousel" onMouseEnter={() => setPaused(true)} onMouseLeave={() => setPaused(false)}>
      <div className="sa-carousel__top">
        <span className="sa-eyebrow">Inside a governed request</span>
        <span className="sa-mono">{String(active + 1).padStart(2, '0')} / {String(SLIDES.length).padStart(2, '0')}</span>
      </div>
      <div className="sa-carousel__stage">
        <AnimatePresence mode="wait">
          <motion.div key={slide[0]} className="sa-slide" initial={{ opacity: 0, x: 24, filter: 'blur(6px)' }} animate={{ opacity: 1, x: 0, filter: 'blur(0px)' }} exit={{ opacity: 0, x: -24, filter: 'blur(6px)' }} transition={{ duration: 0.8, ease }}>
            <div className="sa-slide__copy">
              <span className="sa-mono sa-slide__num">{slide[0]} · {slide[1]}</span>
              <h3>{slide[2]}</h3>
              <p>{slide[3]}</p>
            </div>
            <div className="sa-signal">
              <span className="sa-mono">{slide[4]}</span>
              <strong>{slide[5]}</strong>
              <b className="sa-tag">{slide[6]}</b>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
      <div className="sa-carousel__controls">
        <button type="button" onClick={() => setActive((c) => (c - 1 + SLIDES.length) % SLIDES.length)} aria-label="Previous step">←</button>
        <div className="sa-dots">
          {SLIDES.map((s, i) => (
            <button type="button" key={s[0]} className={i === active ? 'is-active' : ''} onClick={() => setActive(i)} aria-label={`Show step ${s[0]}`} />
          ))}
        </div>
        <button type="button" onClick={() => setActive((c) => (c + 1) % SLIDES.length)} aria-label="Next step">→</button>
      </div>
    </div>
  )
}

export default function LandingPage() {
  const navigate = useNavigate()

  useEffect(() => { window.scrollTo({ top: 0, left: 0, behavior: 'auto' }) }, [])

  return (
    <div className="sa">
      <Nav />
      <main>
        <Hero />

        <section id="statement" className="sa-section sa-statement">
          <div className="sa-shell">
            <Reveal><span className="sa-eyebrow">The promise</span></Reveal>
            <Reveal as="h2" className="sa-statement__text" delay={0.08}>
              Responsible intelligence should feel like <span className="is-green">craftsmanship</span> — quiet, considered, and made for the people who depend on it.
            </Reveal>
          </div>
        </section>

        <div className="sa-band" aria-hidden="true">
          <div className="sa-band__track">
            {Array.from({ length: 2 }).map((_, k) => (
              <span key={k}>Policy-grounded answers <b>◇</b> Role-aware access <b>◇</b> Every decision accountable <b>◇</b> Human oversight <b>◇</b> Audit trail built in <b>◇</b> </span>
            ))}
          </div>
        </div>

        <section id="features" className="sa-section">
          <div className="sa-shell">
            <div className="sa-head sa-head--split">
              <Reveal>
                <span className="sa-eyebrow">One calm layer of control</span>
                <h2 className="sa-h2">AI that works <span className="is-green">with</span> your organization.</h2>
              </Reveal>
              <Reveal delay={0.1}>
                <p className="sa-lead">SecureAI brings access control, policy, risk, and audit into one workspace. Employees get useful answers; administrators get the context to make responsible decisions.</p>
              </Reveal>
            </div>
            <div className="sa-features">
              {CAPABILITIES.map(([Icon, title, text], i) => (
                <Reveal key={title} delay={i * 0.08} as="article" className="sa-feature">
                  <span className="sa-feature__icon"><Icon size={18} /></span>
                  <span className="sa-mono sa-feature__num">0{i + 1}</span>
                  <h3>{title}</h3>
                  <p>{text}</p>
                </Reveal>
              ))}
            </div>
          </div>
        </section>

        <section id="how" className="sa-section sa-section--tint">
          <div className="sa-shell">
            <div className="sa-head">
              <Reveal>
                <span className="sa-eyebrow">How it works</span>
                <h2 className="sa-h2">Every request leaves a <span className="is-green">trace.</span></h2>
              </Reveal>
            </div>
            <Reveal className="sa-panel sa-audit">
              <div className="sa-audit__head">
                <span><i className="sa-dot" /> Live decision trace</span>
                <span className="sa-mono">SecureAI / audit</span>
              </div>
              {AUDIT_EVENTS.map(([time, event, status]) => (
                <div className="sa-audit__row" key={event}>
                  <time className="sa-mono">{time}</time>
                  <span className="sa-audit__node" />
                  <strong>{event}</strong>
                  <b className="sa-tag"><Check size={11} /> {status}</b>
                </div>
              ))}
            </Reveal>
            <Reveal delay={0.08}><WorkflowCarousel /></Reveal>
          </div>
        </section>

        <section id="method" className="sa-section">
          <div className="sa-shell">
            <div className="sa-head">
              <Reveal>
                <span className="sa-eyebrow">The method</span>
                <h2 className="sa-h2">Four steps. <span className="is-green">No guesswork.</span></h2>
              </Reveal>
            </div>
            <ol className="sa-steps">
              {STEPS.map(([n, title, text], i) => (
                <Reveal as="li" key={n} delay={i * 0.08} className="sa-step">
                  <span className="sa-step__num">{n}</span>
                  <h3>{title}</h3>
                  <p>{text}</p>
                </Reveal>
              ))}
            </ol>
          </div>
        </section>

        <section id="start" className="sa-section sa-final">
          <div className="sa-shell">
            <Reveal>
              <span className="sa-eyebrow">Get started</span>
              <h2 className="sa-final__title">Make AI<br /><span className="is-green">answerable.</span></h2>
              <p className="sa-lead">Start with a governed workspace built around your organization’s policies and people.</p>
              <div className="sa-hero__ctas">
                <button type="button" className="sa-btn sa-btn--primary sa-btn--lg" onClick={() => navigate('/login')}>
                  Get started <span className="sa-btn__badge"><ArrowRight size={16} /></span>
                </button>
              </div>
            </Reveal>
          </div>
        </section>
      </main>
      <footer className="sa-footer">
        <span className="sa-brand"><span className="sa-brand__mark"><Shield size={18} strokeWidth={1.8} /></span><strong>SecureAI</strong></span>
        <span>AI governance for people who care about the details.</span>
      </footer>
    </div>
  )
}
