import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { format } from 'date-fns'
import {
  Send, Trash2, Bot, User, Lock, ShieldAlert, ShieldCheck, Shield, Cpu,
  AlertTriangle, Zap, ChevronDown, ChevronUp, Info, BookOpen,
  Download, ThumbsUp, ThumbsDown,
} from 'lucide-react'

import { useAuth } from '../context/AuthContext'
import api from '../utils/api'
import { getRoleMeta } from '../utils/roles'

const STATUS_CONFIG = {
  allowed: { icon: ShieldCheck, color: 'text-success', bg: 'bg-success/10 border-success/20', label: 'Allowed' },
  filtered: { icon: Shield, color: 'text-warn', bg: 'bg-warn/10 border-warn/20', label: 'Filtered' },
  blocked: { icon: Lock, color: 'text-danger', bg: 'bg-danger/10 border-danger/20', label: 'Blocked' },
}

const RISK_CONFIG = {
  low: { color: 'text-success', bg: 'bg-success/10 border-success/20', bar: '#06d6a0' },
  medium: { color: 'text-warn', bg: 'bg-warn/10 border-warn/20', bar: '#ffb703' },
  high: { color: 'text-danger', bg: 'bg-danger/10 border-danger/20', bar: '#ff4d6d' },
}

function TypingIndicator() {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 8 }} className="flex items-end gap-3 mb-4">
      <div className="w-8 h-8 rounded-xl bg-accent/10 border border-accent/20 flex items-center justify-center flex-shrink-0">
        <Bot size={14} className="text-accent" />
      </div>
      <div className="glass-light rounded-2xl rounded-bl-sm px-4 py-3">
        <div className="flex gap-1.5 items-center h-4">
          {[0, 1, 2].map(i => <div key={i} className="typing-dot" style={{ animationDelay: `${i * 0.2}s` }} />)}
        </div>
      </div>
    </motion.div>
  )
}

