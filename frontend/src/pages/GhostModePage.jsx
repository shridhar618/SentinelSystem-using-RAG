import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence, MotionConfig } from 'framer-motion'
import { ease, fadeIn } from '../utils/motion'
import { Ghost, Shield, Radar, Eye, Sparkles } from 'lucide-react'
import GhostChat from '../components/GhostChat'
import GhostAdminPanel from '../components/GhostAdminPanel'

export default function GhostModePage() {
  const [view, setView] = useState('admin')   // 'admin' | 'user'
  // Deep links from alert notifications: /ghost-mode?alert=ID or ?investigation=ID
  const [params] = useSearchParams()
  const focusAlertId = params.get('alert') ? Number(params.get('alert')) : null
  const focusInvestigationId = params.get('investigation') ? Number(params.get('investigation')) : null
  useEffect(() => {
    if (focusAlertId || focusInvestigationId) setView('admin')
  }, [focusAlertId, focusInvestigationId])

  return (
    <MotionConfig reducedMotion="user">
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="h-full overflow-y-auto">
      <div className="px-6 py-8 md:px-8 md:py-10 space-y-6">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-accent/20 bg-accent/10 text-[10px] font-mono uppercase tracking-[0.28em] text-accent">
              <Radar size={12} />
              Active deception layer
            </div>
            <h1 className="text-2xl md:text-3xl font-bold text-white mt-4">Ghost Mode</h1>
            <p className="text-[10px] text-slate-500 font-mono uppercase tracking-widest mt-2">
              AI Honeypot · Trap & Track Malicious Users
            </p>
            <p className="max-w-2xl text-sm text-slate-400 mt-3 leading-relaxed">
              Detect threats in the AI chatbot, escalate suspicious users into an isolated decoy, and investigate live with an AI Persona or direct admin control. The original honeypot sessions and decoy preview remain available.
            </p>
          </div>
          <motion.div {...fadeIn(0.15, { duration: 0.8 })} className="flex flex-wrap gap-1 p-1 rounded-2xl border border-white/8 bg-bg-800/60">
            {[
              { key: 'admin', label: 'Admin View', icon: Shield, on: 'text-accent', pill: 'bg-accent/10 border-accent/20' },
              { key: 'user', label: 'Honeypot Interface', icon: Ghost, on: 'text-danger', pill: 'bg-danger/10 border-danger/20' },
            ].map(({ key, label, icon: Icon, on, pill }) => (
              <motion.button
                key={key}
                onClick={() => setView(key)}
                whileTap={{ scale: 0.96 }}
                className={`relative flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-mono transition-colors duration-300 ${view === key ? on : 'text-slate-400 hover:text-slate-200'}`}
              >
                {view === key && (
                  <motion.span layoutId="ghost-view-pill" transition={{ type: 'spring', stiffness: 420, damping: 34 }}
                    className={`absolute inset-0 rounded-xl border ${pill}`} />
                )}
                <Icon size={12} className="relative" /><span className="relative">{label}</span>
              </motion.button>
            ))}
          </motion.div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[1.35fr_0.9fr] gap-4">
          <div className="glass rounded-3xl border border-white/5 p-5 md:p-6">
            <div className="flex items-start gap-4">
              <div className={`w-12 h-12 rounded-2xl flex items-center justify-center border ${
                view === 'admin'
                  ? 'bg-accent/10 border-accent/20 text-accent'
                  : 'bg-danger/10 border-danger/20 text-danger'
              }`}>
                <AnimatePresence mode="wait" initial={false}>
                  <motion.span key={view} className="inline-flex" initial={{ rotate: -90, scale: 0.5, opacity: 0 }} animate={{ rotate: 0, scale: 1, opacity: 1 }} exit={{ rotate: 90, scale: 0.5, opacity: 0 }} transition={{ duration: 0.3, ease }}>
                    {view === 'admin' ? <Shield size={20} /> : <Ghost size={20} />}
                  </motion.span>
                </AnimatePresence>
              </div>
              <div className="flex-1">
                <p className="text-xs font-mono uppercase tracking-[0.24em] text-slate-500">
                  {view === 'admin' ? 'Operator console' : 'Target-facing shell'}
                </p>
                <h2 className="text-lg font-semibold text-white mt-2">
                  {view === 'admin' ? 'Detect, investigate, intervene, and act.' : 'Preview the decoy conversation flow.'}
                </h2>
                <p className="text-sm text-slate-400 mt-2 leading-relaxed">
                  {view === 'admin'
                    ? 'Threat alerts stream in as they happen. Activate Interactive Ghost Mode on a suspect to divert their chatbot traffic into a sealed decoy, then let the AI Persona engage or take manual control yourself.'
                    : 'Test the bait experience from the user side with the same minimal shell, misleading assistant framing, and trap escalation behavior.'}
                </p>
              </div>
            </div>
          </div>

          <div className="glass rounded-3xl border border-white/5 p-5 md:p-6">
            <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-1 gap-3">
              {[
                {
                  icon: Eye,
                  label: 'Live visibility',
                  value: 'Realtime',
                  tone: 'text-accent',
                },
                {
                  icon: Sparkles,
                  label: 'Ghost responses',
                  value: view === 'admin' ? 'AI Persona + Admin' : 'Decoy UI',
                  tone: 'text-warn',
                },
                {
                  icon: Radar,
                  label: 'Threat scoring',
                  value: 'Low → Critical (0–100)',
                  tone: 'text-danger',
                },
              ].map(({ icon: Icon, label, value, tone }) => (
                <div key={label} className="rounded-2xl border border-white/6 bg-bg-800/50 p-4">
                  <div className="flex items-center gap-2">
                    <Icon size={14} className={tone} />
                    <p className="text-[10px] font-mono uppercase tracking-widest text-slate-500">{label}</p>
                  </div>
                  <p className={`text-sm font-semibold mt-2 ${tone}`}>{value}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        <AnimatePresence mode="wait" initial={false}>
        <motion.div
          key={view}
          initial={{ opacity: 0, y: 18, filter: 'blur(6px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)', transition: { duration: 0.5, ease } }}
          exit={{ opacity: 0, y: -10, filter: 'blur(4px)', transition: { duration: 0.22 } }}
        >
        {view === 'admin' && <GhostAdminPanel focusAlertId={focusAlertId} focusInvestigationId={focusInvestigationId} />}
        {view === 'user' && (
          <div className="grid grid-cols-1 xl:grid-cols-[0.9fr_1.15fr] gap-6 items-start">
            <div className="glass rounded-3xl border border-white/5 p-5 md:p-6">
              <p className="text-[10px] font-mono text-danger/60 uppercase tracking-widest">
                Demo preview
              </p>
              <h2 className="text-xl font-semibold text-white mt-3">What the target user sees</h2>
              <p className="text-sm text-slate-400 mt-3 leading-relaxed">
                The honeypot should feel believable but not flashy. This panel now keeps the interface closer to the main product style while still looking like a slightly unsafe, unrestricted chat tool.
              </p>
              <div className="mt-5 space-y-3">
                {[
                  'Compact chat shell with persistent risk signal',
                  'More balanced spacing so the screen does not feel empty',
                  'Same visual language as the rest of the platform',
                ].map(item => (
                  <div key={item} className="flex items-center gap-3 rounded-2xl border border-white/6 bg-bg-800/45 px-4 py-3">
                    <div className="w-2 h-2 rounded-full bg-danger" />
                    <p className="text-sm text-slate-300">{item}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="max-w-3xl">
              <GhostChat username="demo_target" />
            </div>
          </div>
        )}
        </motion.div>
        </AnimatePresence>
      </div>
    </motion.div>
    </MotionConfig>
  )
}
