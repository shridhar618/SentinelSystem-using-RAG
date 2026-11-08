import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { motion, AnimatePresence, MotionConfig, useSpring, useTransform } from 'framer-motion'
import toast from 'react-hot-toast'
import {
  AlertTriangle, Bot, UserCog, Pause, Play, Square, Ban, Download, Send,
  Radar, Clock, Activity, MessageSquare, ShieldAlert, ChevronDown,
  Plus, Crosshair, History, X, FileJson, FileSpreadsheet, Eye,
} from 'lucide-react'
import api from '../utils/api'
import { joinGhostAdminRoom } from '../utils/ghostSocket'
import { ease } from '../utils/motion'
import { useAuth } from '../context/AuthContext'

/* ── visual vocabulary ─────────────────────────────────────────────────────
   Normal Ghost Mode (honeypot demo) ......... red / ghost (existing panel)
   AI Persona Mode ............................ accent / Bot
   Admin Manual Control ....................... warn / UserCog
   Active Investigation ....................... danger, pulsing LIVE dot
   Paused ..................................... purple
   Terminated / Expired ....................... slate (muted)
*/
const LEVEL_STYLE = {
  low: 'text-success bg-success/10 border-success/20',
  medium: 'text-warn bg-warn/10 border-warn/20',
  high: 'text-danger bg-danger/10 border-danger/20',
  critical: 'text-white bg-danger border-danger',
}
const LEVEL_BAR = { low: 'bg-success', medium: 'bg-warn', high: 'bg-danger', critical: 'bg-danger' }

const STATUS_META = {
  active: { label: 'Active Investigation', cls: 'text-danger bg-danger/10 border-danger/25', live: true },
  paused: { label: 'Monitoring Paused', cls: 'text-purple-400 bg-purple-500/10 border-purple-500/25' },
  terminated: { label: 'Terminated Investigation', cls: 'text-slate-400 bg-white/5 border-white/10' },
  expired: { label: 'Expired Investigation', cls: 'text-slate-400 bg-white/5 border-white/10' },
}

const MODE_META = {
  ai_persona: { label: 'AI Persona Mode', icon: Bot, cls: 'text-accent bg-accent/10 border-accent/25' },
  admin_manual: { label: 'Admin Manual Control', icon: UserCog, cls: 'text-warn bg-warn/10 border-warn/25' },
}

const CATEGORY_LABELS = {
  unauthorized_access: 'Unauthorized access',
  private_conversation_access: 'Private conversation access',
  credential_theft: 'Credential theft',
  database_exploitation: 'Database exploitation',
  auth_bypass: 'Authentication bypass',
  sensitive_data_extraction: 'Sensitive data extraction',
  privilege_escalation: 'Privilege escalation',
  prompt_injection: 'Prompt injection',
}
const catLabel = c => CATEGORY_LABELS[c] || (c ? c.replace(/_/g, ' ') : 'Unclassified')

const OPEN = ['active', 'paused']

/* ── motion language ─────────────────────────────────────────────────────
   Reuses the app's shared `ease` curve; springs for anything interactive so
   state changes settle naturally rather than snapping. MotionConfig below
   honours the OS "reduce motion" setting for every animation in here. */
const spring = { type: 'spring', stiffness: 420, damping: 34, mass: 0.7 }
const softSpring = { type: 'spring', stiffness: 170, damping: 26 }
const sectionStagger = { hidden: {}, show: { transition: { staggerChildren: 0.09, delayChildren: 0.04 } } }
const listStagger = { hidden: {}, show: { transition: { staggerChildren: 0.05 } } }
const rise = {
  hidden: { opacity: 0, y: 16, filter: 'blur(6px)' },
  show: { opacity: 1, y: 0, filter: 'blur(0px)', transition: { duration: 0.7, ease } },
}
const itemRise = {
  hidden: { opacity: 0, y: 10 },
  show: { opacity: 1, y: 0, transition: { duration: 0.45, ease } },
}
const press = { whileHover: { y: -1 }, whileTap: { scale: 0.96 }, transition: spring }
const collapse = {
  initial: { opacity: 0, height: 0 },
  animate: { opacity: 1, height: 'auto', transition: { height: { duration: 0.35, ease }, opacity: { duration: 0.25, delay: 0.08 } } },
  exit: { opacity: 0, height: 0, transition: { height: { duration: 0.3, ease }, opacity: { duration: 0.15 } } },
}
const swap = {
  initial: { opacity: 0, y: -6, scale: 0.92 },
  animate: { opacity: 1, y: 0, scale: 1, transition: spring },
  exit: { opacity: 0, y: 6, scale: 0.92, transition: { duration: 0.15 } },
}

function fmtDuration(totalSeconds) {
  const s = Math.max(0, Math.floor(totalSeconds || 0))
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  return h ? `${h}h ${String(m).padStart(2, '0')}m` : `${m}m ${String(sec).padStart(2, '0')}s`
}
const fmtTime = iso => (iso ? new Date(iso).toLocaleTimeString() : '')

function errMsg(err, fallback) {
  return err?.response?.data?.error || fallback
}

/* Counts smoothly toward `value` instead of jumping. */
function AnimatedNumber({ value }) {
  const mv = useSpring(0, { stiffness: 90, damping: 20 })
  const rounded = useTransform(mv, v => Math.round(v))
  useEffect(() => { mv.set(value || 0) }, [value, mv])
  return <motion.span>{rounded}</motion.span>
}

/* Pulsing dot with an expanding ring, for anything live. */
function LiveDot({ tone = 'bg-danger' }) {
  return (
    <span className="relative inline-flex w-1.5 h-1.5">
      <motion.span className={`absolute inset-0 rounded-full ${tone}`}
        animate={{ scale: [1, 2.6], opacity: [0.6, 0] }}
        transition={{ duration: 1.6, repeat: Infinity, ease: 'easeOut' }} />
      <span className={`relative w-1.5 h-1.5 rounded-full ${tone}`} />
    </span>
  )
}

/* Segmented filter with a pill that glides between options. */
function Segmented({ id, options, value, onChange }) {
  return (
    <div className="relative flex gap-0.5 p-0.5 rounded-lg border border-white/8 bg-bg-900/40">
      {options.map(opt => (
        <button key={opt} onClick={() => onChange(opt)}
          className={`relative px-2 py-1 rounded-md text-[10px] font-mono uppercase transition-colors duration-300 ${value === opt ? 'text-accent' : 'text-slate-500 hover:text-slate-300'}`}>
          {value === opt && (
            <motion.span layoutId={`seg-${id}`} transition={spring}
              className="absolute inset-0 rounded-md bg-accent/10 border border-accent/25" />
          )}
          <span className="relative">{opt}</span>
        </button>
      ))}
    </div>
  )
}

function LevelBadge({ level, score }) {
  return (
    <span className={`inline-flex px-1.5 py-0.5 rounded border text-[9px] font-mono font-bold uppercase transition-colors duration-500 ${LEVEL_STYLE[level] || LEVEL_STYLE.low}`}>
      {level}{score !== undefined && score !== null ? <>&nbsp;·&nbsp;<AnimatedNumber value={score} /></> : ''}
    </span>
  )
}