function GovernancePanel({ msg }) {
  const [open, setOpen] = useState(false)
  const riskCfg = RISK_CONFIG[msg.risk_level] || RISK_CONFIG.low
  const hasDetails = msg.reason || msg.triggered_rules?.length || msg.validator_notes?.length || msg.policy_evidence?.length
  if (!hasDetails && msg.risk_level === 'low' && msg.status === 'allowed') return null

  return (
    <motion.div initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} className="mt-2 ml-11">
      <button onClick={() => setOpen(v => !v)} className="flex items-center gap-1.5 text-[10px] font-mono text-slate-600 hover:text-slate-400">
        <Info size={9} />Governance details{open ? <ChevronUp size={9} /> : <ChevronDown size={9} />}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
            <div className="mt-2 glass-light rounded-xl p-3 space-y-2 border border-white/6 text-[11px] font-mono">
              <div className="flex items-center gap-2">
                <span className="text-slate-500 w-20 flex-shrink-0">Risk score</span>
                <div className="flex-1 h-1.5 rounded-full bg-bg-600 overflow-hidden">
                  <motion.div initial={{ width: 0 }} animate={{ width: `${(msg.risk_score || 0) * 100}%` }} transition={{ duration: 0.6 }} className="h-full rounded-full" style={{ background: riskCfg.bar }} />
                </div>
                <span className={`font-bold uppercase px-1.5 py-0.5 rounded border text-[9px] ${riskCfg.bg} ${riskCfg.color}`}>{msg.risk_level || 'low'}</span>
              </div>
              {msg.reason && <div className="px-2.5 py-2 rounded-lg bg-warn/8 border border-warn/15 text-warn/80">{msg.reason}</div>}
              {msg.recommended_action && (
                <div>
                  <p className="text-slate-500 mb-1">Recommended action:</p>
                  <div className="px-2.5 py-2 rounded-lg bg-accent/8 border border-accent/15 text-accent/80">{msg.recommended_action}</div>
                </div>
              )}
              {msg.policy_evidence?.length > 0 && (
                <div>
                  <p className="text-slate-500 mb-1">Policy evidence:</p>
                  {msg.policy_evidence.map(citation => (
                    <div key={citation} className="flex items-center gap-1.5 text-slate-300 py-0.5">
                      <BookOpen size={9} className="text-accent/60 flex-shrink-0" />{citation}
                    </div>
                  ))}
                </div>
              )}
              {msg.triggered_rules?.length > 0 && (
                <div>
                  <p className="text-slate-500 mb-1">Triggered rules:</p>
                  {msg.triggered_rules.map(rule => <div key={rule} className="text-danger/70 py-0.5">{rule}</div>)}
                </div>
              )}
              {msg.validator_notes?.length > 0 && (
                <div>
                  <p className="text-slate-500 mb-1">Layer-2 validator signals:</p>
                  {msg.validator_notes.map(note => <div key={note} className="text-warn/70 py-0.5">{note}</div>)}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

function FeedbackBar({ msg, onFeedback }) {
  if (msg.role !== 'assistant' || !msg.log_id) return null
  return (
    <div className="mt-2 ml-11 flex flex-wrap gap-2">
      <button
        onClick={() => onFeedback(msg.log_id, 'helpful')}
        className={`px-2.5 py-1 rounded-lg text-[10px] font-mono border ${msg.feedback === 'helpful' ? 'bg-success/10 border-success/20 text-success' : 'bg-white/5 border-white/8 text-slate-400 hover:text-success'}`}
      >
        <ThumbsUp size={10} className="inline mr-1" />Helpful
      </button>
      <button
        onClick={() => onFeedback(msg.log_id, 'unhelpful')}
        className={`px-2.5 py-1 rounded-lg text-[10px] font-mono border ${msg.feedback === 'unhelpful' ? 'bg-danger/10 border-danger/20 text-danger' : 'bg-white/5 border-white/8 text-slate-400 hover:text-danger'}`}
      >
        <ThumbsDown size={10} className="inline mr-1" />Not Helpful
      </button>
    </div>
  )
}

function ChatBubble({ msg, onFeedback }) {
  const isUser = msg.role === 'user'
  const statusCfg = msg.status ? STATUS_CONFIG[msg.status] : null
  const riskCfg = RISK_CONFIG[msg.risk_level] || RISK_CONFIG.low
  const StatusIcon = statusCfg?.icon

  return (
    <>
      <motion.div initial={{ opacity: 0, y: 12, scale: 0.97 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ duration: 0.3 }} className={`flex items-end gap-3 mb-2 ${isUser ? 'flex-row-reverse' : ''}`}>
        <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${isUser ? 'bg-accent/20 border border-accent/30' : 'bg-bg-600 border border-white/8'}`}>
          {isUser ? <User size={13} className="text-accent" /> : <Bot size={13} className="text-slate-400" />}
        </div>
        <div className={`flex flex-col gap-1.5 max-w-[75%] ${isUser ? 'items-end' : 'items-start'}`}>
          {!isUser && msg.is_high_risk && (
            <motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-danger/15 border border-danger/25 text-[10px] font-mono text-danger font-bold self-start">
              <Zap size={9} />HIGH RISK EVENT FLAGGED
            </motion.div>
          )}
          <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${isUser ? 'bg-accent text-bg-900 font-medium rounded-br-sm' : msg.status === 'blocked' ? 'bg-danger/10 border border-danger/20 text-danger/90 rounded-bl-sm' : msg.status === 'filtered' ? 'bg-warn/5 border border-warn/15 text-slate-200 rounded-bl-sm' : 'glass-light text-slate-200 rounded-bl-sm'}`}>
            {msg.content}
          </div>
          {!isUser && msg.sources?.length > 0 && (
            <div className="ml-1 mt-1 space-y-1">
              <p className="text-[10px] font-mono uppercase tracking-wider text-slate-500">Policy sources</p>
              {msg.sources.map((source, index) => (
                <div key={`${source.document_name}-${index}`} className="flex items-center gap-1.5 text-[11px] text-slate-400">
                  <BookOpen size={10} className="text-accent/70" />
                  <span>{source.document_name}{source.section ? ` · ${source.section}` : ''}{source.page ? ` · p. ${source.page}` : ''}</span>
                </div>
              ))}
            </div>
          )}
          <div className={`flex items-center gap-2 flex-wrap px-1 ${isUser ? 'flex-row-reverse' : ''}`}>
            <span className="text-[10px] text-slate-600 font-mono">{format(new Date(msg.timestamp), 'HH:mm')}</span>
            {statusCfg && !isUser && (
              <span className={`flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded border ${statusCfg.bg} ${statusCfg.color}`}>
                <StatusIcon size={9} />{statusCfg.label}
              </span>
            )}
            {!isUser && msg.risk_level && (
              <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border font-bold uppercase ${riskCfg.bg} ${riskCfg.color}`}>{msg.risk_level}</span>
            )}
          </div>
        </div>
      </motion.div>
      {!isUser && msg.status === 'blocked' && msg.reason && (
        <motion.div initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} className="mt-2 ml-11">
          <div className="rounded-xl border border-danger/25 bg-danger/10 p-3 text-[11px] font-mono text-danger/90 space-y-2">
            <div className="flex items-center gap-2 font-bold uppercase tracking-wide">
              <AlertTriangle size={12} />Blocked Request Details
            </div>
            <p>{msg.reason}</p>
            {!!msg.triggered_rules?.length && (
              <p className="text-danger/80">
                Triggered by: {msg.triggered_rules.join(', ')}
              </p>
            )}
          </div>
        </motion.div>
      )}
      {!isUser && <GovernancePanel msg={msg} />}
      {!isUser && <FeedbackBar msg={msg} onFeedback={onFeedback} />}
    </>
  )
}

export default function ChatPage() {
  const { user } = useAuth()
  const [messages, setMessages] = useState([{
    id: 'welcome',
    role: 'assistant',
    content: `Hello ${user?.username}. I'm your role-aware company policy assistant. Ask a question about an approved policy, and I'll answer using indexed policy sources.`,
    timestamp: new Date().toISOString(),
    status: 'allowed',
    risk_level: 'low',
    risk_score: 0,
  }])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [assistantStatus, setAssistantStatus] = useState(null)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)
  const currentRole = getRoleMeta(user?.role)
  const roleInfo = {
    color: currentRole.value === 'admin' ? 'text-purple-400' : currentRole.value === 'hr' ? 'text-warn' : currentRole.value === 'intern' ? 'text-accent' : 'text-slate-200',
    label: currentRole.badge,
    desc: currentRole.desc,
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => {
    api.get('/chat/status').then(({ data }) => setAssistantStatus(data)).catch(() => setAssistantStatus(null))
  }, [])

  const assistantReady = assistantStatus?.rag?.ready && assistantStatus?.llm?.configured

  const sendMessage = async (text = input) => {
    const msg = text.trim()
    if (!msg || loading) return
    setInput('')

    const userMsg = { id: Date.now(), role: 'user', content: msg, timestamp: new Date().toISOString() }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      const res = await api.post('/chat', { message: msg })
      const { log_id, response, status, risk_score, risk_level, reason, triggered_rules, validator_notes, is_high_risk, recommended_action, policy_evidence, sources } = res.data
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        log_id,
        content: response,
        timestamp: new Date().toISOString(),
        status,
        risk_score,
        risk_level,
        reason,
        triggered_rules: triggered_rules || [],
        validator_notes: validator_notes || [],
        is_high_risk,
        recommended_action,
        policy_evidence: policy_evidence || [],
        sources: sources || [],
        feedback: null,
      }])
    } catch {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: 'Connection error. Please check the backend server is running.',
        timestamp: new Date().toISOString(),
        status: 'blocked',
        risk_level: 'low',
        risk_score: 0,
      }])
    } finally {
      setLoading(false)
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }

  const clearChat = async () => {
    await api.post('/chat/clear').catch(() => {})
    setMessages([{
      id: 'welcome',
      role: 'assistant',
      content: `Chat cleared. Ask me a question about a company policy, and I'll look for relevant indexed sources.`,
      timestamp: new Date().toISOString(),
      status: 'allowed',
      risk_level: 'low',
      risk_score: 0,
    }])
  }

  const submitFeedback = async (logId, value) => {
    try {
      await api.post('/chat/feedback', { log_id: logId, value })
      setMessages(prev => prev.map(msg => msg.log_id === logId ? { ...msg, feedback: value } : msg))
    } catch {
      // Feedback is optional; keep the chat usable if it cannot be saved.
    }
  }

  const exportConversation = async () => {
    const res = await api.get('/chat/export', { responseType: 'blob' })
    const url = window.URL.createObjectURL(res.data)
    const link = document.createElement('a')
    link.href = url
    link.download = 'secureai-conversation-export.csv'
    link.click()
    window.URL.revokeObjectURL(url)
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col h-full min-h-0">
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 glass flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-9 h-9 rounded-xl bg-accent/10 border border-accent/20 flex items-center justify-center">
              <Cpu size={16} className="text-accent" />
            </div>
            <div className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full bg-success border border-bg-900" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white">SecureAI Chatbot</h2>
            <p className="text-[10px] text-slate-500 font-mono">Role-aware policy assistant · {assistantReady ? 'RAG + LLM configured' : 'Setup required'}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg glass-light border border-white/8 ${roleInfo.color}`}>
            <ShieldAlert size={12} />
            <span className="text-xs font-mono font-bold">{roleInfo.label}</span>
            <span className="text-[10px] text-slate-500 hidden sm:block">- {roleInfo.desc}</span>
          </div>
          <button onClick={exportConversation} className="p-2 rounded-lg hover:bg-white/5 border border-white/8 text-slate-400 hover:text-accent">
            <Download size={14} />
          </button>
          <button onClick={clearChat} className="p-2 rounded-lg hover:bg-danger/10 border border-transparent hover:border-danger/20 text-slate-500 hover:text-danger">
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      <div className="flex-1 min-h-0 px-6 py-4">
        {assistantStatus && !assistantReady && (
          <div className="mb-3 rounded-xl border border-warn/20 bg-warn/5 px-4 py-3 text-xs text-warn/90">
            Chat needs setup before it can answer from policies.
            {!assistantStatus.llm?.configured && ` Configure an LLM provider (currently: ${assistantStatus.llm?.provider || 'unknown'}).`}
            {!assistantStatus.rag?.sentence_transformers_installed && ' Install the RAG packages from backend/requirements-rag.txt.'}
            {!assistantStatus.rag?.qdrant_client_installed && ' qdrant-client is not installed.'}
            {!assistantStatus.rag?.index_exists && ' Build the policy index with backend/scripts/ingest_policies.py.'}
          </div>
        )}
        <div className="flex-1 min-h-0 flex flex-col xl:flex-row gap-4">
          <div className="flex-1 min-h-0 glass-light border border-white/8 rounded-2xl overflow-hidden flex flex-col">
            <div className="flex-1 min-h-0 overflow-y-auto px-6 py-4">
              <AnimatePresence initial={false}>
                {messages.map(msg => <ChatBubble key={msg.id} msg={msg} onFeedback={submitFeedback} />)}
                {loading && <TypingIndicator key="typing" />}
              </AnimatePresence>
              <div ref={bottomRef} />
            </div>

            <div className="px-6 py-4 border-t border-white/5 flex-shrink-0">
              <div className="flex gap-3 items-end">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      sendMessage()
                    }
                  }}
                  rows={1}
                  className="flex-1 px-4 py-3 rounded-xl bg-bg-800 border border-white/8 text-white placeholder-slate-600 focus:outline-none focus:border-accent/50 focus:shadow-glow transition-all text-sm resize-none font-mono leading-relaxed"
                  placeholder="Ask about a company policy... (Enter to send)"
                  style={{ minHeight: '48px', maxHeight: '120px' }}
                />
                <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={() => sendMessage()} disabled={loading || !input.trim()} className="w-12 h-12 rounded-xl bg-accent text-bg-900 flex items-center justify-center disabled:opacity-40 disabled:cursor-not-allowed hover:bg-accent-dim transition-all shadow-glow flex-shrink-0">
                  <Send size={16} />
                </motion.button>
              </div>
              <p className="text-[10px] text-slate-600 mt-2 font-mono text-center">
                Answers are grounded in indexed policy documents and tailored to your role.
              </p>
            </div>
          </div>

        </div>
      </div>
    </motion.div>
  )
}
