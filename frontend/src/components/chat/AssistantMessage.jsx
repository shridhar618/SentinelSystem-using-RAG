import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { format } from 'date-fns'
import {
  AlertTriangle, BookOpen, Check, ChevronDown, Copy, FileSearch, Radar, Scale, ShieldX, ThumbsDown, ThumbsUp, Zap, Cpu,
} from 'lucide-react'

import { TONES, RISK_TONE, cleanRule, decisionFor, parseAnswer } from './chatConfig'

export function RiskMeter({ score = 0, level = 'low', compact = false }) {
  const tone = TONES[RISK_TONE[level] || 'success']
  const pct = Math.round(Math.max(0, Math.min(1, score || 0)) * 100)
  return (
    <div className={`flex items-center gap-2 ${compact ? '' : 'w-full'}`} title={`Risk score ${pct}/100`}>
      <div className={`${compact ? 'w-20' : 'flex-1'} h-2 rounded-full bg-bg-600 overflow-hidden`}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${Math.max(pct, 3)}%` }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
          className="h-full rounded-full"
          style={{ background: tone.grad }}
        />
      </div>
      <span className={`text-[10px] font-mono font-bold uppercase ${tone.text}`}>{level} · {pct}</span>
    </div>
  )
}

function AnswerBody({ parsed }) {
  return (
    <div className="space-y-2.5 text-[13.5px] leading-relaxed text-slate-200">
      {parsed.blocks.map((block, i) => {
        if (block.type === 'list') {
          return (
            <ul key={i} className="space-y-1.5">
              {block.items.map((item, j) => (
                <li key={j} className="flex gap-2">
                  <span className="mt-[7px] w-1.5 h-1.5 rounded-full bg-accent/70 flex-shrink-0" />
                  <span className="min-w-0">
                    {item.source && (
                      <span className="inline-flex items-center gap-1 mr-1.5 mb-0.5 px-1.5 py-0.5 rounded-md bg-accent/10 border border-accent/25 text-[10.5px] font-mono text-accent align-middle">
                        <BookOpen size={9} />{item.source}
                      </span>
                    )}
                    {item.text}
                  </span>
                </li>
              ))}
            </ul>
          )
        }
        if (block.type === 'heading') return <p key={i} className="font-semibold text-white">{block.text}</p>
        return <p key={i} className={block.muted ? 'text-slate-500 text-[12.5px]' : ''}>{block.text}</p>
      })}
    </div>
  )
}

function RestrictedCard({ msg }) {
  const rules = (msg.triggered_rules || []).map(cleanRule)
  return (
    <div className="space-y-3">
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 rounded-xl bg-danger/10 border border-danger/30 flex items-center justify-center flex-shrink-0">
          <ShieldX size={16} className="text-danger" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-danger">Request restricted by SecureAI policy</p>
          <p className="text-[12.5px] text-slate-300 mt-1 leading-relaxed">{msg.reason || msg.content}</p>
        </div>
      </div>
      {rules.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {rules.map(rule => (
            <span
              key={rule.label}
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10.5px] font-mono border ${rule.kind === 'intent' ? 'bg-danger/10 border-danger/30 text-danger' : 'bg-warn/10 border-warn/30 text-warn'}`}
            >
              {rule.kind === 'intent' ? <Radar size={9} /> : <AlertTriangle size={9} />}
              {rule.label}
            </span>
          ))}
        </div>
      )}
      {msg.recommended_action && (
        <div className="rounded-xl bg-bg-800/70 border border-white/8 px-3 py-2 text-[12px] text-slate-300">
          <span className="font-semibold text-white">What to do: </span>{msg.recommended_action}
        </div>
      )}
    </div>
  )
}

