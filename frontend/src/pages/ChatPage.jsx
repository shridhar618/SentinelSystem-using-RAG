import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { format } from 'date-fns'
import { Send, Trash2, Download, Cpu, PanelRight, Sparkles, X, ShieldCheck } from 'lucide-react'

import { useAuth } from '../context/AuthContext'
import api from '../utils/api'
import { getSocket } from '../utils/socket'
import { getRoleMeta } from '../utils/roles'
import AssistantMessage from '../components/chat/AssistantMessage'
import ChatSidebar from '../components/chat/ChatSidebar'
import Suggestions from '../components/chat/Suggestions'

const MAX_CHARS = 4000

function welcomeMessage(text) {
  return { id: 'welcome', role: 'assistant', content: text, timestamp: new Date().toISOString(), status: 'allowed', risk_level: 'low', risk_score: 0 }
}

function storageKey(user) {
  return user ? `secureai.chat.${user.id || user.username}` : null
}

function loadStored(user) {
  try {
    const raw = sessionStorage.getItem(storageKey(user))
    const parsed = raw ? JSON.parse(raw) : null
    return Array.isArray(parsed) && parsed.length ? parsed : null
  } catch {
    return null
  }
}

function TypingIndicator() {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="flex items-center gap-3 mb-5">
      <div className="w-8 h-8 rounded-xl chat-badge flex items-center justify-center flex-shrink-0">
        <Cpu size={14} />
      </div>
      <div className="rounded-2xl rounded-tl-md bg-bg-800/80 border border-white/8 px-4 py-3 flex items-center gap-3">
        <div className="flex gap-1.5 items-center h-4">
          {[0, 1, 2].map(i => <div key={i} className="typing-dot" style={{ animationDelay: `${i * 0.2}s` }} />)}
        </div>
        <span className="text-[11px] font-mono text-slate-500">Checking role, policy and risk…</span>
      </div>
    </motion.div>
  )
}

function UserMessage({ msg }) {
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }} className="flex flex-col items-end mb-5">
      <div className="chat-primary max-w-[85%] sm:max-w-[70%] px-4 py-2.5 rounded-2xl rounded-tr-md text-[13.5px] font-medium leading-relaxed whitespace-pre-wrap break-words">
        {msg.content}
      </div>
      <span className="text-[10px] text-slate-600 font-mono mt-1 px-1">{format(new Date(msg.timestamp), 'HH:mm')}</span>
    </motion.div>
  )
}

function EmptyState({ user, roleMeta, permissions, onPick }) {
  return (
    <div className="max-w-3xl mx-auto py-6 sm:py-10">
      <div className="flex items-center gap-3 mb-2">
        <div className="w-12 h-12 rounded-2xl chat-badge flex items-center justify-center">
          <ShieldCheck size={22} />
        </div>
        <div>
          <p className="text-[11px] font-mono uppercase tracking-wider text-slate-500">Signed in as {roleMeta.label}</p>
          <p className="text-2xl sm:text-[28px] font-bold text-white leading-tight" style={{ fontFamily: "'Syne', 'Inter', sans-serif", letterSpacing: '-0.02em' }}>
            Hi {user?.username}, <span className="chat-accent-text">ask SecureAI</span>
          </p>
        </div>
      </div>
      <p className="text-sm text-slate-400 mb-6 max-w-2xl">
        A policy assistant that knows your role. Every question is checked against your permissions and
        company policy, given a risk score, and logged. Answers cite their sources.
      </p>
      <Suggestions permissions={permissions} onPick={onPick} />
    </div>
  )
}