function ThreatMeter({ score = 0, level = 'low' }) {
  return (
    <div className="flex items-center gap-2">
      <div className="relative flex-1 h-1.5 rounded-full bg-bg-900 overflow-hidden">
        <motion.div className={`h-full rounded-full transition-colors duration-700 ${LEVEL_BAR[level] || 'bg-success'}`}
          initial={{ width: 0 }} animate={{ width: `${score}%` }} transition={softSpring} />
        {level === 'critical' && (
          // slow sheen sweeping across a critical bar
          <motion.div className="absolute inset-y-0 w-1/4 bg-gradient-to-r from-transparent via-white/40 to-transparent"
            initial={{ x: '-100%' }} animate={{ x: '400%' }}
            transition={{ duration: 2.2, repeat: Infinity, ease: 'easeInOut', repeatDelay: 0.6 }} />
        )}
      </div>
      <span className="text-[10px] font-mono font-bold text-slate-300 w-12 text-right"><AnimatedNumber value={score} />/100</span>
    </div>
  )
}

function StatusBadge({ status }) {
  const meta = STATUS_META[status] || STATUS_META.terminated
  return (
    <AnimatePresence mode="popLayout" initial={false}>
      <motion.span key={status} {...swap} layout
        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md border text-[10px] font-mono uppercase ${meta.cls}`}>
        {meta.live && <LiveDot />}
        {meta.label}
      </motion.span>
    </AnimatePresence>
  )
}

function ModeBadge({ mode, muted }) {
  const meta = MODE_META[mode] || MODE_META.ai_persona
  const Icon = meta.icon
  return (
    <AnimatePresence mode="popLayout" initial={false}>
      <motion.span key={`${mode}-${muted}`} {...swap} layout
        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border text-[10px] font-mono uppercase ${muted ? 'text-slate-500 border-white/10' : meta.cls}`}>
        <Icon size={10} />{meta.label}
      </motion.span>
    </AnimatePresence>
  )
}

/* Confirmation modal with optional reason + mode chooser. Server also
   enforces confirmation (confirm: true) for every sensitive action.
   Centred with a flex wrapper rather than translate classes, because
   framer-motion's inline transform would override Tailwind's translate. */
function ActionDialog({ dialog, onClose }) {
  const [reason, setReason] = useState('')
  const [mode, setMode] = useState('ai_persona')
  const [busy, setBusy] = useState(false)
  useEffect(() => { setReason(''); setMode('ai_persona'); setBusy(false) }, [dialog])
  const run = async () => {
    setBusy(true)
    try { await dialog.onConfirm({ reason, mode }); onClose() } catch { setBusy(false) }
  }
  return (
    <AnimatePresence>
      {dialog && (
        <motion.div key="dialog" className="fixed inset-0 z-[60] flex items-center justify-center p-4"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, transition: { duration: 0.2 } }}>
          <motion.div onClick={onClose} className="absolute inset-0 bg-black/60"
            initial={{ backdropFilter: 'blur(0px)' }} animate={{ backdropFilter: 'blur(4px)' }} exit={{ backdropFilter: 'blur(0px)' }} />
          <motion.div role="alertdialog" aria-modal="true"
            initial={{ opacity: 0, scale: 0.94, y: 14 }} animate={{ opacity: 1, scale: 1, y: 0, transition: spring }}
            exit={{ opacity: 0, scale: 0.96, y: 8, transition: { duration: 0.18 } }}
            className="relative w-full max-w-md glass border border-white/10 rounded-2xl p-5 shadow-card">
            <div className="flex items-start gap-3">
              <motion.div initial={{ rotate: -12, scale: 0.6 }} animate={{ rotate: 0, scale: 1 }} transition={{ ...spring, delay: 0.06 }}
                className={`w-9 h-9 rounded-xl flex items-center justify-center border flex-shrink-0 ${dialog.danger ? 'bg-danger/10 border-danger/25 text-danger' : 'bg-accent/10 border-accent/25 text-accent'}`}>
                <AlertTriangle size={16} />
              </motion.div>
              <div className="flex-1">
                <h3 className="text-sm font-bold text-white">{dialog.title}</h3>
                <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">{dialog.message}</p>
              </div>
            </div>
            {dialog.chooseMode && (
              <div className="mt-4 grid grid-cols-2 gap-2">
                {Object.entries(MODE_META).map(([key, meta]) => {
                  const Icon = meta.icon
                  const active = mode === key
                  return (
                    <motion.button key={key} onClick={() => setMode(key)} {...press}
                      className={`relative rounded-xl border p-3 text-left transition-colors duration-300 ${active ? meta.cls : 'border-white/8 text-slate-400 hover:border-white/20'}`}>
                      <motion.span animate={{ scale: active ? 1.15 : 1, rotate: active ? -6 : 0 }} transition={spring} className="inline-block">
                        <Icon size={14} />
                      </motion.span>
                      <p className="text-xs font-semibold mt-1.5">{meta.label}</p>
                      <p className="text-[10px] opacity-70 mt-0.5">{key === 'ai_persona' ? 'Decoy AI engages the user' : 'You reply directly'}</p>
                    </motion.button>
                  )
                })}
              </div>
            )}
            {dialog.withReason && (
              <textarea value={reason} onChange={e => setReason(e.target.value)} rows={2} maxLength={500}
                placeholder="Reason (recorded in the audit log)"
                className="mt-4 w-full px-3 py-2 rounded-xl bg-bg-800 border border-white/8 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-accent/40 transition-colors" />
            )}
            <div className="flex justify-end gap-2 mt-5">
              <motion.button {...press} onClick={onClose} className="px-3 py-2 rounded-xl border border-white/10 text-xs text-slate-300 hover:bg-white/5">Cancel</motion.button>
              <motion.button {...press} onClick={run} disabled={busy}
                className={`px-3 py-2 rounded-xl border text-xs font-semibold disabled:opacity-40 min-w-[88px] ${dialog.danger ? 'bg-danger/80 hover:bg-danger border-danger/40 text-white' : 'bg-accent text-bg-900 border-accent'}`}>
                <AnimatePresence mode="wait" initial={false}>
                  <motion.span key={busy ? 'busy' : 'idle'} className="inline-block"
                    initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }} transition={{ duration: 0.15 }}>
                    {busy ? 'Working…' : dialog.confirmLabel}
                  </motion.span>
                </AnimatePresence>
              </motion.button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

