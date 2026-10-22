import { AnimatePresence, motion, useMotionValue, useReducedMotion, useScroll, useSpring, useTransform } from 'framer-motion'
import { useEffect, useRef, useState } from 'react'
import { ArrowRight, ArrowUpRight, Activity, Check, FileCheck2, LockKeyhole, Shield, Sparkles, UsersRound } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

const CAPABILITIES = [
  [LockKeyhole, 'Role-aware access', 'Permissions follow the person, so sensitive requests stay within the right boundaries.'],
  [FileCheck2, 'Policy-grounded answers', 'Approved policy sources give every response useful context and traceable evidence.'],
  [Activity, 'Risk that is visible', 'Transparent scoring turns risky patterns into signals your team can review and understand.'],
  [UsersRound, 'Human accountability', 'Governance cases, alerts, and audit trails keep important decisions in human hands.'],
]

const DECISION_STEPS = [
  ['01', 'Ask', 'A request enters the governed workspace.'],
  ['02', 'Check access', 'Role and permissions are verified first.'],
  ['03', 'Evaluate risk', 'Policies and signals shape the decision.'],
  ['04', 'Answer & record', 'The response and evidence are logged.'],
]

const AUDIT_EVENTS = [
  ['09:42:18', 'Policy match completed', 'LOW RISK', 'low'],
  ['09:42:19', 'Decision trace created', 'RECORDED', 'info'],
  ['09:42:20', 'Response released to user', 'APPROVED', 'success'],
]

const WORKFLOW_SLIDES = [
  {
    step: '01',
    eyebrow: 'The request',
    title: 'Start with a question.',
    text: 'Every request enters a governed workspace with the user, role, and context attached.',
    label: 'INCOMING REQUEST',
    value: 'Can I share this customer data?',
    status: 'Awaiting evaluation',
    tone: 'cyan',
  },
  {
    step: '02',
    eyebrow: 'Access control',
    title: 'Check who is asking.',
    text: 'Role-aware permissions establish what the user can access before an answer is considered.',
    label: 'IDENTITY VERIFIED',
    value: 'Marketing analyst · customer-data access',
    status: 'Role verified',
    tone: 'purple',
  },
  {
    step: '03',
    eyebrow: 'Risk evaluation',
    title: 'Let policy shape the answer.',
    text: 'Approved sources and risk signals are evaluated together, with the reasoning kept visible.',
    label: 'POLICY EVALUATION',
    value: 'Customer data handling policy · §4.2',
    status: 'Low risk · policy matched',
    tone: 'green',
  },
  {
    step: '04',
    eyebrow: 'Decision trace',
    title: 'Answer and record.',
    text: 'The user gets a useful response while the decision, evidence, and risk outcome are recorded.',
    label: 'FINAL DECISION',
    value: 'Approved with handling guidance',
    status: 'Recorded · trace available',
    tone: 'gold',
  },
]

const reveal = {
  hidden: { opacity: 0, y: 28 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.22, 1, 0.36, 1] } },
}

function Reveal({ children, className = '', delay = 0 }) {
  return (
    <motion.div
      className={className}
      variants={reveal}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.2 }}
      transition={{ delay }}
    >
      {children}
    </motion.div>
  )
}

function WorkflowCarousel({ shouldReduceMotion }) {
  const [active, setActive] = useState(0)
  const [paused, setPaused] = useState(false)
  const slide = WORKFLOW_SLIDES[active]

  useEffect(() => {
    if (paused || shouldReduceMotion) return undefined
    const timer = window.setInterval(() => {
      setActive((current) => (current + 1) % WORKFLOW_SLIDES.length)
    }, 5200)
    return () => window.clearInterval(timer)
  }, [paused, shouldReduceMotion])

  const move = (direction) => {
    setActive((current) => (current + direction + WORKFLOW_SLIDES.length) % WORKFLOW_SLIDES.length)
  }

  return (
    <div
      className="landing-workflow-carousel"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocus={() => setPaused(true)}
      onBlur={() => setPaused(false)}
      aria-roledescription="carousel"
      aria-label="SecureAI governance workflow"
    >
      <div className="landing-workflow-topline">
        <span className="landing-eyebrow">Inside a governed request</span>
        <span>{String(active + 1).padStart(2, '0')} / {String(WORKFLOW_SLIDES.length).padStart(2, '0')}</span>
      </div>
      <div className="landing-workflow-stage">
        <AnimatePresence mode="wait">
          <motion.div
            key={slide.step}
            className={`landing-workflow-slide landing-workflow-slide-${slide.tone}`}
            initial={shouldReduceMotion ? false : { opacity: 0, x: 18 }}
            animate={{ opacity: 1, x: 0 }}
            exit={shouldReduceMotion ? undefined : { opacity: 0, x: -18 }}
            transition={{ duration: .38, ease: [0.22, 1, 0.36, 1] }}
            role="group"
            aria-roledescription="slide"
            aria-label={`${slide.step}: ${slide.title}`}
          >
            <div className="landing-workflow-copy">
              <span className="landing-workflow-step">{slide.step}</span>
              <p className="landing-eyebrow">{slide.eyebrow}</p>
              <h3>{slide.title}</h3>
              <p>{slide.text}</p>
            </div>
            <div className="landing-workflow-signal">
              <span>{slide.label}</span>
              <strong>{slide.value}</strong>
              <b>{slide.status}</b>
              <i />
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
      <div className="landing-workflow-controls">
        <button type="button" onClick={() => move(-1)} aria-label="Previous workflow step">←</button>
        <div className="landing-workflow-dots">
          {WORKFLOW_SLIDES.map((item, index) => (
            <button
              type="button"
              key={item.step}
              className={index === active ? 'is-active' : ''}
              onClick={() => setActive(index)}
              aria-label={`Show workflow step ${item.step}`}
              aria-current={index === active ? 'step' : undefined}
            />
          ))}
        </div>
        <button type="button" onClick={() => move(1)} aria-label="Next workflow step">→</button>
      </div>
    </div>
  )
}

