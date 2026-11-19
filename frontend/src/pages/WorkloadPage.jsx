import { useEffect, useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { ClipboardList, CheckCircle2, Clock, AlertTriangle, TrendingUp, Briefcase } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { isManagerRole } from '../utils/roles'
import api from '../utils/api'
import { useTheme } from '../utils/theme'

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass rounded-2xl p-4 border border-white/5">
      <div className="flex items-center justify-between mb-2">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${color}1a` }}>
          <Icon size={15} style={{ color }} />
        </div>
      </div>
      <p className="text-xl font-bold text-white">{value}</p>
      <p className="text-[11px] text-slate-500 mt-0.5">{label}</p>
    </motion.div>
  )
}

function WorkloadCards({ summary }) {
  const [theme] = useTheme()
  const ACCENT = theme === 'dark' ? '#ef5539' : '#7fa95b'
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      <StatCard icon={ClipboardList} label="Assigned Tasks" value={summary.assigned_tasks} color={ACCENT} />
      <StatCard icon={CheckCircle2} label="Completed" value={summary.completed_tasks} color="#4f9a6a" />
      <StatCard icon={Clock} label="Pending" value={summary.pending_tasks} color="#c9922e" />
      <StatCard icon={AlertTriangle} label="Overdue" value={summary.overdue_tasks} color="#c4553f" />
      <StatCard icon={TrendingUp} label="Completion Rate" value={`${Math.round(summary.completion_rate * 100)}%`} color="#8a7bb8" />
      <StatCard icon={Briefcase} label="Active Workload" value={summary.workload} color="#5f86a8" />
    </div>
  )
}

export default function WorkloadPage() {
  const { user } = useAuth()
  const isManager = isManagerRole(user?.role)
  const [own, setOwn] = useState(null)
  const [team, setTeam] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(false)
    try {
      const res = await api.get('/work/workload')
      setOwn(res.data.workload)
      if (isManager) {
        const teamRes = await api.get('/work/workload', { params: { scope: 'team' } })
        setTeam(teamRes.data.workload || [])
      }
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }, [isManager])

  useEffect(() => { load() }, [load])

  if (loading) return <div className="h-full flex items-center justify-center text-xs text-slate-500">Loading workload data...</div>
  if (error) return <div className="h-full flex items-center justify-center text-xs text-danger">Couldn't load workload data.</div>

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6">
      <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-xl font-bold text-white">{isManager ? 'Team Workload' : 'My Workload'}</h1>
        <p className="text-xs text-slate-500 mt-0.5">
          {isManager ? 'Real-time task metrics across your team' : 'Your assigned tasks at a glance'}
        </p>
      </motion.div>

      {own && (
        <div>
          {isManager && <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2">Your own tasks</p>}
          <WorkloadCards summary={own} />
        </div>
      )}

      {isManager && (
        <div>
          <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2">Team breakdown</p>
          <div className="glass rounded-2xl border border-white/5 overflow-hidden">
            {team.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500">No team assignments recorded yet</div>
            ) : (
              <div className="ui-table-scroll">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-white/5 text-slate-500 uppercase text-[10px] tracking-wider">
                    <th className="text-left px-4 py-3 font-semibold">User</th>
                    <th className="text-left px-4 py-3 font-semibold">Assigned</th>
                    <th className="text-left px-4 py-3 font-semibold">Completed</th>
                    <th className="text-left px-4 py-3 font-semibold">Pending</th>
                    <th className="text-left px-4 py-3 font-semibold">Overdue</th>
                    <th className="text-left px-4 py-3 font-semibold">Completion</th>
                    <th className="text-left px-4 py-3 font-semibold">Workload</th>
                  </tr>
                </thead>
                <tbody>
                  {team.map((row) => (
                    <tr key={row.user_id} className="border-b border-white/5 last:border-0 hover:bg-white/[0.02]">
                      <td className="px-4 py-3 text-slate-300">{row.username} <span className="text-slate-600">({row.role})</span></td>
                      <td className="px-4 py-3 text-slate-400">{row.assigned_tasks}</td>
                      <td className="px-4 py-3 text-success">{row.completed_tasks}</td>
                      <td className="px-4 py-3 text-warn">{row.pending_tasks}</td>
                      <td className={row.overdue_tasks > 0 ? 'px-4 py-3 text-danger font-semibold' : 'px-4 py-3 text-slate-500'}>{row.overdue_tasks}</td>
                      <td className="px-4 py-3 text-slate-400">{Math.round(row.completion_rate * 100)}%</td>
                      <td className="px-4 py-3 text-slate-400">{row.workload}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