function DecisionDetails({ msg }) {
  const [open, setOpen] = useState(false)
  const rules = (msg.triggered_rules || []).map(cleanRule)
  const notes = msg.validator_notes || []
  const evidence = msg.policy_evidence || []
  const showAction = msg.recommended_action && msg.status !== 'blocked'
  const hasDetails = rules.length || notes.length || evidence.length || showAction || (msg.reason && msg.status !== 'blocked')
  if (!hasDetails) return null

  return (
    <div className="border-t border-white/5">
      <button
        onClick={() => setOpen(v => !v)}
        className="w-full flex items-center justify-between px-4 py-2 text-[11px] font-mono text-slate-500 hover:text-slate-300"
        aria-expanded={open}
      >
        <span className="flex items-center gap-1.5"><Scale size={11} className="text-accent" />Why this decision?</span>
        <ChevronDown size={12} className={`transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
            <div className="px-4 pb-4 space-y-3 text-[11.5px]">
              <div>
                <p className="text-[10px] uppercase tracking-wider font-mono text-slate-500 mb-1.5">Risk score</p>
                <RiskMeter score={msg.risk_score} level={msg.risk_level} />
              </div>
              {msg.reason && msg.status !== 'blocked' && (
                <p className="px-3 py-2 rounded-lg bg-warn/8 border border-warn/15 text-warn">{msg.reason}</p>
              )}
              {rules.length > 0 && (
                <div>
                  <p className="text-[10px] uppercase tracking-wider font-mono text-slate-500 mb-1.5">Triggered rules</p>
                  <div className="flex flex-wrap gap-1.5">
                    {rules.map(rule => (
                      <span key={rule.label} className="px-2 py-0.5 rounded-md bg-white/5 border border-white/10 font-mono text-[10.5px] text-slate-300">
                        {rule.kind === 'intent' ? 'intent · ' : ''}{rule.label}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {notes.length > 0 && (
                <div>
                  <p className="text-[10px] uppercase tracking-wider font-mono text-slate-500 mb-1.5">Signals</p>
                  <ul className="space-y-1">
                    {notes.map(note => (
                      <li key={note} className="flex gap-1.5 text-slate-400"><Radar size={11} className="mt-0.5 flex-shrink-0 text-warn" />{note}</li>
                    ))}
                  </ul>
                </div>
              )}
              {evidence.length > 0 && (
                <div>
                  <p className="text-[10px] uppercase tracking-wider font-mono text-slate-500 mb-1.5">Policy evidence</p>
                  <ul className="space-y-1">
                    {evidence.map(citation => (
                      <li key={citation} className="flex gap-1.5 text-slate-300"><BookOpen size={11} className="mt-0.5 flex-shrink-0 text-accent" />{citation}</li>
                    ))}
                  </ul>
                </div>
              )}
              {showAction && (
                <p className="px-3 py-2 rounded-lg bg-accent/8 border border-accent/15 text-slate-300">
                  <span className="font-semibold text-white">Recommended: </span>{msg.recommended_action}
                </p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default function AssistantMessage({ msg, onFeedback }) {
  const [copied, setCopied] = useState(false)
  const decision = decisionFor(msg)
  const tone = TONES[decision.tone]
  const DecisionIcon = decision.icon
  const parsed = parseAnswer(msg.content)
  const blocked = msg.status === 'blocked'
  const isWelcome = msg.id === 'welcome'

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(parsed.blocks.length ? msg.content.replace(/^\[Offline policy mode[^\]]*\]\n?/, '') : msg.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      // clipboard unavailable (insecure context); ignore
    }
  }

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }} className="flex gap-3 mb-5">
      <div className="w-8 h-8 rounded-xl chat-badge flex items-center justify-center flex-shrink-0 mt-0.5">
        <Cpu size={14} />
      </div>
      <div className="min-w-0 flex-1 max-w-3xl">
        {msg.is_high_risk && (
          <div className="inline-flex items-center gap-1.5 mb-1.5 px-2.5 py-1 rounded-full bg-danger/10 border border-danger/30 text-danger text-[10px] font-mono font-bold">
            <Zap size={9} />HIGH-RISK EVENT · LOGGED FOR REVIEW
          </div>
        )}
        <div className={`rounded-2xl rounded-tl-md border overflow-hidden ${isWelcome ? '' : `border-l-[3px] ${tone.edge}`} ${blocked ? 'bg-danger/5 border-danger/30' : 'bg-bg-800/90 border-white/8'} shadow-card`}>
          {!isWelcome && (
            <div className={`flex flex-wrap items-center justify-between gap-2 px-4 py-2 border-b border-white/5 ${tone.head}`}>
              <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10.5px] font-mono font-bold border ${tone.bg} ${tone.border} ${tone.text}`}>
                <DecisionIcon size={11} />{decision.label}
              </span>
              <div className="flex items-center gap-2">
                {parsed.offline && (
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded border border-white/10 text-slate-500" title="No LLM configured: answer composed from policy excerpts and role-scoped sample data">
                    offline mode
                  </span>
                )}
                {msg.status !== 'error' && <RiskMeter score={msg.risk_score} level={msg.risk_level} compact />}
              </div>
            </div>
          )}

          <div className="px-4 py-3.5">
            {parsed.caution && !blocked && (
              <div className="flex gap-2 mb-3 px-3 py-2 rounded-lg bg-warn/10 border border-warn/20 text-[12px] text-warn">
                <AlertTriangle size={13} className="mt-0.5 flex-shrink-0" />{parsed.caution}
              </div>
            )}
            {blocked ? <RestrictedCard msg={msg} /> : <AnswerBody parsed={parsed} />}
          </div>

          {msg.sources?.length > 0 && !blocked && (
            <div className="px-4 pb-3 flex flex-wrap gap-1.5">
              {msg.sources.map((source, index) => (
                <span key={`${source.document_name}-${index}`} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-[10.5px] text-slate-400 max-w-full">
                  <FileSearch size={10} className="flex-shrink-0 text-accent" />
                  <span className="truncate">{source.document_name}{source.section ? ` · ${source.section}` : ''}{source.page ? ` · p.${source.page}` : ''}</span>
                </span>
              ))}
            </div>
          )}

          {!isWelcome && <DecisionDetails msg={msg} />}
        </div>

        <div className="flex items-center gap-1 mt-1.5 px-1">
          <span className="text-[10px] text-slate-600 font-mono mr-1">{format(new Date(msg.timestamp), 'HH:mm')}</span>
          {!isWelcome && msg.status !== 'error' && (
            <button onClick={copy} className="p-1 rounded-md text-slate-600 hover:text-slate-300 hover:bg-white/5" title="Copy answer" aria-label="Copy answer">
              {copied ? <Check size={12} className="text-success" /> : <Copy size={12} />}
            </button>
          )}
          {msg.log_id && (
            <>
              <button
                onClick={() => onFeedback(msg.log_id, 'helpful')}
                className={`p-1 rounded-md hover:bg-white/5 ${msg.feedback === 'helpful' ? 'text-success' : 'text-slate-600 hover:text-success'}`}
                title="Helpful" aria-label="Mark helpful"
              >
                <ThumbsUp size={12} />
              </button>
              <button
                onClick={() => onFeedback(msg.log_id, 'unhelpful')}
                className={`p-1 rounded-md hover:bg-white/5 ${msg.feedback === 'unhelpful' ? 'text-danger' : 'text-slate-600 hover:text-danger'}`}
                title="Not helpful" aria-label="Mark not helpful"
              >
                <ThumbsDown size={12} />
              </button>
            </>
          )}
        </div>
      </div>
    </motion.div>
  )
}
