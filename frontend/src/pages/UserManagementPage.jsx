import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { format, formatDistanceToNow } from 'date-fns'
import {
  AlertCircle, CheckCircle2, ChevronLeft, ChevronRight, Eye, KeyRound, LogIn, Pencil,
  Power, RefreshCw, Search, ShieldAlert, Trash2, UserPlus, Users, X,
} from 'lucide-react'

import api from '../utils/api'
import ConfirmDialog from '../components/ConfirmDialog'
import { useAuth } from '../context/AuthContext'
import { FALLBACK_ROLE_NAMES, getRolePillClass } from '../utils/roles'

// Backend timestamps are naive UTC; mark them as UTC so the browser shows local time.
const toDate = value => (value ? new Date(/[zZ]|[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`) : null)
const fmt = value => (value ? format(toDate(value), 'dd MMM yyyy, HH:mm') : '—')
const ago = value => (value ? formatDistanceToNow(toDate(value), { addSuffix: true }) : 'Never')

function browserName(ua) {
  if (!ua) return '—'
  if (/Edg\//.test(ua)) return 'Edge'
  if (/OPR\/|Opera/.test(ua)) return 'Opera'
  if (/Chrome\//.test(ua)) return 'Chrome'
  if (/Firefox\//.test(ua)) return 'Firefox'
  if (/Safari\//.test(ua)) return 'Safari'
  return ua.split(' ')[0].slice(0, 24)
}

const inputCls = 'w-full px-3 py-2.5 rounded-xl bg-bg-800 border border-white/8 text-white placeholder-slate-600 focus:outline-none focus:border-accent/50 transition-all text-sm'
const labelCls = 'block text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-1.5'

function Pill({ tone = 'slate', children }) {
  const tones = {
    success: 'text-success bg-success/10 border-success/20',
    danger: 'text-danger bg-danger/10 border-danger/20',
    warn: 'text-warn bg-warn/10 border-warn/20',
    accent: 'text-accent bg-accent/10 border-accent/20',
    slate: 'text-slate-400 bg-white/5 border-white/10',
  }
  return <span className={`inline-flex items-center uppercase text-[10px] font-bold px-1.5 py-0.5 rounded border whitespace-nowrap ${tones[tone]}`}>{children}</span>
}

const EVENT_TONE = { login: 'success', login_failed: 'danger', logout: 'slate' }
const EVENT_LABEL = { login: 'Login', login_failed: 'Failed', logout: 'Logout' }

function StatCard({ label, value, tone = 'text-white' }) {
  return (
    <div className="glass rounded-2xl p-4 border border-white/5">
      <p className="text-[10px] text-slate-500 font-mono uppercase tracking-wider">{label}</p>
      <p className={`text-2xl font-bold mt-1 ${tone}`}>{value ?? '—'}</p>
    </div>
  )
}

function Modal({ open, onClose, title, children, wide = false }) {
  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={onClose} className="fixed inset-0 bg-black/60 z-[50]" />
          <motion.div role="dialog" aria-modal="true"
            initial={{ opacity: 0, scale: 0.97, y: 8 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.97, y: 8 }}
            transition={{ duration: 0.15 }}
            className={`fixed z-[55] left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[94%] ${wide ? 'max-w-3xl' : 'max-w-md'} max-h-[88vh] overflow-y-auto glass border border-white/10 rounded-2xl p-5 shadow-card`}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-white">{title}</h3>
              <button onClick={onClose} aria-label="Close" className="p-1.5 rounded-lg text-slate-500 hover:text-white hover:bg-white/5"><X size={14} /></button>
            </div>
            {children}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

function LoginTable({ events, loading, emptyText, showUser = true }) {
  const headers = [...(showUser ? ['User', 'Role'] : []), 'Time', 'Event', 'Method', 'IP address', 'Browser', 'Details']
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-[11px] font-mono">
        <thead>
          <tr className="border-b border-white/5 text-slate-500 uppercase tracking-wider text-[10px]">
            {headers.map(h => <th key={h} className="px-3 py-3 text-left font-semibold">{h}</th>)}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr><td colSpan={headers.length} className="text-center py-10 text-slate-600">Loading...</td></tr>
          ) : !events.length ? (
            <tr><td colSpan={headers.length} className="text-center py-10 text-slate-600">{emptyText}</td></tr>
          ) : events.map(ev => (
            <tr key={ev.id} className={`border-b border-white/5 ${ev.event_type === 'login_failed' ? 'bg-danger/5' : 'hover:bg-white/5'}`}>
              {showUser && <td className="px-3 py-2.5 text-slate-200 font-semibold">{ev.username}</td>}
              {showUser && <td className="px-3 py-2.5 text-slate-400 uppercase">{ev.role}</td>}
              <td className="px-3 py-2.5 text-slate-400 whitespace-nowrap" title={ago(ev.timestamp)}>{fmt(ev.timestamp)}</td>
              <td className="px-3 py-2.5"><Pill tone={EVENT_TONE[ev.event_type]}>{EVENT_LABEL[ev.event_type] || ev.event_type}</Pill></td>
              <td className="px-3 py-2.5 text-slate-400">{ev.method === 'login_code' ? 'Login code' : ev.method === 'password' ? 'Password' : '—'}</td>
              <td className="px-3 py-2.5 text-slate-400">{ev.ip || '—'}</td>
              <td className="px-3 py-2.5 text-slate-400" title={ev.user_agent || ''}>{browserName(ev.user_agent)}</td>
              <td className="px-3 py-2.5 text-slate-500 max-w-[220px] truncate" title={ev.reason || ev.description}>{ev.reason || ev.description}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function UserManagementPage() {
  const navigate = useNavigate()
  const { user: me } = useAuth()

  const [tab, setTab] = useState('users')
  const [summary, setSummary] = useState(null)
  const [roles, setRoles] = useState(FALLBACK_ROLE_NAMES)
  const [toast, setToast] = useState(null)

  // Users tab
  const [users, setUsers] = useState([])
  const [usersLoading, setUsersLoading] = useState(true)
  const [filters, setFilters] = useState({ q: '', role: '', status: '' })

  // Login activity tab
  const [activity, setActivity] = useState({ events: [], total: 0, page: 1, pages: 1 })
  const [activityLoading, setActivityLoading] = useState(false)
  const [activityFilters, setActivityFilters] = useState({ username: '', event_type: '', page: 1 })

  // Modals
  const [detail, setDetail] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [editing, setEditing] = useState(null)
  const [editForm, setEditForm] = useState({})
  const [saving, setSaving] = useState(false)
  const [editError, setEditError] = useState('')
  const [confirm, setConfirm] = useState(null)
  const [issuedCode, setIssuedCode] = useState(null)

  const notify = (type, text) => {
    setToast({ type, text })
    window.clearTimeout(notify.timer)
    notify.timer = window.setTimeout(() => setToast(null), 4500)
  }

  const loadSummary = useCallback(() => {
    api.get('/admin/users/summary').then(res => setSummary(res.data)).catch(() => {})
  }, [])

  const loadUsers = useCallback(() => {
    setUsersLoading(true)
    const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v))
    api.get('/admin/users', { params })
      .then(res => setUsers(res.data.users || []))
      .catch(err => notify('error', err.response?.data?.error || 'Could not load users'))
      .finally(() => setUsersLoading(false))
  }, [filters])

  const loadActivity = useCallback(() => {
    setActivityLoading(true)
    const params = { per_page: 25, ...Object.fromEntries(Object.entries(activityFilters).filter(([, v]) => v)) }
    api.get('/admin/login-activity', { params })
      .then(res => setActivity(res.data))
      .catch(err => notify('error', err.response?.data?.error || 'Could not load login activity'))
      .finally(() => setActivityLoading(false))
  }, [activityFilters])

  useEffect(() => {
    loadSummary()
    api.get('/roles').then(res => {
      const names = (res.data?.roles || []).map(r => r.name).filter(Boolean)
      if (names.length) setRoles(names)
    }).catch(() => {})
  }, [loadSummary])

  useEffect(() => {
    const t = setTimeout(loadUsers, 250)
    return () => clearTimeout(t)
  }, [loadUsers])

  useEffect(() => {
    if (tab !== 'activity') return
    const t = setTimeout(loadActivity, 250)
    return () => clearTimeout(t)
  }, [tab, loadActivity])

  const refreshAll = () => {
    loadSummary()
    loadUsers()
    if (tab === 'activity') loadActivity()
  }

  const openDetail = id => {
    setDetailLoading(true)
    setDetail({ loading: true })
    api.get(`/admin/users/${id}`)
      .then(res => setDetail(res.data))
      .catch(err => { setDetail(null); notify('error', err.response?.data?.error || 'Could not load user') })
      .finally(() => setDetailLoading(false))
  }

  const openEdit = u => {
    setEditing(u)
    setEditError('')
    setEditForm({ username: u.username, email: u.email, role: u.role, is_active: u.is_active !== false, clear_suspicious: false })
  }

  const saveEdit = async e => {
    e.preventDefault()
    setSaving(true)
    setEditError('')
    try {
      const payload = { ...editForm }
      if (!payload.clear_suspicious) delete payload.clear_suspicious
      await api.put(`/admin/users/${editing.id}`, payload)
      setEditing(null)
      notify('success', `Saved changes to ${editForm.username}`)
      refreshAll()
    } catch (err) {
      setEditError(err.response?.data?.error || 'Update failed')
    } finally {
      setSaving(false)
    }
  }

  const runConfirmed = async () => {
    const action = confirm
    setConfirm(null)
    if (!action) return
    const { kind, user: u } = action
    try {
      if (kind === 'toggle') {
        await api.put(`/admin/users/${u.id}`, { is_active: u.is_active === false })
        notify('success', `${u.username} ${u.is_active === false ? 'activated' : 'deactivated'}`)
      } else if (kind === 'reset') {
        const res = await api.post(`/admin/users/${u.id}/reset-code`)
        setIssuedCode({ username: u.username, code: res.data.login_code })
      } else if (kind === 'delete') {
        await api.delete(`/admin/users/${u.id}`)
        notify('success', `${u.username} deleted`)
        if (detail?.user?.id === u.id) setDetail(null)
      }
      refreshAll()
    } catch (err) {
      notify('error', err.response?.data?.error || 'Action failed')
    }
  }

  const confirmCopy = {
    toggle: u => u.is_active === false
      ? { title: `Activate ${u.username}?`, message: 'They will be able to sign in again with their existing login code or password.', confirmLabel: 'Activate', danger: false }
      : { title: `Deactivate ${u.username}?`, message: 'They will be blocked from signing in. Their data and history stay intact, and you can reactivate them at any time.', confirmLabel: 'Deactivate', danger: true },
    reset: u => ({ title: `Reset login code for ${u.username}?`, message: 'A new login code is generated and shown once. Their old login code and password stop working immediately.', confirmLabel: 'Reset code', danger: true }),
    delete: u => ({ title: `Delete ${u.username} permanently?`, message: 'This removes the account, face credential, attendance and notifications. It cannot be undone. Audit log entries are kept. Users with messages, work items or governance records cannot be deleted; deactivate them instead.', confirmLabel: 'Delete user', danger: true }),
  }
  const confirmProps = confirm ? confirmCopy[confirm.kind](confirm.user) : {}

  const isSelf = u => me && u.id === me.id

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="h-full overflow-y-auto">
      <div className="px-4 sm:px-6 py-6 max-w-7xl space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-white">Users & Logins</h1>
            <p className="text-[10px] text-slate-500 font-mono mt-0.5 tracking-widest uppercase">Every account, its login history, and full user management</p>
          </div>
          <div className="flex gap-2">
            <button onClick={refreshAll} className="px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-xs text-slate-300 hover:text-white flex items-center gap-2">
              <RefreshCw size={13} /> Refresh
            </button>
            <button onClick={() => navigate('/user-access')} className="px-3 py-2 rounded-xl bg-accent text-bg-900 text-xs font-bold hover:bg-accent-dim flex items-center gap-2">
              <UserPlus size={13} /> Add user
            </button>
          </div>
        </div>

        <AnimatePresence>
          {toast && (
            <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              className={`flex items-center gap-2 p-3 rounded-xl border text-sm ${toast.type === 'error' ? 'bg-danger/10 border-danger/20 text-danger' : 'bg-success/10 border-success/20 text-success'}`}>
              {toast.type === 'error' ? <AlertCircle size={14} /> : <CheckCircle2 size={14} />}
              <span className="flex-1">{toast.text}</span>
              <button onClick={() => setToast(null)} aria-label="Dismiss"><X size={13} /></button>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="grid gap-3 grid-cols-2 md:grid-cols-3 xl:grid-cols-6">
          <StatCard label="Total users" value={summary?.total_users} />
          <StatCard label="Active" value={summary?.active_users} tone="text-success" />
          <StatCard label="Inactive" value={summary?.inactive_users} tone="text-slate-400" />
          <StatCard label="Suspicious" value={summary?.suspicious_users} tone="text-warn" />
          <StatCard label="Logins (24h)" value={summary?.logins_24h} tone="text-accent" />
          <StatCard label="Failed logins (24h)" value={summary?.failed_logins_24h} tone="text-danger" />
        </div>

        <div className="flex gap-2 border-b border-white/5">
          {[['users', 'All users', Users], ['activity', 'Login activity', LogIn]].map(([key, label, Icon]) => (
            <button key={key} onClick={() => setTab(key)}
              className={`px-4 py-2.5 text-sm flex items-center gap-2 border-b-2 -mb-px transition-colors ${tab === key ? 'border-accent text-white' : 'border-transparent text-slate-500 hover:text-slate-300'}`}>
              <Icon size={14} /> {label}
            </button>
          ))}
        </div>

        {tab === 'users' && (
          <div className="glass rounded-2xl border border-white/5 shadow-card">
            <div className="p-4 grid gap-3 md:grid-cols-[1fr_200px_180px]">
              <div className="relative">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600" />
                <input value={filters.q} onChange={e => setFilters(f => ({ ...f, q: e.target.value }))}
                  className={`${inputCls} pl-9`} placeholder="Search username or email..." />
              </div>
              <select value={filters.role} onChange={e => setFilters(f => ({ ...f, role: e.target.value }))} className={inputCls}>
                <option value="">All roles</option>
                {roles.map(r => <option key={r} value={r.toLowerCase()}>{r}</option>)}
              </select>
              <select value={filters.status} onChange={e => setFilters(f => ({ ...f, status: e.target.value }))} className={inputCls}>
                <option value="">All statuses</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="suspicious">Suspicious</option>
              </select>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-[11px] font-mono">
                <thead>
                  <tr className="border-y border-white/5 text-slate-500 uppercase tracking-wider text-[10px]">
                    {['User', 'Role', 'Status', 'Logins', 'Failed', 'Last login', 'Created', 'Actions'].map(h => (
                      <th key={h} className="px-3 py-3 text-left font-semibold">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {usersLoading && !users.length ? (
                    <tr><td colSpan={8} className="text-center py-12 text-slate-600">Loading...</td></tr>
                  ) : !users.length ? (
                    <tr><td colSpan={8} className="text-center py-12 text-slate-600">No users match these filters</td></tr>
                  ) : users.map(u => (
                    <tr key={u.id} className={`border-b border-white/5 hover:bg-white/5 ${u.is_active === false ? 'opacity-60' : ''}`}>
                      <td className="px-3 py-2.5">
                        <p className="text-slate-200 font-semibold">{u.username}{isSelf(u) && <span className="text-accent ml-1">(you)</span>}</p>
                        <p className="text-slate-500 text-[10px]">{u.email}</p>
                      </td>
                      <td className="px-3 py-2.5"><span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border uppercase ${getRolePillClass(u.role)}`}>{u.role}</span></td>
                      <td className="px-3 py-2.5">
                        <div className="flex flex-wrap gap-1">
                          {u.is_active === false ? <Pill tone="slate">Inactive</Pill> : <Pill tone="success">Active</Pill>}
                          {u.is_suspicious && <Pill tone="warn">Suspicious</Pill>}
                          {u.face_enrolled && <Pill tone="accent">Face</Pill>}
                        </div>
                      </td>
                      <td className="px-3 py-2.5 text-slate-300">{u.login_count}</td>
                      <td className={`px-3 py-2.5 ${u.failed_login_count ? 'text-danger font-semibold' : 'text-slate-500'}`}>{u.failed_login_count}</td>
                      <td className="px-3 py-2.5 text-slate-400 whitespace-nowrap" title={fmt(u.last_login)}>{ago(u.last_login)}</td>
                      <td className="px-3 py-2.5 text-slate-500 whitespace-nowrap">{u.created_at ? format(toDate(u.created_at), 'dd MMM yyyy') : '—'}</td>
                      <td className="px-3 py-2.5">
                        <div className="flex gap-1">
                          <IconBtn title="View details" onClick={() => openDetail(u.id)}><Eye size={12} /></IconBtn>
                          <IconBtn title="Edit" onClick={() => openEdit(u)}><Pencil size={12} /></IconBtn>
                          <IconBtn title="Reset login code" onClick={() => setConfirm({ kind: 'reset', user: u })}><KeyRound size={12} /></IconBtn>
                          <IconBtn title={isSelf(u) ? 'You cannot deactivate yourself' : u.is_active === false ? 'Activate' : 'Deactivate'}
                            disabled={isSelf(u)} tone={u.is_active === false ? 'success' : 'warn'}
                            onClick={() => setConfirm({ kind: 'toggle', user: u })}><Power size={12} /></IconBtn>
                          <IconBtn title={isSelf(u) ? 'You cannot delete yourself' : 'Delete'} disabled={isSelf(u)} tone="danger"
                            onClick={() => setConfirm({ kind: 'delete', user: u })}><Trash2 size={12} /></IconBtn>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="px-4 py-3 text-[10px] text-slate-600 font-mono">{users.length} user{users.length === 1 ? '' : 's'} shown</p>
          </div>
        )}

        {tab === 'activity' && (
          <div className="glass rounded-2xl border border-white/5 shadow-card">
            <div className="p-4 grid gap-3 md:grid-cols-[1fr_200px]">
              <div className="relative">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600" />
                <input value={activityFilters.username}
                  onChange={e => setActivityFilters(f => ({ ...f, username: e.target.value, page: 1 }))}
                  className={`${inputCls} pl-9`} placeholder="Filter by username..." />
              </div>
              <select value={activityFilters.event_type}
                onChange={e => setActivityFilters(f => ({ ...f, event_type: e.target.value, page: 1 }))} className={inputCls}>
                <option value="">All events</option>
                <option value="login">Successful logins</option>
                <option value="login_failed">Failed logins</option>
                <option value="logout">Logouts</option>
              </select>
            </div>
            <LoginTable events={activity.events} loading={activityLoading} emptyText="No login events match these filters" />
            <div className="flex items-center justify-between px-4 py-3 text-[11px] text-slate-500 font-mono">
              <span>{activity.total} event{activity.total === 1 ? '' : 's'}</span>
              <div className="flex items-center gap-2">
                <IconBtn title="Previous page" disabled={activity.page <= 1}
                  onClick={() => setActivityFilters(f => ({ ...f, page: f.page - 1 }))}><ChevronLeft size={13} /></IconBtn>
                <span>Page {activity.page} of {activity.pages}</span>
                <IconBtn title="Next page" disabled={activity.page >= activity.pages}
                  onClick={() => setActivityFilters(f => ({ ...f, page: f.page + 1 }))}><ChevronRight size={13} /></IconBtn>
              </div>
            </div>
            <p className="px-4 pb-4 text-[10px] text-slate-600">IP address and browser are recorded for logins from this version onward; older entries show “—”.</p>
          </div>
        )}
      </div>

      {/* View details */}
      <Modal open={!!detail} onClose={() => setDetail(null)} title={detail?.user ? `User: ${detail.user.username}` : 'User details'} wide>
        {detailLoading || !detail?.user ? (
          <p className="text-sm text-slate-500 py-8 text-center">Loading...</p>
        ) : (
          <div className="space-y-5">
            <div className="grid gap-3 grid-cols-2 md:grid-cols-4 text-sm">
              {[
                ['Email', detail.user.email],
                ['Role', detail.user.role?.toUpperCase()],
                ['Status', detail.user.is_active === false ? 'Inactive' : 'Active'],
                ['Face credential', detail.user.face_enrolled ? 'Enrolled' : 'Not enrolled'],
                ['Created', fmt(detail.user.created_at)],
                ['Last login', fmt(detail.user.last_login)],
                ['Last logout', fmt(detail.user.last_logout)],
                ['Last failed login', fmt(detail.user.last_failed_login)],
                ['Total logins', detail.user.login_count],
                ['Failed logins', detail.user.failed_login_count],
                ['AI requests', detail.ai_requests],
                ['Blocked AI requests', detail.blocked_ai_requests],
              ].map(([label, value]) => (
                <div key={label} className="rounded-xl bg-bg-900/40 border border-white/8 p-3">
                  <p className="text-[10px] text-slate-500 font-mono uppercase tracking-wider">{label}</p>
                  <p className="text-white mt-1 break-all text-[13px]">{value ?? '—'}</p>
                </div>
              ))}
            </div>

            {detail.user.is_suspicious && (
              <div className="flex items-center gap-2 p-3 rounded-xl bg-warn/10 border border-warn/20 text-warn text-xs">
                <ShieldAlert size={14} /> Flagged suspicious {detail.user.flagged_at ? `on ${fmt(detail.user.flagged_at)}` : ''} after {detail.user.sensitive_query_count} sensitive queries.
              </div>
            )}

            <div>
              <p className="text-xs font-bold text-white mb-2">Recent login activity</p>
              <div className="rounded-xl border border-white/8">
                <LoginTable events={detail.recent_logins} loading={false} emptyText="No login activity yet" showUser={false} />
              </div>
            </div>

            <div>
              <p className="text-xs font-bold text-white mb-2">Recent attendance</p>
              {detail.recent_attendance.length ? (
                <div className="flex flex-wrap gap-2">
                  {detail.recent_attendance.map(a => (
                    <span key={a.id} className="text-[11px] font-mono px-2 py-1 rounded-lg bg-white/5 border border-white/10 text-slate-300">
                      {a.event_type === 'check_in' ? 'In' : 'Out'} · {fmt(a.created_at)}
                    </span>
                  ))}
                </div>
              ) : <p className="text-xs text-slate-500">No attendance records.</p>}
            </div>

            {Object.keys(detail.delete_blockers || {}).length > 0 && (
              <p className="text-[11px] text-slate-500">
                Cannot be deleted while linked to: {Object.entries(detail.delete_blockers).map(([k, v]) => `${v} ${k}`).join(', ')}. Deactivate instead.
              </p>
            )}
          </div>
        )}
      </Modal>

      {/* Edit */}
      <Modal open={!!editing} onClose={() => setEditing(null)} title={editing ? `Edit ${editing.username}` : ''}>
        {editing && (
          <form onSubmit={saveEdit} className="space-y-4">
            {editError && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-danger/10 border border-danger/20 text-danger text-xs">
                <AlertCircle size={13} /> {editError}
              </div>
            )}
            <div>
              <label className={labelCls}>Username</label>
              <input className={`${inputCls} font-mono`} value={editForm.username} required maxLength={80}
                onChange={e => setEditForm(f => ({ ...f, username: e.target.value }))} />
            </div>
            <div>
              <label className={labelCls}>Email</label>
              <input type="email" className={inputCls} value={editForm.email} required maxLength={120}
                onChange={e => setEditForm(f => ({ ...f, email: e.target.value }))} />
            </div>
            <div>
              <label className={labelCls}>Role</label>
              <select className={inputCls} value={editForm.role} disabled={isSelf(editing)}
                onChange={e => setEditForm(f => ({ ...f, role: e.target.value }))}>
                {!roles.some(r => r.toLowerCase() === editForm.role) && <option value={editForm.role}>{editForm.role}</option>}
                {roles.map(r => <option key={r} value={r.toLowerCase()}>{r}</option>)}
              </select>
              {isSelf(editing) && <p className="text-[10px] text-slate-500 mt-1">You cannot change your own role.</p>}
            </div>
            <label className={`flex items-center gap-2 text-sm text-slate-300 ${isSelf(editing) ? 'opacity-50' : ''}`}>
              <input type="checkbox" checked={editForm.is_active} disabled={isSelf(editing)}
                onChange={e => setEditForm(f => ({ ...f, is_active: e.target.checked }))} />
              Account active (can sign in)
            </label>
            {editing.is_suspicious && (
              <label className="flex items-center gap-2 text-sm text-warn">
                <input type="checkbox" checked={editForm.clear_suspicious}
                  onChange={e => setEditForm(f => ({ ...f, clear_suspicious: e.target.checked }))} />
                Clear the suspicious flag and reset the sensitive-query count
              </label>
            )}
            <div className="flex justify-end gap-2 pt-1">
              <button type="button" onClick={() => setEditing(null)} className="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-xs text-slate-300 hover:text-white">Cancel</button>
              <button type="submit" disabled={saving} className="px-4 py-2 rounded-lg bg-accent text-bg-900 text-xs font-bold hover:bg-accent-dim disabled:opacity-50">
                {saving ? 'Saving...' : 'Save changes'}
              </button>
            </div>
          </form>
        )}
      </Modal>

      {/* New login code */}
      <Modal open={!!issuedCode} onClose={() => setIssuedCode(null)} title="New login code issued">
        {issuedCode && (
          <div className="space-y-3">
            <p className="text-xs text-slate-400">Share this with <span className="text-white font-semibold">{issuedCode.username}</span>. It is shown only once.</p>
            <div className="rounded-xl bg-accent/10 border border-accent/20 p-4 text-center">
              <p className="text-xl text-accent font-bold font-mono tracking-[0.25em] select-all">{issuedCode.code}</p>
            </div>
            <button onClick={() => navigator.clipboard?.writeText(issuedCode.code).then(() => notify('success', 'Code copied'))}
              className="w-full py-2 rounded-lg bg-white/5 border border-white/10 text-xs text-slate-300 hover:text-white">Copy code</button>
          </div>
        )}
      </Modal>

      <ConfirmDialog
        open={!!confirm}
        title={confirmProps.title}
        message={confirmProps.message}
        confirmLabel={confirmProps.confirmLabel}
        danger={confirmProps.danger}
        onConfirm={runConfirmed}
        onCancel={() => setConfirm(null)}
      />
    </motion.div>
  )
}

function IconBtn({ children, onClick, title, disabled = false, tone = 'accent' }) {
  const hover = {
    accent: 'hover:bg-accent/10 hover:text-accent hover:border-accent/20',
    success: 'hover:bg-success/10 hover:text-success hover:border-success/20',
    warn: 'hover:bg-warn/10 hover:text-warn hover:border-warn/20',
    danger: 'hover:bg-danger/10 hover:text-danger hover:border-danger/20',
  }[tone]
  return (
    <button type="button" onClick={onClick} title={title} aria-label={title} disabled={disabled}
      className={`p-1.5 rounded-lg bg-white/5 text-slate-500 border border-transparent ${hover} disabled:opacity-30 disabled:pointer-events-none`}>
      {children}
    </button>
  )
}
