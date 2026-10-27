import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import { useEffect, useState } from 'react'
import { Activity, ArrowRight, ArrowUpRight, Check, FileCheck2, LockKeyhole, Shield, Sparkles, UsersRound } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

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
  ['01', 'The request', 'Start with a question.', 'Every request enters a governed workspace with the user, role, and context attached.', 'INCOMING REQUEST', 'Can I share this customer data?', 'Awaiting evaluation', 'cyan'],
  ['02', 'Access control', 'Check who is asking.', 'Role-aware permissions establish what the user can access before an answer is considered.', 'IDENTITY VERIFIED', 'Marketing analyst · customer-data access', 'Role verified', 'purple'],
  ['03', 'Risk evaluation', 'Let policy shape the answer.', 'Approved sources and risk signals are evaluated together, with the reasoning kept visible.', 'POLICY EVALUATION', 'Customer data handling policy · §4.2', 'Low risk · policy matched', 'green'],
  ['04', 'Decision trace', 'Answer and record.', 'The user gets a useful response while the decision, evidence, and risk outcome are recorded.', 'FINAL DECISION', 'Approved with handling guidance', 'Recorded · trace available', 'gold'],
]

const AUDIT_EVENTS = [
  ['09:42:18', 'Policy match completed', 'LOW RISK', 'low'],
  ['09:42:19', 'Decision trace created', 'RECORDED', 'info'],
  ['09:42:20', 'Response released to user', 'APPROVED', 'success'],
]

function Reveal({ children, className = '', delay = 0 }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.2 }}
      transition={{ duration: 0.65, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  )
}

function WorkflowCarousel({ reduceMotion }) {
  const [active, setActive] = useState(0)
  const [paused, setPaused] = useState(false)
  const slide = SLIDES[active]

  useEffect(() => {
    if (paused || reduceMotion) return undefined
    const timer = window.setInterval(() => setActive(current => (current + 1) % SLIDES.length), 5200)
    return () => window.clearInterval(timer)
  }, [paused, reduceMotion])

  return (
    <div className="landing-workflow-carousel" onMouseEnter={() => setPaused(true)} onMouseLeave={() => setPaused(false)}>
      <div className="landing-workflow-topline">
        <span className="landing-eyebrow">Inside a governed request</span>
        <span>{String(active + 1).padStart(2, '0')} / {String(SLIDES.length).padStart(2, '0')}</span>
      </div>
      <div className="landing-workflow-stage">
        <AnimatePresence mode="wait">
          <motion.div key={slide[0]} className={`landing-workflow-slide landing-workflow-slide-${slide[7]}`} initial={{ opacity: 0, x: 18 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -18 }} transition={{ duration: 0.35 }}>
            <div className="landing-workflow-copy">
              <span className="landing-workflow-step">{slide[0]}</span>
              <p className="landing-eyebrow">{slide[1]}</p>
              <h3>{slide[2]}</h3>
              <p>{slide[3]}</p>
            </div>
            <div className="landing-workflow-signal">
              <span>{slide[4]}</span>
              <strong>{slide[5]}</strong>
              <b>{slide[6]}</b>
              <i />
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
      <div className="landing-workflow-controls">
        <button type="button" onClick={() => setActive(current => (current - 1 + SLIDES.length) % SLIDES.length)} aria-label="Previous workflow step">←</button>
        <div className="landing-workflow-dots">
          {SLIDES.map((item, index) => <button type="button" key={item[0]} className={index === active ? 'is-active' : ''} onClick={() => setActive(index)} aria-label={`Show workflow step ${item[0]}`} />)}
        </div>
        <button type="button" onClick={() => setActive(current => (current + 1) % SLIDES.length)} aria-label="Next workflow step">→</button>
      </div>
    </div>
  )
}