export default function CinematicLanding() {
  const navigate = useNavigate()
  const shouldReduceMotion = useReducedMotion()
  const methodRef = useRef(null)
  const { scrollYProgress } = useScroll()
  const smoothProgress = useSpring(scrollYProgress, { stiffness: 90, damping: 30, mass: 0.4 })
  const coreY = useTransform(smoothProgress, [0, 0.35], [0, shouldReduceMotion ? 0 : 120])
  const coreRotate = useTransform(smoothProgress, [0, 0.35], [-3, shouldReduceMotion ? -3 : 10])
  const methodOffset = useMotionValue(0)
  const methodX = useSpring(methodOffset, { stiffness: 120, damping: 28, mass: 0.45 })

  useEffect(() => {
    const updateMethodOffset = () => {
      if (shouldReduceMotion || window.innerWidth < 761 || !methodRef.current) {
        methodOffset.set(0)
        return
      }
      const rect = methodRef.current.getBoundingClientRect()
      const sectionTop = rect.top + window.scrollY
      const start = sectionTop - 140
      const end = start + window.innerHeight * 0.8
      const progress = Math.max(0, Math.min(1, (window.scrollY - start) / (end - start)))
      methodOffset.set(-((window.innerWidth / 3) + 24) * progress)
    }
    updateMethodOffset()
    window.addEventListener('resize', updateMethodOffset)
    window.addEventListener('scroll', updateMethodOffset, { passive: true })
    return () => {
      window.removeEventListener('resize', updateMethodOffset)
      window.removeEventListener('scroll', updateMethodOffset)
    }
  }, [methodOffset, shouldReduceMotion])

  return (
    <div className="landing-page">
      <motion.header
        className="landing-header"
        initial={{ opacity: 0, y: -18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
      >
        <button className="landing-brand" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
          <span className="landing-mark"><Shield size={17} /></span>
          SecureAI
        </button>
        <nav>
          <a href="#method">Method</a>
          <button onClick={() => navigate('/login')}>Sign in <ArrowUpRight size={15} /></button>
        </nav>
      </motion.header>

      <main>
        <section className="landing-hero">
          <motion.div className="landing-orbit landing-orbit-one" initial={{ opacity: 0, scale: .8 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 1.2, delay: .2 }} />
          <motion.div className="landing-orbit landing-orbit-two" initial={{ opacity: 0, scale: .8 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 1.2, delay: .35 }} />
          <motion.div className="landing-core" style={{ y: coreY, rotate: coreRotate }} initial={{ opacity: 0, scale: .7 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 1.1, delay: .3, ease: [0.22, 1, 0.36, 1] }}><Sparkles size={28} /></motion.div>
          <motion.div
            className="landing-hero-copy"
            initial="hidden"
            animate="visible"
            variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.12, delayChildren: 0.45 } } }}
          >
            <div className="landing-hero-content">
              <p className="landing-eyebrow">Enterprise AI governance platform</p>
              <motion.h1 variants={reveal}>Intelligence,<br /><em>held accountable.</em></motion.h1>
              <motion.div className="landing-intro" variants={reveal}>
                <p>Give every team useful AI with policy controls, role-aware access, visible risk, and an audit trail built in.</p>
                <div className="landing-actions">
                  <button className="landing-cta" onClick={() => navigate('/login')}>Enter SecureAI <ArrowRight size={16} /></button>
                  <a className="landing-secondary-cta" href="#overview">See how it works <ArrowRight size={15} /></a>
                </div>
              </motion.div>
            </div>
            <motion.div className="landing-hero-proof" aria-label="SecureAI governance checks" variants={reveal}>
              <div className="landing-proof-header"><span className="landing-status-dot" /> Governance layer active <span>LIVE</span></div>
              <div className="landing-proof-query">
                <span className="landing-proof-label">REQUEST EVALUATION</span>
                <strong>Can I share this customer data?</strong>
              </div>
              <motion.div
                className="landing-proof-checks"
                initial="hidden"
                animate="visible"
                variants={{ hidden: {}, visible: { transition: { delayChildren: .9, staggerChildren: .22 } } }}
              >
                {['Role verified', 'Policy matched', 'Risk recorded'].map((check) => (
                  <motion.span key={check} variants={{ hidden: { opacity: 0, x: -10 }, visible: { opacity: 1, x: 0, transition: { duration: .35 } } }}>
                    <Check size={13} /> {check}
                  </motion.span>
                ))}
              </motion.div>
              <div className="landing-proof-meter" aria-label="Low risk score">
                <span />
              </div>
              <div className="landing-proof-footer"><span>Decision trace available</span><span className="landing-proof-score">LOW RISK</span></div>
            </motion.div>
          </motion.div>
          <motion.span className="landing-scroll" animate={shouldReduceMotion ? {} : { y: [0, 7, 0], opacity: [0.55, 1, 0.55] }} transition={{ duration: 2.4, repeat: Infinity, ease: 'easeInOut' }}>Scroll to explore ↓</motion.span>
        </section>

        <div className="landing-marquee">
          <div>Policy-grounded answers <b>·</b> Role-aware access <b>·</b> Every decision accountable <b>·</b> Human oversight <b>·</b></div>
        </div>

        <Reveal className="landing-manifesto">
          <p className="landing-eyebrow">The promise</p>
          <h2>Responsible intelligence should feel like <em>craftsmanship</em> — quiet, considered, and made for the people who depend on it.</h2>
        </Reveal>

        <section id="overview" className="landing-overview">
          <Reveal className="landing-section-title"><span className="landing-eyebrow">One calm layer of control</span><i /></Reveal>
          <Reveal className="landing-overview-copy" delay={0.08}>
            <h2>AI that works <em>with</em> your organization.</h2>
            <p>SecureAI brings access control, policy, risk, and audit into one workspace. Employees get useful answers; administrators get the context to make responsible decisions.</p>
          </Reveal>
          <div className="landing-capabilities">
            {CAPABILITIES.map(([Icon, title, text], index) => (
              <Reveal key={title} delay={index * 0.08}>
                <article>
                <span className="landing-capability-icon"><Icon size={18} /></span>
                <h3>{title}</h3>
                <p>{text}</p>
                </article>
              </Reveal>
            ))}
          </div>
          <Reveal className="landing-audit-preview" delay={0.18}>
            <div className="landing-audit-heading">
              <span><span className="landing-status-dot" /> Live decision trace</span>
              <span>SECUREAI / AUDIT</span>
            </div>
            <div className="landing-audit-events">
              {AUDIT_EVENTS.map(([time, event, status, tone], index) => (
                <motion.div
                  key={event}
                  className="landing-audit-event"
                  initial={{ opacity: 0, x: -14 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true, amount: 0.4 }}
                  transition={{ delay: index * 0.14, duration: .45 }}
                >
                  <time>{time}</time>
                  <span className="landing-audit-line" />
                  <strong>{event}</strong>
                  <b data-tone={tone}>{status}</b>
                </motion.div>
              ))}
            </div>
          </Reveal>
          <Reveal delay={0.24}>
            <WorkflowCarousel shouldReduceMotion={shouldReduceMotion} />
          </Reveal>
        </section>

        <section id="method" ref={methodRef} className="landing-method">
          <Reveal className="landing-section-title"><span className="landing-eyebrow">The method</span><i /></Reveal>
          <div className="landing-cards-viewport">
            <motion.div className="landing-cards" style={{ x: methodX }}>
              {DECISION_STEPS.map(([number, title, text], index) => (
                <Reveal key={number} delay={index * 0.1}>
                  <article>
                    <span>{number}</span>
                    <div><h3>{title}</h3><p>{text}</p></div>
                  </article>
                </Reveal>
              ))}
            </motion.div>
          </div>
          <Reveal className="landing-flow">
            <span className="landing-eyebrow">Every request follows a clear path</span>
            <div>
              {DECISION_STEPS.map(([number, title], index) => (
                <motion.span
                  key={number}
                  className="landing-flow-step"
                  initial={{ opacity: 0, y: 12 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, amount: 0.7 }}
                  transition={{ delay: index * .12, duration: .4 }}
                >
                  <b>{title}</b>{index < DECISION_STEPS.length - 1 && <i>→</i>}
                </motion.span>
              ))}
            </div>
          </Reveal>
        </section>

        <motion.section className="landing-final" initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.3 }} variants={reveal}>
          <span className="landing-mark"><Shield size={21} /></span>
          <h2>Make AI<br /><em>answerable.</em></h2>
          <p>Start with a governed workspace built around your organization’s policies and people.</p>
          <button className="landing-cta" onClick={() => navigate('/login')}>Get started <ArrowRight size={16} /></button>
        </motion.section>
      </main>

      <footer className="landing-footer"><strong>SecureAI</strong><span>AI governance for people who care about the details.</span></footer>
    </div>
  )
}