/* ── Threat alert card ──────────────────────────────────────────────────── */
function AlertCard({ alert, highlighted, fresh, onActivate, onDismiss, onOpenInvestigation }) {
  const [open, setOpen] = useState(highlighted)
  const [context, setContext] = useState(null)
  const ref = useRef(null)

  const loadContext = useCallback(async () => {
    try {
      const { data } = await api.get(`/ghost/alerts/${alert.id}`)
      setContext(data.alert)
    } catch (err) {
      toast.error(errMsg(err, 'Could not load conversation'))
    }
  }, [alert.id])

  useEffect(() => {
    if (open && !context) loadContext()
  }, [open, context, loadContext])
  useEffect(() => {
    if (highlighted) ref.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [highlighted])

  return (
    <motion.div ref={ref} layout
      initial={{ opacity: 0, y: -14, scale: 0.97 }}
      animate={{ opacity: alert.status === 'dismissed' ? 0.5 : 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, x: -28, scale: 0.97, transition: { duration: 0.25, ease } }}
      transition={{ layout: spring, default: { duration: 0.45, ease } }}
      className={`relative rounded-xl border p-3 transition-colors duration-500 ${highlighted ? 'border-accent/40 bg-accent/5' : 'bg-bg-800/70 border-danger/15'}`}>
      {(fresh || highlighted) && (
        // attention ring for an alert that just arrived / was deep-linked
        <motion.span aria-hidden className={`pointer-events-none absolute -inset-px rounded-xl border-2 ${highlighted ? 'border-accent' : 'border-danger'}`}
          initial={{ opacity: 0 }} animate={{ opacity: [0, 0.9, 0, 0.6, 0] }} transition={{ duration: 2.2, ease: 'easeInOut' }} />
      )}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-mono text-danger font-bold">{alert.username}</span>
        <LevelBadge level={alert.threat_level} score={alert.threat_score} />
        <span className="text-[10px] font-mono text-slate-400">{catLabel(alert.category)}</span>
        <AnimatePresence initial={false}>
          {alert.status !== 'open' && (
            <motion.span key={alert.status} {...swap}
              className="text-[9px] font-mono uppercase text-slate-500 border border-white/10 px-1.5 py-0.5 rounded">{alert.status}</motion.span>
          )}
        </AnimatePresence>
        <span className="ml-auto text-[10px] font-mono text-slate-600">{fmtTime(alert.created_at)}</span>
      </div>
      <p className="text-[11px] text-slate-300 mt-1.5 break-words">“{alert.message}”</p>
      <div className="flex flex-wrap items-center gap-2 mt-2">
        <button onClick={() => setOpen(v => !v)} className="text-[10px] font-mono text-slate-400 hover:text-accent inline-flex items-center gap-1 transition-colors">
          <Eye size={10} />Conversation
          <motion.span animate={{ rotate: open ? 180 : 0 }} transition={spring} className="inline-flex"><ChevronDown size={10} /></motion.span>
        </button>
        <div className="ml-auto flex gap-1.5">
          <AnimatePresence mode="popLayout" initial={false}>
            {alert.investigation_id ? (
              <motion.button key="open" {...swap} {...press} onClick={() => onOpenInvestigation(alert.investigation_id)}
                className="px-2.5 py-1 rounded-lg border border-accent/25 bg-accent/10 text-[10px] text-accent font-semibold">
                Open investigation
              </motion.button>
            ) : alert.status === 'open' && (
              <motion.div key="actions" {...swap} className="flex gap-1.5">
                <motion.button {...press} onClick={() => onDismiss(alert)} className="px-2.5 py-1 rounded-lg border border-white/10 text-[10px] text-slate-400 hover:text-white transition-colors">Dismiss</motion.button>
                <motion.button {...press} onClick={() => onActivate(alert)}
                  className="group px-2.5 py-1 rounded-lg border border-danger/30 bg-danger/15 hover:bg-danger/25 text-[10px] text-danger font-bold inline-flex items-center gap-1 transition-colors">
                  <Crosshair size={10} className="transition-transform duration-500 group-hover:rotate-90" />Activate Interactive Ghost Mode
                </motion.button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div key="ctx" {...collapse} className="overflow-hidden">
            <motion.div variants={listStagger} initial="hidden" animate={context ? 'show' : 'hidden'}
              className="mt-2 space-y-1.5 max-h-56 overflow-y-auto pr-1">
              {!context && <p className="text-[10px] text-slate-500 font-mono animate-pulse">Loading…</p>}
              {context?.signals?.length > 0 && (
                <motion.div variants={itemRise} className="text-[10px] font-mono text-warn/80 space-y-0.5">
                  {context.signals.map(s => <p key={s}>• {s}</p>)}
                </motion.div>
              )}
              {context?.conversation?.map(row => (
                <motion.div key={row.audit_log_id} variants={itemRise}
                  className={`rounded-lg border p-2 text-[11px] ${row.is_flagged_message ? 'border-danger/30 bg-danger/5' : 'border-white/6 bg-bg-900/40'}`}>
                  <p className="text-slate-200"><span className="text-accent font-mono">{alert.username}:</span> {row.query}</p>
                  {row.response && <p className="text-slate-500 mt-1 line-clamp-2">↳ {row.response}</p>}
                </motion.div>
              ))}
              {context && context.conversation?.length === 0 && <p className="text-[10px] text-slate-500 font-mono">No prior chatbot history.</p>}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

/* ── Message bubble in the live console ─────────────────────────────────── */
const BUBBLE = {
  suspect: { wrap: 'justify-start', box: 'bg-danger/5 border-danger/20', tone: 'text-danger', from: { x: -22, rotate: -1.5 }, origin: 'left' },
  ai_persona: { wrap: 'justify-end', box: 'bg-accent/5 border-accent/20', tone: 'text-accent', from: { x: 22, rotate: 1.5 }, origin: 'right' },
  admin: { wrap: 'justify-end', box: 'bg-warn/5 border-warn/25', tone: 'text-warn', from: { x: 22, rotate: 1.5 }, origin: 'right' },
  system: { wrap: 'justify-center', box: 'bg-white/5 border-white/10', tone: 'text-slate-400', from: { y: 8 }, origin: 'center' },
}

function ConsoleMessage({ m, target }) {
  const style = BUBBLE[m.sender_type] || BUBBLE.system
  const who = { suspect: `${target} · suspect`, ai_persona: 'AI Persona', admin: `Admin · ${m.sender_username || ''}`, system: 'system' }[m.sender_type]
  return (
    <motion.div layout="position" className={`flex ${style.wrap}`}
      initial={{ opacity: 0, scale: 0.92, ...style.from }}
      animate={{ opacity: 1, scale: 1, x: 0, y: 0, rotate: 0 }}
      transition={{ ...spring, opacity: { duration: 0.25 } }}
      style={{ transformOrigin: style.origin }}>
      <div className={`max-w-[82%] rounded-xl border px-3 py-2 ${style.box}`}>
        <p className={`text-[10px] font-mono mb-1 flex items-center gap-2 ${style.tone}`}>
          {m.sender_type === 'ai_persona' && <Bot size={10} />}
          {m.sender_type === 'admin' && <UserCog size={10} />}
          {who}
          <span className="text-slate-600">{fmtTime(m.created_at)}</span>
          {m.sender_type === 'suspect' && m.threat_level && <LevelBadge level={m.threat_level} score={m.threat_score} />}
        </p>
        <p className="text-xs text-slate-200 whitespace-pre-wrap break-words">{m.content}</p>
        {m.sender_type === 'suspect' && m.categories?.length > 0 && (
          <p className="text-[9px] font-mono text-danger/70 mt-1">{m.categories.map(catLabel).join(' · ')}</p>
        )}
      </div>
    </motion.div>
  )
}

/* Shown when the suspect is waiting on the controlling admin. */
function AwaitingReply() {
  return (
    <motion.div layout="position" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 6 }}
      className="flex justify-end">
      <div className="rounded-xl border border-warn/25 bg-warn/5 px-3 py-2 flex items-center gap-2">
        <span className="text-[10px] font-mono text-warn">awaiting your reply</span>
        <span className="flex gap-1">
          {[0, 1, 2].map(i => (
            <motion.span key={i} className="w-1 h-1 rounded-full bg-warn"
              animate={{ y: [0, -3, 0], opacity: [0.4, 1, 0.4] }}
              transition={{ duration: 0.9, repeat: Infinity, delay: i * 0.15, ease: 'easeInOut' }} />
          ))}
        </span>
      </div>
    </motion.div>
  )
}

const EVENT_TONE = {
  activated: 'text-danger', admin_takeover: 'text-warn', control_transferred: 'text-warn',
  persona_resumed: 'text-accent', control_lease_expired: 'text-accent', paused: 'text-purple-400',
  resumed: 'text-success', terminated: 'text-slate-300', expired: 'text-slate-400',
  user_suspended: 'text-danger', persona_guard: 'text-warn', report_exported: 'text-slate-400',
  admin_message: 'text-warn',
}
const EVENT_DOT = {
  activated: 'bg-danger', admin_takeover: 'bg-warn', control_transferred: 'bg-warn', persona_resumed: 'bg-accent',
  control_lease_expired: 'bg-accent', paused: 'bg-purple-400', resumed: 'bg-success', user_suspended: 'bg-danger',
  persona_guard: 'bg-warn', admin_message: 'bg-warn',
}

/* ── main console ───────────────────────────────────────────────────────── */
export default function GhostInvestigationConsole({ focusAlertId, focusInvestigationId, activationRequest, onActivationHandled }) {
  const { user, token } = useAuth()
  const [alerts, setAlerts] = useState([])
  const [freshAlertIds, setFreshAlertIds] = useState(() => new Set())
  const [threshold, setThreshold] = useState(null)
  const [alertFilter, setAlertFilter] = useState('open')
  const [investigations, setInvestigations] = useState([])
  const [invFilter, setInvFilter] = useState('open')
  const [selectedId, setSelectedId] = useState(focusInvestigationId || null)
  const [detail, setDetail] = useState(null)
  const [questions, setQuestions] = useState([])
  const [newQuestion, setNewQuestion] = useState('')
  const [showQuestionEditor, setShowQuestionEditor] = useState(false)
  const [draft, setDraft] = useState('')
  const [draftQuestionId, setDraftQuestionId] = useState(null)
  const [sending, setSending] = useState(false)
  const [dialog, setDialog] = useState(null)
  const [now, setNow] = useState(Date.now())
  const [socketOk, setSocketOk] = useState(false)
  const chatScrollRef = useRef(null)
  const inputRef = useRef(null)
  const selectedRef = useRef(selectedId)
  selectedRef.current = selectedId

  /* data loading */
  const loadAlerts = useCallback(async () => {
    try {
      const { data } = await api.get('/ghost/alerts', { params: alertFilter === 'all' ? {} : { status: alertFilter } })
      setAlerts(data.alerts || [])
      setThreshold(data.threshold)
    } catch { /* surfaced by empty state */ }
  }, [alertFilter])

  const loadInvestigations = useCallback(async () => {
    try {
      const { data } = await api.get('/ghost/investigations', { params: invFilter === 'all' ? {} : { status: 'open' } })
      setInvestigations(data.investigations || [])
    } catch { /* ignore */ }
  }, [invFilter])

  const loadDetail = useCallback(async (id) => {
    if (!id) { setDetail(null); return }
    try {
      const { data } = await api.get(`/ghost/investigations/${id}`)
      setDetail(data.investigation)
    } catch (err) {
      toast.error(errMsg(err, 'Could not load investigation'))
    }
  }, [])

  const loadQuestions = useCallback(async () => {
    try {
      const { data } = await api.get('/ghost/questions')
      setQuestions(data.questions || [])
    } catch { /* ignore */ }
  }, [])

  useEffect(() => { loadAlerts() }, [loadAlerts])
  useEffect(() => { loadInvestigations() }, [loadInvestigations])
  useEffect(() => { loadQuestions() }, [loadQuestions])
  useEffect(() => { loadDetail(selectedId) }, [selectedId, loadDetail])
  useEffect(() => { if (focusInvestigationId) setSelectedId(focusInvestigationId) }, [focusInvestigationId])

  /* ticking clock for live durations */
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(t)
  }, [])

  /* real-time feed over the authenticated admin room */
  useEffect(() => {
    const socket = joinGhostAdminRoom(token)
    const onJoined = () => setSocketOk(true)
    const onDenied = () => { setSocketOk(false); toast.error('Live monitoring unavailable: admin authentication failed') }
    const onAlert = (alert) => {
      setAlerts(prev => {
        const idx = prev.findIndex(a => a.id === alert.id)
        if (idx >= 0) { const copy = [...prev]; copy[idx] = alert; return copy }
        if (alert.status === 'open') toast(`Threat alert: ${alert.username} (${alert.threat_level.toUpperCase()} ${alert.threat_score})`, { icon: '🚨' })
        return [alert, ...prev]
      })
      setFreshAlertIds(prev => new Set(prev).add(alert.id))
      setTimeout(() => setFreshAlertIds(prev => { const next = new Set(prev); next.delete(alert.id); return next }), 2500)
    }
    const onUpdated = (inv) => {
      setInvestigations(prev => {
        const idx = prev.findIndex(i => i.id === inv.id)
        if (idx >= 0) { const copy = [...prev]; copy[idx] = inv; return copy }
        return [inv, ...prev]
      })
      if (inv.id === selectedRef.current) setDetail(prev => (prev ? { ...prev, ...inv } : prev))
    }
    const onMessage = ({ investigation_id, message }) => {
      if (investigation_id !== selectedRef.current) return
      setDetail(prev => {
        if (!prev || prev.messages?.some(m => m.id === message.id)) return prev
        return { ...prev, messages: [...(prev.messages || []), message] }
      })
    }
    const onEvent = ({ investigation_id, event }) => {
      if (investigation_id !== selectedRef.current) return
      setDetail(prev => {
        if (!prev || prev.events?.some(e => e.id === event.id)) return prev
        return { ...prev, events: [...(prev.events || []), event] }
      })
    }
    const onDisconnect = () => setSocketOk(false)
    socket.on('admin_room_joined', onJoined)
    socket.on('admin_room_denied', onDenied)
    socket.on('ghost_threat_alert', onAlert)
    socket.on('ghost_investigation_updated', onUpdated)
    socket.on('ghost_investigation_message', onMessage)
    socket.on('ghost_investigation_event', onEvent)
    socket.on('disconnect', onDisconnect)
    return () => {
      socket.off('disconnect', onDisconnect)
      socket.off('admin_room_joined', onJoined)
      socket.off('admin_room_denied', onDenied)
      socket.off('ghost_threat_alert', onAlert)
      socket.off('ghost_investigation_updated', onUpdated)
      socket.off('ghost_investigation_message', onMessage)
      socket.off('ghost_investigation_event', onEvent)
    }
  }, [token])

  /* polling fallback when the socket is down */
  useEffect(() => {
    if (socketOk) return undefined
    const t = setInterval(() => {
      loadAlerts(); loadInvestigations()
      if (selectedRef.current) loadDetail(selectedRef.current)
    }, 5000)
    return () => clearInterval(t)
  }, [socketOk, loadAlerts, loadInvestigations, loadDetail])

  /* glide the conversation pane (not the whole page) to the newest message */
  useEffect(() => {
    const el = chatScrollRef.current
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }, [detail?.messages?.length, detail?.id])

  /* ── actions ── */
  const activate = useCallback((target) => {
    setDialog({
      title: 'Activate Interactive Ghost Mode?',
      message: `${target.username}'s chatbot traffic will be silently diverted into the isolated decoy environment. No real data is reachable from the decoy. This action is recorded in the audit log.`,
      confirmLabel: 'Activate',
      danger: true,
      chooseMode: true,
      onConfirm: async ({ mode }) => {
        try {
          const { data } = await api.post('/ghost/investigations', {
            confirm: true, mode,
            ...(target.alert_id ? { alert_id: target.alert_id } : {}),
            ...(target.legacy_session_id ? { legacy_session_id: target.legacy_session_id } : {}),
            username: target.username,
          })
          toast.success(`Investigation GHOST-${String(data.investigation.id).padStart(3, '0')} active`)
          setInvFilter('open')
          setSelectedId(data.investigation.id)
          loadInvestigations(); loadAlerts()
        } catch (err) {
          if (err?.response?.data?.code === 'investigation_exists') {
            setSelectedId(err.response.data.investigation_id)
            toast('An investigation is already open for this user. Opened it.')
            return
          }
          toast.error(errMsg(err, 'Activation failed'))
          throw err
        }
      },
    })
  }, [loadAlerts, loadInvestigations])

  /* activation requested from the legacy (normal Ghost Mode) session list */
  useEffect(() => {
    if (activationRequest) { activate(activationRequest); onActivationHandled?.() }
  }, [activationRequest, activate, onActivationHandled])

  const dismissAlert = async (alert) => {
    try {
      await api.post(`/ghost/alerts/${alert.id}/dismiss`, { note: 'Reviewed — not malicious' })
      loadAlerts()
    } catch (err) { toast.error(errMsg(err, 'Could not dismiss alert')) }
  }

  const post = async (path, body = {}, okMsg) => {
    try {
      const { data } = await api.post(`/ghost/investigations/${detail.id}/${path}`, body)
      if (data.investigation) setDetail(prev => ({ ...prev, ...data.investigation }))
      if (okMsg) toast.success(okMsg)
      loadInvestigations()
      return data
    } catch (err) {
      const code = err?.response?.data?.code
      if (code === 'control_held') {
        setDialog({
          title: 'Take over from another administrator?',
          message: `${err.response.data.controlling_admin} currently holds manual control. A forced takeover is logged and visible in the timeline.`,
          confirmLabel: 'Force takeover',
          danger: true,
          onConfirm: async () => { await post('mode', { mode: 'admin_manual', force: true }, 'You now hold manual control') },
        })
        return null
      }
      toast.error(errMsg(err, 'Action failed'))
      throw err
    }
  }

  const switchMode = mode => post('mode', { mode }, mode === 'admin_manual' ? 'Admin Manual Control engaged' : 'Handed back to AI Persona').catch(() => {})

  const sendMessage = async () => {
    const text = draft.trim()
    if (!text || !detail) return
    setSending(true)
    try {
      const body = { message: text }
      if (draftQuestionId && questions.find(q => q.id === draftQuestionId)?.text === text) body.question_id = draftQuestionId
      const { data } = await api.post(`/ghost/investigations/${detail.id}/messages`, body)
      setDetail(prev => (prev.messages?.some(m => m.id === data.message.id) ? prev : { ...prev, messages: [...prev.messages, data.message] }))
      setDraft(''); setDraftQuestionId(null)
    } catch (err) {
      toast.error(errMsg(err, 'Message not sent'))
    } finally {
      setSending(false)
    }
  }

  const pickQuestion = (q) => {
    setDraft(q.text); setDraftQuestionId(q.id)
    inputRef.current?.focus()
  }

  const exportReport = async (format) => {
    try {
      const res = await api.get(`/ghost/investigations/${detail.id}/report`, { params: { format }, responseType: 'blob' })
      const url = window.URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = `secureai-ghost-${String(detail.id).padStart(3, '0')}-report.${format}`
      a.click()
      window.URL.revokeObjectURL(url)
      loadDetail(detail.id)
    } catch (err) { toast.error(errMsg(err, 'Export failed')) }
  }

  const addQuestion = async () => {
    const text = newQuestion.trim()
    if (!text) return
    try {
      await api.post('/ghost/questions', { text })
      setNewQuestion(''); loadQuestions()
    } catch (err) { toast.error(errMsg(err, 'Could not save question')) }
  }
  const deleteQuestion = async (q) => {
    try { await api.delete(`/ghost/questions/${q.id}`); loadQuestions() } catch (err) { toast.error(errMsg(err, 'Could not delete')) }
  }

  /* ── derived ── */
  const openAlerts = alerts.filter(a => a.status === 'open')
  const isOpen = detail && OPEN.includes(detail.status)
  const iControl = detail?.interaction_mode === 'admin_manual' && detail?.controlling_admin === user?.username
  const awaitingAdmin = iControl && detail?.messages?.length > 0 && detail.messages[detail.messages.length - 1].sender_type === 'suspect'
  const liveDuration = useMemo(() => {
    if (!detail?.started_at) return 0
    const end = detail.ended_at ? new Date(detail.ended_at).getTime() : now
    return (end - new Date(detail.started_at).getTime()) / 1000
  }, [detail?.started_at, detail?.ended_at, now])
  const timeline = useMemo(() => [...(detail?.events || [])].reverse(), [detail?.events])

  return (
    <MotionConfig reducedMotion="user">
      <motion.div className="space-y-6" variants={sectionStagger} initial="hidden" animate="show">
        <ActionDialog dialog={dialog} onClose={() => setDialog(null)} />

        {/* Section header */}
        <motion.div variants={rise} className="flex flex-wrap items-center gap-3">
          <motion.div className="w-9 h-9 rounded-xl bg-danger/10 border border-danger/25 flex items-center justify-center"
            animate={{ rotate: [0, 90, 90, 180, 180, 270, 270, 360] }}
            transition={{ duration: 14, repeat: Infinity, ease: 'easeInOut' }}>
            <Crosshair size={16} className="text-danger" />
          </motion.div>
          <div>
            <h2 className="text-lg font-bold text-white">Interactive Investigations</h2>
            <p className="text-[10px] text-slate-500 font-mono uppercase tracking-widest">
              Threat detection → alert → decoy engagement → evidence → action
            </p>
          </div>
          <div className="ml-auto flex items-center gap-2 text-[10px] font-mono">
            <motion.span layout transition={spring}
              className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-lg border transition-colors duration-500 ${socketOk ? 'text-success border-success/20 bg-success/10' : 'text-warn border-warn/20 bg-warn/10'}`}>
              {socketOk ? <LiveDot tone="bg-success" /> : <span className="w-1.5 h-1.5 rounded-full bg-warn" />}
              <AnimatePresence mode="wait" initial={false}>
                <motion.span key={socketOk ? 'live' : 'poll'} initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }} transition={{ duration: 0.2 }}>
                  {socketOk ? 'Live (secured socket)' : 'Polling fallback'}
                </motion.span>
              </AnimatePresence>
            </motion.span>
            {threshold !== null && <span className="px-2 py-1 rounded-lg border border-white/10 text-slate-400">Alert threshold {threshold}/100</span>}
          </div>
        </motion.div>

        {/* Threat alerts */}
        <motion.div variants={rise} className="glass rounded-2xl p-5 border border-danger/15">
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <ShieldAlert size={15} className="text-danger" />
            <p className="text-sm font-bold text-white">Threat Alerts</p>
            <motion.span key={openAlerts.length} initial={{ scale: 1.35 }} animate={{ scale: 1 }} transition={spring}
              className="px-2 py-0.5 rounded-md bg-danger/10 border border-danger/20 text-[10px] text-danger font-mono">
              {openAlerts.length} open
            </motion.span>
            <div className="ml-auto">
              <Segmented id="alerts" options={['open', 'investigating', 'dismissed', 'all']} value={alertFilter} onChange={setAlertFilter} />
            </div>
          </div>
          <motion.div layout className="flex flex-col gap-2 max-h-[340px] overflow-y-auto pr-1" transition={spring}>
            <AnimatePresence initial={false} mode="popLayout">
              {alerts.length === 0 && (
                <motion.p key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                  className="text-xs text-slate-500 font-mono py-4 text-center">
                  No threat alerts in this view. Chatbot messages scoring at or above the threshold appear here instantly.
                </motion.p>
              )}
              {alerts.map(a => (
                <AlertCard key={a.id} alert={a} highlighted={Number(focusAlertId) === a.id} fresh={freshAlertIds.has(a.id)}
                  onActivate={alert => activate({ username: alert.username, alert_id: alert.id })}
                  onDismiss={dismissAlert}
                  onOpenInvestigation={id => { setInvFilter('all'); setSelectedId(id) }} />
              ))}
            </AnimatePresence>
          </motion.div>
        </motion.div>

        {/* Investigations */}
        <motion.div variants={rise} className="grid grid-cols-1 xl:grid-cols-[0.6fr_1.4fr] gap-6">
          <div className="glass rounded-2xl p-5 border border-white/5 h-fit">
            <div className="flex items-center gap-2 mb-3">
              <Radar size={15} className="text-accent" />
              <p className="text-sm font-bold text-white">Investigations</p>
              <div className="ml-auto">
                <Segmented id="investigations" options={['open', 'all']} value={invFilter} onChange={setInvFilter} />
              </div>
            </div>
            <motion.div className="flex flex-col gap-3" variants={listStagger} initial="hidden" animate="show" key={invFilter}>
              <AnimatePresence initial={false} mode="popLayout">
                {investigations.length === 0 && (
                  <motion.p key="empty" variants={itemRise} exit={{ opacity: 0 }} className="text-xs text-slate-500 font-mono">
                    No investigations. Activate one from a threat alert or a honeypot session.
                  </motion.p>
                )}
                {investigations.map(inv => {
                  const ended = !OPEN.includes(inv.status)
                  const selected = selectedId === inv.id
                  return (
                    <motion.button key={inv.id} layout variants={itemRise} exit={{ opacity: 0, scale: 0.96, transition: { duration: 0.2 } }}
                      transition={{ layout: spring }} whileHover={{ x: 3 }} whileTap={{ scale: 0.985 }}
                      onClick={() => setSelectedId(inv.id)}
                      className={`relative w-full text-left rounded-2xl border p-3.5 transition-[border-color,opacity] duration-300 ${selected ? 'border-accent/25' : 'bg-bg-800/70 border-white/8 hover:border-accent/20'} ${ended ? 'opacity-70' : ''}`}>
                      {selected && (
                        <motion.span layoutId="inv-selected" transition={spring}
                          className="absolute inset-0 rounded-2xl bg-accent/10 border border-accent/25" />
                      )}
                      <span className="relative block">
                        <span className="flex items-center justify-between gap-2">
                          <span className="text-sm font-semibold text-white font-mono">{inv.target_username}</span>
                          <span className="text-[10px] font-mono text-slate-500">GHOST-{String(inv.id).padStart(3, '0')}</span>
                        </span>
                        <span className="flex flex-wrap gap-1.5 mt-2">
                          <StatusBadge status={inv.status} />
                          {!ended && <ModeBadge mode={inv.interaction_mode} />}
                        </span>
                        <span className="block mt-2"><ThreatMeter score={inv.threat_score} level={inv.threat_level} /></span>
                        <span className="block text-[10px] text-slate-500 font-mono mt-1.5">
                          <AnimatedNumber value={inv.message_count} /> messages · {catLabel(inv.threat_category)}
                        </span>
                      </span>
                    </motion.button>
                  )
                })}
              </AnimatePresence>
            </motion.div>
          </div>

          {/* Live console */}
          <motion.div layout transition={{ layout: { duration: 0.4, ease } }}
            className="glass rounded-2xl p-5 border border-white/5 flex flex-col min-h-[520px] overflow-hidden">
            <AnimatePresence mode="wait" initial={false}>
              {!detail ? (
                <motion.div key="empty" className="flex-1 flex flex-col items-center justify-center text-center gap-3"
                  initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.97 }}
                  transition={{ duration: 0.35, ease }}>
                  <motion.div animate={{ scale: [1, 1.08, 1], opacity: [0.5, 0.9, 0.5] }} transition={{ duration: 2.8, repeat: Infinity, ease: 'easeInOut' }}>
                    <Crosshair size={30} className="text-slate-500" />
                  </motion.div>
                  <p className="text-xs text-slate-500 font-mono">Select an investigation to open the live console.</p>
                </motion.div>
              ) : (
                <motion.div key={detail.id} className="flex flex-col gap-4 flex-1 min-h-0"
                  initial={{ opacity: 0, y: 14, filter: 'blur(6px)' }}
                  animate={{ opacity: 1, y: 0, filter: 'blur(0px)', transition: { duration: 0.45, ease } }}
                  exit={{ opacity: 0, y: -8, filter: 'blur(4px)', transition: { duration: 0.2 } }}>
                  {/* header */}
                  <div className="flex flex-wrap items-start gap-3 pb-3 border-b border-white/5">
                    <div className="flex-1 min-w-[200px]">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-base font-bold text-white font-mono">{detail.target_username}</h3>
                        <span className="text-[10px] font-mono text-slate-500">{detail.target_role} · GHOST-{String(detail.id).padStart(3, '0')}</span>
                        <AnimatePresence>
                          {detail.user_suspended && (
                            <motion.span {...swap} className="px-1.5 py-0.5 rounded border border-danger/30 bg-danger/10 text-[9px] text-danger font-mono">SUSPENDED</motion.span>
                          )}
                        </AnimatePresence>
                      </div>
                      <motion.div layout className="flex flex-wrap gap-1.5 mt-2">
                        <StatusBadge status={detail.status} />
                        <ModeBadge mode={detail.interaction_mode} muted={!isOpen} />
                        <AnimatePresence>
                          {detail.controlling_admin && isOpen && (
                            <motion.span key={detail.controlling_admin} {...swap}
                              className="text-[10px] font-mono text-warn px-2 py-0.5 rounded-md border border-warn/20">
                              controlled by {detail.controlling_admin === user?.username ? 'you' : detail.controlling_admin}
                            </motion.span>
                          )}
                        </AnimatePresence>
                      </motion.div>
                    </div>
                    <motion.div className="grid grid-cols-3 gap-2 text-center min-w-[260px]" variants={listStagger} initial="hidden" animate="show">
                      <motion.div variants={itemRise} className="rounded-xl border border-white/6 bg-bg-800/50 px-2 py-2">
                        <p className="text-[9px] font-mono uppercase text-slate-500 flex items-center justify-center gap-1"><Activity size={9} />Threat</p>
                        <p className="mt-1"><LevelBadge level={detail.threat_level} score={detail.threat_score} /></p>
                      </motion.div>
                      <motion.div variants={itemRise} className="rounded-xl border border-white/6 bg-bg-800/50 px-2 py-2">
                        <p className="text-[9px] font-mono uppercase text-slate-500 flex items-center justify-center gap-1">
                          <motion.span className="inline-flex" animate={isOpen ? { rotate: 360 } : { rotate: 0 }}
                            transition={isOpen ? { duration: 8, repeat: Infinity, ease: 'linear' } : { duration: 0.3 }}>
                            <Clock size={9} />
                          </motion.span>Duration
                        </p>
                        <p className="text-xs font-mono font-bold text-white mt-1 tabular-nums">{fmtDuration(liveDuration)}</p>
                      </motion.div>
                      <motion.div variants={itemRise} className="rounded-xl border border-white/6 bg-bg-800/50 px-2 py-2">
                        <p className="text-[9px] font-mono uppercase text-slate-500 flex items-center justify-center gap-1"><MessageSquare size={9} />Messages</p>
                        <p className="text-xs font-mono font-bold text-white mt-1"><AnimatedNumber value={detail.messages?.length ?? detail.message_count} /></p>
                      </motion.div>
                    </motion.div>
                    <div className="w-full">
                      <ThreatMeter score={detail.threat_score} level={detail.threat_level} />
                      <p className="text-[10px] font-mono text-slate-500 mt-1">
                        Category: <span className="text-slate-300">{catLabel(detail.threat_category)}</span>
                        {detail.expires_at && isOpen && <> · auto-expires {new Date(detail.expires_at).toLocaleTimeString()}</>}
                        {detail.end_reason && !isOpen && <> · {detail.end_reason}</>}
                      </p>
                    </div>
                  </div>

                  {/* controls */}
                  <motion.div layout className="flex flex-wrap gap-2" transition={{ layout: spring }}>
                    <AnimatePresence mode="popLayout" initial={false}>
                      {detail.status === 'active' && (
                        <motion.button key="pause" {...swap} {...press} onClick={() => post('pause', {}, 'Monitoring paused').catch(() => {})}
                          className="px-3 py-2 rounded-xl bg-purple-500/10 border border-purple-500/25 text-xs text-purple-400 inline-flex items-center gap-1.5"><Pause size={12} />Pause Monitoring</motion.button>
                      )}
                      {detail.status === 'paused' && (
                        <motion.button key="resume" {...swap} {...press} onClick={() => post('resume', {}, 'Monitoring resumed').catch(() => {})}
                          className="px-3 py-2 rounded-xl bg-success/10 border border-success/25 text-xs text-success inline-flex items-center gap-1.5"><Play size={12} />Resume Monitoring</motion.button>
                      )}
                      {isOpen && (
                        <motion.button key="manual" {...swap} {...press} onClick={() => switchMode('admin_manual')} disabled={detail.status === 'paused' || iControl}
                          className="px-3 py-2 rounded-xl bg-warn/10 border border-warn/25 text-xs text-warn disabled:opacity-40 inline-flex items-center gap-1.5 transition-opacity"><UserCog size={12} />Switch to Admin Control</motion.button>
                      )}
                      {isOpen && (
                        <motion.button key="persona" {...swap} {...press} onClick={() => switchMode('ai_persona')} disabled={detail.status === 'paused' || detail.interaction_mode === 'ai_persona'}
                          className="px-3 py-2 rounded-xl bg-accent/10 border border-accent/25 text-xs text-accent disabled:opacity-40 inline-flex items-center gap-1.5 transition-opacity"><Bot size={12} />Switch to AI Persona</motion.button>
                      )}
                    </AnimatePresence>
                    <div className="flex gap-1 ml-auto">
                      <motion.button {...press} onClick={() => exportReport('json')} title="Export JSON report"
                        className="px-2.5 py-2 rounded-xl border border-white/10 text-xs text-slate-300 hover:text-accent transition-colors inline-flex items-center gap-1.5"><Download size={12} /><FileJson size={12} /></motion.button>
                      <motion.button {...press} onClick={() => exportReport('csv')} title="Export CSV transcript"
                        className="px-2.5 py-2 rounded-xl border border-white/10 text-xs text-slate-300 hover:text-accent transition-colors inline-flex items-center gap-1.5"><Download size={12} /><FileSpreadsheet size={12} /></motion.button>
                    </div>
                    <AnimatePresence mode="popLayout" initial={false}>
                      {!detail.user_suspended && detail.target_active !== false && (
                        <motion.button key="suspend" {...swap} {...press} onClick={() => setDialog({
                          title: `Suspend ${detail.target_username}?`,
                          message: 'The account is disabled immediately: existing sessions stop working and sign-in is refused. Any open investigation is closed. This is recorded in the audit log and can be reversed by an administrator.',
                          confirmLabel: 'Suspend user', danger: true, withReason: true,
                          onConfirm: ({ reason }) => post('suspend-user', { confirm: true, reason }, 'User suspended'),
                        })}
                          className="px-3 py-2 rounded-xl bg-danger/10 border border-danger/25 text-xs text-danger inline-flex items-center gap-1.5"><Ban size={12} />Suspend User</motion.button>
                      )}
                      {isOpen && (
                        <motion.button key="terminate" {...swap} {...press} onClick={() => setDialog({
                          title: 'Terminate this investigation?',
                          message: `${detail.target_username} will be returned to the normal assistant. All evidence (messages, timeline) is retained for the report.`,
                          confirmLabel: 'Terminate', danger: true, withReason: true,
                          onConfirm: ({ reason }) => post('terminate', { confirm: true, reason }, 'Investigation terminated'),
                        })}
                          className="px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-xs text-slate-300 hover:text-danger hover:border-danger/30 transition-colors inline-flex items-center gap-1.5"><Square size={12} />Terminate Investigation</motion.button>
                      )}
                    </AnimatePresence>
                  </motion.div>

                  <AnimatePresence initial={false}>
                    {detail.status === 'paused' && (
                      <motion.div key="paused" {...collapse} className="overflow-hidden">
                        <div className="rounded-xl border border-purple-500/25 bg-purple-500/5 px-3 py-2 text-[11px] text-purple-300">
                          Monitoring paused: the user remains in the isolated decoy with the AI Persona and every message is still recorded, but live streaming is suspended. Resume to see new activity live.
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* conversation + timeline */}
                  <div className="grid grid-cols-1 lg:grid-cols-[1.5fr_1fr] gap-4 flex-1 min-h-0">
                    <div className="flex flex-col min-h-0">
                      <p className="text-[10px] font-mono text-slate-500 uppercase mb-2 flex items-center gap-1.5"><MessageSquare size={11} className="text-accent" />Live decoy conversation</p>
                      <div ref={chatScrollRef} className="flex-1 overflow-y-auto overflow-x-hidden space-y-2 max-h-[380px] min-h-[200px] pr-1 rounded-xl border border-white/5 bg-bg-900/30 p-3">
                        {(detail.messages || []).length === 0 && (
                          <motion.p initial={{ opacity: 0 }} animate={{ opacity: [0.4, 1, 0.4] }} transition={{ duration: 2.4, repeat: Infinity }}
                            className="text-xs text-slate-600 font-mono">Waiting for the user's next message…</motion.p>
                        )}
                        {(detail.messages || []).map(m => <ConsoleMessage key={m.id} m={m} target={detail.target_username} />)}
                        <AnimatePresence>{awaitingAdmin && <AwaitingReply key="awaiting" />}</AnimatePresence>
                      </div>
                    </div>
                    <div className="flex flex-col min-h-0">
                      <p className="text-[10px] font-mono text-slate-500 uppercase mb-2 flex items-center gap-1.5"><History size={11} className="text-accent" />Activity timeline</p>
                      <div className="flex-1 overflow-y-auto overflow-x-hidden max-h-[380px] min-h-[200px] pr-1 rounded-xl border border-white/5 bg-bg-900/30 p-3">
                        <ol className="relative ml-1 space-y-3">
                          {/* the rail draws itself in */}
                          <motion.span aria-hidden className="absolute left-0 top-0 w-px bg-white/10 origin-top"
                            initial={{ scaleY: 0 }} animate={{ scaleY: 1 }} transition={{ duration: 0.8, ease }} style={{ height: '100%' }} />
                          <AnimatePresence initial={false}>
                            {timeline.map((e, i) => (
                              <motion.li key={e.id} layout="position" className="relative ml-3"
                                initial={{ opacity: 0, x: -12 }}
                                animate={{ opacity: 1, x: 0, transition: { duration: 0.4, ease, delay: Math.min(i * 0.04, 0.4) } }}
                                exit={{ opacity: 0 }}>
                                <motion.span className={`absolute -left-[16px] top-1 w-2 h-2 rounded-full ${EVENT_DOT[e.event_type] || 'bg-white/30'}`}
                                  initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ ...spring, delay: Math.min(i * 0.04, 0.4) + 0.1 }} />
                                <p className={`text-[10px] font-mono uppercase ${EVENT_TONE[e.event_type] || 'text-slate-400'}`}>{e.event_type.replace(/_/g, ' ')}</p>
                                <p className="text-[11px] text-slate-300">{e.description}</p>
                                <p className="text-[9px] font-mono text-slate-600">{e.actor} · {fmtTime(e.created_at)}</p>
                              </motion.li>
                            ))}
                          </AnimatePresence>
                        </ol>
                      </div>
                    </div>
                  </div>

                  {/* investigation questions + manual input */}
                  <AnimatePresence initial={false}>
                    {isOpen && (
                      <motion.div key="interact" {...collapse} className="overflow-hidden">
                        <div className="border-t border-white/5 pt-3 space-y-3">
                          <div>
                            <div className="flex items-center gap-2 mb-2">
                              <p className="text-[10px] font-mono text-slate-500 uppercase">Investigation questions</p>
                              <button onClick={() => setShowQuestionEditor(v => !v)} className="text-[10px] font-mono text-accent hover:underline">
                                {showQuestionEditor ? 'done' : 'customize'}
                              </button>
                            </div>
                            <motion.div layout className="flex flex-wrap gap-1.5" variants={listStagger} initial="hidden" animate="show">
                              <AnimatePresence initial={false} mode="popLayout">
                                {questions.map(q => (
                                  <motion.span key={q.id} layout variants={itemRise} exit={{ opacity: 0, scale: 0.8, transition: { duration: 0.15 } }}
                                    whileHover={{ y: -2 }} transition={spring}
                                    className={`inline-flex items-center rounded-lg border transition-colors duration-300 ${draftQuestionId === q.id ? 'border-warn/50 bg-warn/15' : 'border-warn/20 bg-warn/5'}`}>
                                    <button onClick={() => pickQuestion(q)} className="px-2.5 py-1 text-[11px] text-warn/90 hover:text-warn">{q.text}</button>
                                    <AnimatePresence>
                                      {showQuestionEditor && !q.is_default && (
                                        <motion.button initial={{ width: 0, opacity: 0 }} animate={{ width: 'auto', opacity: 1 }} exit={{ width: 0, opacity: 0 }}
                                          onClick={() => deleteQuestion(q)} className="pr-2 text-slate-500 hover:text-danger overflow-hidden"><X size={10} /></motion.button>
                                      )}
                                    </AnimatePresence>
                                  </motion.span>
                                ))}
                              </AnimatePresence>
                            </motion.div>
                            <AnimatePresence initial={false}>
                              {showQuestionEditor && (
                                <motion.div key="editor" {...collapse} className="overflow-hidden">
                                  <div className="flex gap-2 mt-2">
                                    <input value={newQuestion} onChange={e => setNewQuestion(e.target.value)} onKeyDown={e => e.key === 'Enter' && addQuestion()} maxLength={500}
                                      placeholder="Add a custom question…"
                                      className="flex-1 px-3 py-1.5 rounded-lg bg-bg-800 border border-white/8 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-accent/40 transition-colors" />
                                    <motion.button {...press} onClick={addQuestion} className="px-2.5 rounded-lg border border-accent/25 text-accent"><Plus size={12} /></motion.button>
                                  </div>
                                </motion.div>
                              )}
                            </AnimatePresence>
                          </div>

                          <AnimatePresence mode="wait" initial={false}>
                            {iControl ? (
                              <motion.div key="manual" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.25, ease }}>
                                <p className="text-[10px] font-mono text-warn uppercase mb-2 flex items-center gap-1.5">
                                  <UserCog size={11} />Admin Manual Control — your messages appear to the user as the assistant
                                </p>
                                <div className="flex gap-2">
                                  <input ref={inputRef} value={draft} onChange={e => { setDraft(e.target.value); setDraftQuestionId(null) }}
                                    onKeyDown={e => e.key === 'Enter' && !sending && sendMessage()} maxLength={2000}
                                    placeholder="Type a reply to the user…"
                                    className="flex-1 px-3 py-2 rounded-xl bg-bg-800 border border-warn/25 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-warn/50 focus:shadow-[0_0_0_3px_rgb(var(--warn)/0.12)] transition-all duration-300" />
                                  <motion.button {...press} onClick={sendMessage} disabled={sending || !draft.trim()}
                                    className="px-4 py-2 rounded-xl bg-warn/15 border border-warn/30 text-warn text-xs font-semibold disabled:opacity-40 inline-flex items-center gap-1.5 transition-opacity">
                                    <motion.span className="inline-flex" animate={sending ? { x: [0, 14], opacity: [1, 0] } : { x: 0, opacity: 1 }}
                                      transition={sending ? { duration: 0.35, ease: 'easeIn' } : spring}>
                                      <Send size={13} />
                                    </motion.span>
                                    Send
                                  </motion.button>
                                </div>
                              </motion.div>
                            ) : (
                              <motion.div key="observe" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.25, ease }}
                                className="rounded-xl border border-white/8 bg-bg-800/40 px-3 py-2.5 flex flex-wrap items-center gap-3">
                                <motion.span className="inline-flex" animate={{ y: [0, -2, 0] }} transition={{ duration: 2.4, repeat: Infinity, ease: 'easeInOut' }}>
                                  <Bot size={14} className="text-accent" />
                                </motion.span>
                                <p className="text-[11px] text-slate-400 flex-1">
                                  {detail.interaction_mode === 'ai_persona'
                                    ? 'The AI Persona is engaging the user. Take over to send your own messages or questions.'
                                    : `${detail.controlling_admin} is currently in control.`}
                                  {draft && <span className="block text-warn/80 mt-1">Draft ready: “{draft}”</span>}
                                </p>
                                {detail.status === 'active' && (
                                  <motion.button {...press} onClick={() => switchMode('admin_manual')} className="px-3 py-1.5 rounded-lg bg-warn/10 border border-warn/25 text-[11px] text-warn">Take over</motion.button>
                                )}
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </motion.div>
      </motion.div>
    </MotionConfig>
  )
}