export default function LandingPage() {
  const navigate = useNavigate()
  const reduceMotion = useReducedMotion()

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'auto' })
  }, [])

  return (
    <div className="landing-page">
      <motion.header
        className="landing-header"
        initial={reduceMotion ? false : { opacity: 0, y: -18 }}
        animate={reduceMotion ? {} : { opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
      >
        <button className="landing-brand" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}><span className="landing-mark"><Shield size={17} /></span>SecureAI</button>
        <nav><a href="#method">Method</a><button onClick={() => navigate('/login')}>Sign in <ArrowUpRight size={15} /></button></nav>
      </motion.header>

      <main>
        <section className="landing-hero">
          <motion.div className="landing-orbit landing-orbit-one" animate={reduceMotion ? {} : { rotate: [-25, -20, -25], opacity: [0.45, 0.8, 0.45] }} transition={{ duration: 16, repeat: Infinity, ease: 'easeInOut' }} />
          <motion.div className="landing-orbit landing-orbit-two" animate={reduceMotion ? {} : { rotate: [35, 27, 35], opacity: [0.25, 0.55, 0.25] }} transition={{ duration: 22, repeat: Infinity, ease: 'easeInOut' }} />
          <motion.div className="landing-core" animate={reduceMotion ? {} : { y: [0, -18, 0], rotate: [-3, 10, -3], scale: [1, 1.04, 1] }} transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}><Sparkles size={28} /></motion.div>
          <div className="landing-hero-copy">
            <motion.div
              className="landing-hero-content"
            >
              <p className="landing-eyebrow">Enterprise AI governance platform</p>
              <h1>Intelligence,<br /><em>held accountable.</em></h1>
              <div className="landing-intro"><p>Give every team useful AI with policy controls, role-aware access, visible risk, and an audit trail built in.</p><div className="landing-actions"><button className="landing-cta" onClick={() => navigate('/login')}>Enter SecureAI <ArrowRight size={16} /></button><a className="landing-secondary-cta" href="#overview">See how it works <ArrowRight size={15} /></a></div></div>
            </motion.div>
            <motion.div className="landing-hero-proof">
              <div className="landing-proof-header"><span className="landing-status-dot" /> Governance layer active <span>LIVE</span></div>
              <div className="landing-proof-query"><span className="landing-proof-label">REQUEST EVALUATION</span><strong>Can I share this customer data?</strong></div>
              <div className="landing-proof-checks">{['Role verified', 'Policy matched', 'Risk recorded'].map(check => <span key={check}><Check size={13} /> {check}</span>)}</div>
              <div className="landing-proof-meter"><span /></div>
              <div className="landing-proof-footer"><span>Decision trace available</span><span className="landing-proof-score">LOW RISK</span></div>
            </motion.div>
          </div>
          <motion.span className="landing-scroll" animate={reduceMotion ? {} : { y: [0, 7, 0], opacity: [0.5, 1, 0.5] }} transition={{ duration: 2.4, repeat: Infinity, ease: 'easeInOut' }}>Scroll to explore ↓</motion.span>
        </section>

        <div className="landing-marquee"><div>Policy-grounded answers <b>·</b> Role-aware access <b>·</b> Every decision accountable <b>·</b> Human oversight <b>·</b> Policy-grounded answers <b>·</b> Role-aware access</div></div>
        <Reveal className="landing-manifesto"><p className="landing-eyebrow">The promise</p><h2>Responsible intelligence should feel like <em>craftsmanship</em> — quiet, considered, and made for the people who depend on it.</h2></Reveal>

        <section id="overview" className="landing-overview">
          <Reveal className="landing-section-title"><span className="landing-eyebrow">One calm layer of control</span><i /></Reveal>
          <Reveal className="landing-overview-copy"><h2>AI that works <em>with</em> your organization.</h2><p>SecureAI brings access control, policy, risk, and audit into one workspace. Employees get useful answers; administrators get the context to make responsible decisions.</p></Reveal>
          <div className="landing-capabilities">{CAPABILITIES.map(([Icon, title, text], index) => <Reveal key={title} delay={index * 0.08}><motion.article whileHover={reduceMotion ? {} : { y: -7, scale: 1.015 }} transition={{ type: 'spring', stiffness: 280, damping: 20 }}><span className="landing-capability-icon"><Icon size={18} /></span><h3>{title}</h3><p>{text}</p></motion.article></Reveal>)}</div>
          <Reveal className="landing-audit-preview"><div className="landing-audit-heading"><span><span className="landing-status-dot" /> Live decision trace</span><span>SECUREAI / AUDIT</span></div><div className="landing-audit-events">{AUDIT_EVENTS.map(([time, event, status, tone]) => <div className="landing-audit-event" key={event}><time>{time}</time><span className="landing-audit-line" /><strong>{event}</strong><b data-tone={tone}>{status}</b></div>)}</div></Reveal>
          <Reveal><WorkflowCarousel reduceMotion={reduceMotion} /></Reveal>
        </section>

        <section id="method" className="landing-method">
          <Reveal className="landing-section-title"><span className="landing-eyebrow">The method</span><i /></Reveal>
          <div className="landing-cards">{STEPS.map(([number, title, text], index) => <Reveal key={number} delay={index * 0.08}><motion.article whileHover={reduceMotion ? {} : { y: -8, scale: 1.015 }} transition={{ type: 'spring', stiffness: 260, damping: 20 }}><span>{number}</span><div><h3>{title}</h3><p>{text}</p></div></motion.article></Reveal>)}</div>
          <Reveal className="landing-flow"><span className="landing-eyebrow">Every request follows a clear path</span><div>{STEPS.map(([number, title], index) => <span className="landing-flow-step" key={number}><b>{title}</b>{index < STEPS.length - 1 && <i>→</i>}</span>)}</div></Reveal>
        </section>

        <Reveal className="landing-final"><span className="landing-mark"><Shield size={21} /></span><h2>Make AI<br /><em>answerable.</em></h2><p>Start with a governed workspace built around your organization’s policies and people.</p><button className="landing-cta" onClick={() => navigate('/login')}>Get started <ArrowRight size={16} /></button></Reveal>
      </main>
      <footer className="landing-footer"><strong>SecureAI</strong><span>AI governance for people who care about the details.</span></footer>
    </div>
  )
}
