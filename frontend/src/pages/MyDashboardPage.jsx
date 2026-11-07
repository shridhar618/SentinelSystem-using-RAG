import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { format } from 'date-fns'
import {
  Cpu, ShieldCheck, ShieldAlert, AlertTriangle, Briefcase, ScanFace,
  MessageSquare, CheckCircle2, TrendingUp, Lock,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import api from '../utils/api'

const RISK_STYLE = {
  LOW: { color: 'text-success', bg: 'bg-success/10 border-success/20', bar: '#4f9a6a' },
  MEDIUM: { color: 'text-warn', bg: 'bg-warn/10 border-warn/20', bar: '#c9922e' },
  HIGH: { color: 'text-danger', bg: 'bg-danger/10 border-danger/20', bar: '#c4553f' },
}

const DECISION_STYLE = {
  ALLOWED: 'text-success bg-success/10 border-success/20',
  WARNING: 'text-warn bg-warn/10 border-warn/20',
  RESTRICTED: 'text-danger bg-danger/10 border-danger/20',
}

function Stat({ icon: Icon, label, value, sub, to }) {
  const body = (
    <div className="glass rounded-2xl p-4 border border-white/5 h-full hover:border-white/10 transition-colors">
      <div className="flex items-center gap-2 mb-2 text-slate-500">
        <Icon size={14} />
        <span className="text-[11px] font-semibold uppercase tracking-wider">{label}</span>
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
      {sub && <p className="text-[11px] text-slate-500 mt-0.5">{sub}</p>}
    </div>
  )
  return to ? <Link to={to}>{body}</Link> : body
}

export default function MyDashboardPage() {
  const { user, hasPermission } = useAuth()
  const [data, setData] = useState(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    api.get('/me/summary').then(r => setData(r.data)).catch(() => setError(true))
  }, [])

  if (error) return <div className="h-full flex items-center justify-center text-xs text-danger">Couldn't load your dashboard.</div>
  if (!data) return <div className="h-full flex items-center justify-center text-xs text-slate-500">Loading your dashboard...</div>

  const risk = RISK_STYLE[data.risk.level]
  const canUseAI = hasPermission('use_ai_assistant')

  return (
    <div className="h-full overflow-y-auto p-6 space-y-5">
      <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-xl font-bold text-white">Welcome back, {user?.username}</h1>
        <p className="text-xs text-slate-500 mt-0.5">Your AI usage, governance status, and work at a glance</p>
      </motion.div>

      {data.access.restricted && (
        <div className="rounded-xl border border-danger/30 bg-danger/10 px-4 py-3 flex items-start gap-3">
          <Lock size={16} className="text-danger mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-danger">AI assistant access is temporarily restricted</p>
            <p className="text-xs text-slate-400 mt-0.5">
              An administrator is reviewing your activity (case {data.access.case_code}). You'll regain access once the review is complete.
            </p>
          </div>
        </div>
      )}
      {!data.access.restricted && data.access.under_review && (
        <div className="rounded-xl border border-warn/30 bg-warn/10 px-4 py-3 flex items-start gap-3">
          <AlertTriangle size={16} className="text-warn mt-0.5 flex-shrink-0" />
          <p className="text-xs text-slate-300">An administrator is reviewing your recent AI activity. No action is needed from you.</p>
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Stat icon={Cpu} label="AI Requests" value={data.ai_usage.total_requests} sub={`${data.ai_usage.last_7_days} in the last 7 days`} to={canUseAI ? '/chat' : undefined} />
        <Stat icon={AlertTriangle} label="Warnings" value={data.ai_usage.warnings} sub="Responses with sensitive data masked" />
        <Stat icon={ShieldAlert} label="Restricted" value={data.ai_usage.restricted_requests} sub="Requests outside your role's access" />
        <Stat icon={MessageSquare} label="Unread Messages" value={data.messages.unread} to="/messages" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="glass rounded-2xl p-5 border border-white/5">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-bold text-white flex items-center gap-1.5"><TrendingUp size={13} /> My Risk Level</p>
            <span className={`px-2 py-0.5 rounded border text-[10px] font-mono font-bold ${risk.bg} ${risk.color}`}>{data.risk.level}</span>
          </div>
          <div className="h-1.5 rounded-full bg-bg-600 overflow-hidden mb-3">
            <div className="h-full rounded-full transition-all" style={{ width: `${data.risk.progress * 100}%`, background: risk.bar }} />
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">{data.risk.explanation}</p>
        </div>

        <div className="glass rounded-2xl p-5 border border-white/5">
          <p className="text-xs font-bold text-white mb-3 flex items-center gap-1.5"><Briefcase size={13} /> My Tasks</p>
          <div className="grid grid-cols-2 gap-2 text-center">
            {[['Assigned', data.tasks.assigned], ['Completed', data.tasks.completed], ['Pending', data.tasks.pending], ['Overdue', data.tasks.overdue]].map(([label, value]) => (
              <div key={label} className="rounded-lg bg-white/[0.03] py-2">
                <p className={`text-lg font-bold ${label === 'Overdue' && value > 0 ? 'text-danger' : 'text-white'}`}>{value}</p>
                <p className="text-[10px] text-slate-500 uppercase">{label}</p>
              </div>
            ))}
          </div>
          <Link to="/my-work" className="block text-[11px] text-accent mt-3 hover:text-accent/70">Open my work →</Link>
        </div>

        <div className="glass rounded-2xl p-5 border border-white/5">
          <p className="text-xs font-bold text-white mb-3 flex items-center gap-1.5"><ScanFace size={13} /> Attendance Today</p>
          {data.attendance.today_status ? (
            <div className="flex items-center gap-2">
              <CheckCircle2 size={18} className="text-success" />
              <div>
                <p className="text-sm text-white capitalize">{data.attendance.today_status.replace('_', ' ')}</p>
                <p className="text-[11px] text-slate-500">{data.attendance.last_event_at ? format(new Date(data.attendance.last_event_at), 'HH:mm') : ''}</p>
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-500">No check-in recorded today.</p>
          )}
          <Link to="/attendance" className="block text-[11px] text-accent mt-3 hover:text-accent/70">Go to attendance →</Link>
        </div>
      </div>

      <div className="glass rounded-2xl border border-white/5 overflow-hidden">
        <div className="px-5 py-3 border-b border-white/5 flex items-center gap-1.5">
          <ShieldCheck size={13} className="text-accent" />
          <p className="text-xs font-bold text-white">Recent Governance Decisions</p>
        </div>
        {data.recent_decisions.length === 0 ? (
          <p className="text-xs text-slate-500 px-5 py-6">No AI requests yet.</p>
        ) : (
          <div className="divide-y divide-white/5">
            {data.recent_decisions.map(d => (
              <div key={d.id} className="px-5 py-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-xs text-slate-300 truncate">{d.request}</p>
                  <span className={`flex-shrink-0 px-2 py-0.5 rounded border text-[10px] font-mono font-bold ${DECISION_STYLE[d.decision] || ''}`}>{d.decision}</span>
                </div>
                {d.decision !== 'ALLOWED' && d.recommended_action && (
                  <p className="text-[11px] text-slate-500 mt-1">{d.recommended_action}</p>
                )}
                <p className="text-[10px] text-slate-600 font-mono mt-1">{d.timestamp ? format(new Date(d.timestamp), 'MMM d, HH:mm') : ''}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