export default function ChatPage() {
  const { user, token, permissions } = useAuth()
  const roleMeta = getRoleMeta(user?.role)
  const [messages, setMessages] = useState(() => loadStored(user) || [])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [assistantStatus, setAssistantStatus] = useState(null)
  const [awaitingReply, setAwaitingReply] = useState(false)
  const [showTray, setShowTray] = useState(false)
  const [showPanel, setShowPanel] = useState(false)
  const replyCursorRef = useRef(null)      // id of the last async reply seen
  const seenReplyIdsRef = useRef(new Set())
  const scrollRef = useRef(null)
  const inputRef = useRef(null)

  const conversation = messages.filter(m => m.id !== 'welcome')
  const isEmpty = conversation.length === 0

  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    if (isEmpty && !loading) el.scrollTo({ top: 0 })
    else el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }, [messages, loading, awaitingReply, isEmpty])

  useEffect(() => {
    const key = storageKey(user)
    if (!key) return
    try {
      sessionStorage.setItem(key, JSON.stringify(messages.slice(-100)))
    } catch {
      // storage full or blocked; the chat still works without it
    }
  }, [messages, user])

  // Auto-grow the composer.
  useLayoutEffect(() => {
    const el = inputRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }, [input])

  // Some replies arrive asynchronously (e.g. after a hand-off), pushed over
  // the authenticated socket to this user's private room, with an HTTP
  // fallback below. Duplicate deliveries are ignored by id.
  const appendAsyncReply = (reply) => {
    if (!reply || seenReplyIdsRef.current.has(reply.id)) return
    seenReplyIdsRef.current.add(reply.id)
    replyCursorRef.current = Math.max(replyCursorRef.current || 0, reply.id)
    setAwaitingReply(false)
    setMessages(prev => [...prev, {
      id: `reply-${reply.id}`,
      role: 'assistant',
      content: reply.content,
      timestamp: reply.timestamp || new Date().toISOString(),
      status: 'allowed',
      risk_level: 'low',
      risk_score: 0,
    }])
  }

  useEffect(() => {
    if (!token) return undefined
    const socket = getSocket(token)
    const onReply = (reply) => appendAsyncReply(reply)
    socket.on('assistant_reply', onReply)
    return () => { socket.off('assistant_reply', onReply) }
  }, [token])

  useEffect(() => {
    if (!awaitingReply) return undefined
    const poll = setInterval(async () => {
      try {
        const { data } = await api.get('/chat/updates', { params: { after: replyCursorRef.current || 0 } })
        ;(data.replies || []).forEach(appendAsyncReply)
      } catch {
        // transient; keep waiting
      }
    }, 4000)
    return () => clearInterval(poll)
  }, [awaitingReply])

  useEffect(() => {
    api.get('/chat/status').then(({ data }) => setAssistantStatus(data)).catch(() => setAssistantStatus(null))
  }, [])

  const assistantReady = assistantStatus?.rag?.ready && assistantStatus?.llm?.configured
  const modeLabel = !assistantStatus ? 'Connecting…' : assistantReady ? `RAG + ${assistantStatus.llm.provider}` : 'Offline policy mode'

  const pickSuggestion = (text) => {
    setInput(text)
    setShowTray(false)
    setTimeout(() => inputRef.current?.focus(), 50)
  }

  const sendMessage = async (text = input) => {
    const msg = text.trim()
    if (!msg || loading) return
    setInput('')
    setShowTray(false)

    const userMsg = { id: Date.now(), role: 'user', content: msg, timestamp: new Date().toISOString() }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      const res = await api.post('/chat', { message: msg })
      const { log_id, response, status, risk_score, risk_level, reason, triggered_rules, validator_notes, is_high_risk, recommended_action, policy_evidence, sources, pending, reply_cursor } = res.data
      if (reply_cursor) {
        replyCursorRef.current = Math.max(replyCursorRef.current || 0, reply_cursor)
        if (!pending) seenReplyIdsRef.current.add(reply_cursor)
      }
      if (pending) {
        setAwaitingReply(true)
        return
      }
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
    } catch (err) {
      const serverError = err?.response?.data?.error
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: serverError || 'Connection error. Please check that the backend server is running.',
        timestamp: new Date().toISOString(),
        status: err?.response?.status === 403 ? 'blocked' : 'error',
        reason: serverError,
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
    setMessages([])
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

  const sidebar = <ChatSidebar roleMeta={roleMeta} permissions={permissions} messages={messages} status={assistantStatus} />
  const nearLimit = input.length > MAX_CHARS * 0.8

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="chat-scope flex flex-col h-full min-h-0">
      {/* Header */}
      <header className="flex items-center justify-between gap-3 px-4 sm:px-6 py-3 border-b border-white/5 glass flex-shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          <div className="relative flex-shrink-0">
            <div className="w-9 h-9 rounded-xl chat-badge flex items-center justify-center">
              <Cpu size={16} />
            </div>
            <span className={`absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-bg-900 ${assistantReady ? 'bg-success' : 'bg-warn'}`} />
          </div>
          <div className="min-w-0">
            <h2 className="text-sm font-bold text-white leading-tight">SecureAI Assistant</h2>
            <p className="text-[10.5px] text-slate-500 font-mono truncate">Role-aware · policy-checked · audited · {modeLabel}</p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 sm:gap-2">
          <span className={`hidden sm:inline-flex items-center px-2.5 py-1 rounded-lg border border-white/10 bg-white/5 text-[11px] font-mono font-bold ${roleMeta.color}`}>
            {roleMeta.badge}
          </span>
          <button onClick={() => setShowPanel(true)} className="xl:hidden p-2 rounded-lg border border-white/8 text-slate-400 hover:text-accent hover:bg-white/5" title="Access & risk" aria-label="Show access and risk panel">
            <PanelRight size={14} />
          </button>
          <button onClick={exportConversation} className="p-2 rounded-lg border border-white/8 text-slate-400 hover:text-accent hover:bg-white/5" title="Export conversation (CSV)" aria-label="Export conversation">
            <Download size={14} />
          </button>
          <button onClick={clearChat} disabled={isEmpty} className="p-2 rounded-lg border border-white/8 text-slate-400 hover:text-danger hover:bg-danger/10 disabled:opacity-40 disabled:pointer-events-none" title="Clear conversation" aria-label="Clear conversation">
            <Trash2 size={14} />
          </button>
        </div>
      </header>

      <div className="flex-1 min-h-0 flex gap-4 px-3 sm:px-6 py-4">
        {/* Conversation */}
        <div className="flex-1 min-w-0 min-h-0 flex flex-col rounded-2xl glass-light overflow-hidden">
          <div ref={scrollRef} className="flex-1 min-h-0 overflow-y-auto px-4 sm:px-6 pt-5">
            {isEmpty
              ? <EmptyState user={user} roleMeta={roleMeta} permissions={permissions} onPick={pickSuggestion} />
              : (
                <div className="max-w-4xl mx-auto">
                  <AnimatePresence initial={false}>
                    {conversation.map(msg => (msg.role === 'user'
                      ? <UserMessage key={msg.id} msg={msg} />
                      : <AssistantMessage key={msg.id} msg={msg} onFeedback={submitFeedback} />))}
                    {(loading || awaitingReply) && <TypingIndicator key="typing" />}
                  </AnimatePresence>
                </div>
              )}
          </div>

          {/* Composer */}
          <div className="px-3 sm:px-6 pb-4 pt-2 flex-shrink-0">
            <div className="max-w-4xl mx-auto">
              <AnimatePresence>
                {showTray && !isEmpty && (
                  <motion.div
                    initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 8 }}
                    className="mb-2 rounded-2xl bg-bg-800/95 border border-white/10 p-3 shadow-card"
                  >
                    <div className="flex justify-end -mb-6">
                      <button onClick={() => setShowTray(false)} className="p-1 rounded-md text-slate-500 hover:text-slate-200" aria-label="Close suggestions"><X size={13} /></button>
                    </div>
                    <Suggestions permissions={permissions} onPick={pickSuggestion} compact />
                  </motion.div>
                )}
              </AnimatePresence>
              <div className="flex items-end gap-2">
                <textarea
                  ref={inputRef}
                  value={input}
                  maxLength={MAX_CHARS}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      sendMessage()
                    }
                  }}
                  rows={1}
                  aria-label="Message SecureAI"
                  className="flex-1 block px-4 py-3 text-[13.5px] resize-none leading-relaxed placeholder-slate-600"
                  placeholder="Ask about a policy, a project, or what your role can access…"
                  style={{ minHeight: '48px' }}
                />
                <motion.button
                  whileTap={{ scale: 0.94 }}
                  onClick={() => sendMessage()}
                  disabled={loading || !input.trim()}
                  className="chat-primary w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0 disabled:opacity-40 disabled:cursor-not-allowed"
                  aria-label="Send message"
                >
                  <Send size={16} />
                </motion.button>
              </div>
              <div className="flex items-center justify-between gap-2 mt-1.5 px-1">
                <button
                  onClick={() => setShowTray(v => !v)}
                  className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-lg text-[11.5px] transition-colors ${isEmpty ? 'invisible' : ''} ${showTray ? 'bg-accent/10 text-accent' : 'text-slate-500 hover:text-accent hover:bg-white/5'}`}
                >
                  <Sparkles size={12} />Suggestions
                </button>
                <span className={`text-[10.5px] font-mono ${nearLimit ? 'text-warn' : 'text-slate-600'}`}>
                  {nearLimit ? `${input.length}/${MAX_CHARS}` : <span className="hidden sm:inline">Enter to send · Shift+Enter for new line</span>}
                </span>
              </div>
              <p className="text-[10.5px] text-slate-600 mt-1 text-center">
                Every message is checked against your role and company policy, risk-scored, and recorded in the audit log.
              </p>
            </div>
          </div>
        </div>

        {/* Side panel (desktop) */}
        <aside className="hidden xl:block w-80 flex-shrink-0 overflow-y-auto">{sidebar}</aside>
      </div>

      {/* Side panel (mobile drawer) */}
      <AnimatePresence>
        {showPanel && (
          <motion.div className="fixed inset-0 z-50 xl:hidden" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <div className="absolute inset-0 bg-black/40" onClick={() => setShowPanel(false)} />
            <motion.aside
              initial={{ x: '100%' }} animate={{ x: 0 }} exit={{ x: '100%' }} transition={{ type: 'tween', duration: 0.25 }}
              className="absolute right-0 top-0 bottom-0 w-[min(22rem,100%)] bg-bg-900 border-l border-white/10 p-4 overflow-y-auto"
            >
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm font-bold text-white">Access & risk</p>
                <button onClick={() => setShowPanel(false)} className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5" aria-label="Close panel"><X size={15} /></button>
              </div>
              {sidebar}
            </motion.aside>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
