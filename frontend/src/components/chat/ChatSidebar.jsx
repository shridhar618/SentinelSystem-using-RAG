import { Check, Lock, Activity, Workflow, Database, Cpu } from 'lucide-react'

import { DATA_SCOPES, TONES, RISK_TONE, hasScope } from './chatConfig'

function Card({ title, icon: Icon, children, right, iconClass = 'text-accent' }) {
  return (
    <section className="rounded-2xl bg-bg-800/80 border border-white/8 p-4 shadow-card">
      <div className="flex items-center justify-between mb-3">
        <h3 className="flex items-center gap-2 text-[11px] font-mono uppercase tracking-wider text-slate-500" style={{ fontFamily: 'inherit', letterSpacing: '0.08em' }}>
          <span className={`w-6 h-6 rounded-lg flex items-center justify-center ${iconClass}`} style={{ backgroundColor: 'color-mix(in srgb, currentColor 15%, transparent)' }}><Icon size={12} /></span>{title}
        </h3>
        {right}
      </div>
      {children}
    </section>
  )
}

function Stat({ label, value, tone }) {
  return (
    <div className={`rounded-xl border px-2.5 py-2 ${tone ? `${TONES[tone].bg} border-white/5` : 'bg-bg-700/60 border-white/5'}`}>
      <p className={`text-xl font-extrabold leading-none ${tone ? TONES[tone].text : 'text-white'}`}>{value}</p>
      <p className="text-[10px] text-slate-500 mt-1">{label}</p>
    </div>
  )
}

function RiskHistory({ scored }) {
  if (!scored.length) {
    return <p className="text-[11px] text-slate-500">No questions yet. Each answer's risk score will appear here.</p>
  }
  const recent = scored.slice(-24)
  return (
    <div>
      <div className="flex items-end gap-1 h-14" role="img" aria-label={`Risk scores of the last ${recent.length} answers`}>
        {recent.map(m => (
          <div
            key={m.id}
            title={`${Math.round((m.risk_score || 0) * 100)}/100 · ${m.risk_level}`}
            className="flex-1 min-w-[4px] max-w-[14px] rounded-t-sm"
            style={{
              height: `${Math.max(8, (m.risk_score || 0) * 100)}%`,
              background: TONES[RISK_TONE[m.risk_level] || 'success'].grad,
              opacity: 0.9,
            }}
          />
        ))}
      </div>
      <div className="flex justify-between mt-1 text-[9.5px] font-mono text-slate-600">
        <span>older</span><span>latest</span>
      </div>
    </div>
  )
}

const PIPELINE = [
  ['RBAC', 'Your role decides which data classes can be returned.'],
  ['Rules + intent', 'Keyword rules and intent analysis score every request.'],
  ['Policy evidence', 'Decisions cite the policy clause behind them.'],
  ['Audit', 'Every request is logged; humans decide consequences.'],
]

export default function ChatSidebar({ roleMeta, permissions, messages, status }) {
  const answers = messages.filter(m => m.role === 'assistant' && m.id !== 'welcome' && m.status && m.status !== 'error')
  const counts = {
    allowed: answers.filter(m => m.status === 'allowed').length,
    limited: answers.filter(m => m.status === 'filtered').length,
    blocked: answers.filter(m => m.status === 'blocked').length,
  }
  const peak = answers.reduce((max, m) => Math.max(max, m.risk_score || 0), 0)
  const llmOk = !!status?.llm?.configured
  const ragOk = !!status?.rag?.ready

  return (
    <div className="space-y-3">
      <Card title="Your access" icon={Lock}>
        <div className="flex items-center gap-2 mb-3">
          <span className={`px-2 py-0.5 rounded-md text-[10.5px] font-mono font-bold border border-white/10 bg-white/5 ${roleMeta.color}`}>{roleMeta.badge}</span>
          <span className="text-[11px] text-slate-500 truncate">{roleMeta.desc}</span>
        </div>
        <ul className="space-y-1.5">
          {DATA_SCOPES.map(scope => {
            const ok = hasScope(permissions, scope)
            const Icon = scope.icon
            return (
              <li key={scope.perm} className={`flex items-center gap-2.5 text-[12px] ${ok ? 'text-slate-200' : 'text-slate-500'}`}>
                <span className={`w-6 h-6 rounded-lg flex items-center justify-center ${ok ? 'bg-accent/10 text-accent' : 'bg-white/5 text-slate-600'}`}><Icon size={12} /></span>
                <span className="flex-1">{scope.label}</span>
                {ok
                  ? <Check size={13} className="text-success" aria-label="allowed" />
                  : <Lock size={12} className="text-slate-600" aria-label="not permitted" />}
              </li>
            )
          })}
        </ul>
      </Card>

      <Card title="Session risk" icon={Activity} right={<span className="text-[10px] font-mono text-slate-500">peak {Math.round(peak * 100)}</span>}>
        <div className="grid grid-cols-3 gap-2 mb-3">
          <Stat label="Allowed" value={counts.allowed} tone="success" />
          <Stat label="Limited" value={counts.limited} tone="warn" />
          <Stat label="Blocked" value={counts.blocked} tone="danger" />
        </div>
        <RiskHistory scored={answers} />
      </Card>

      <Card title="How decisions are made" icon={Workflow}>
        <ol className="space-y-2">
          {PIPELINE.map(([name, text], i) => (
            <li key={name} className="flex gap-2.5">
              <span className={`w-5 h-5 rounded-full text-[10px] font-mono font-bold flex items-center justify-center flex-shrink-0 border bg-accent/10 border-accent/30 text-accent`}>{i + 1}</span>
              <p className="text-[11.5px] text-slate-400 leading-snug"><span className="text-slate-200 font-semibold">{name}.</span> {text}</p>
            </li>
          ))}
        </ol>
      </Card>

      <Card title="Assistant" icon={Cpu}>
        <ul className="space-y-1.5 text-[12px]">
          <li className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${ragOk ? 'bg-success' : 'bg-warn'}`} />
            <Database size={12} className="text-slate-500" />
            <span className="text-slate-300 flex-1">Policy search</span>
            <span className="text-[10.5px] font-mono text-slate-500">{ragOk ? 'semantic' : 'keyword'}</span>
          </li>
          <li className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${llmOk ? 'bg-success' : 'bg-warn'}`} />
            <Cpu size={12} className="text-slate-500" />
            <span className="text-slate-300 flex-1">Language model</span>
            <span className="text-[10.5px] font-mono text-slate-500">{llmOk ? status.llm.provider : 'not configured'}</span>
          </li>
        </ul>
        {!llmOk && (
          <p className="mt-3 text-[11px] text-slate-500 leading-snug">
            Offline policy mode: answers are policy excerpts and role-scoped sample data. Set <code className="font-mono text-slate-400">AI_PROVIDER</code> in <code className="font-mono text-slate-400">backend/.env</code> for written answers.
          </p>
        )}
      </Card>
    </div>
  )
}
