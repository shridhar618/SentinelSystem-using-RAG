import { useState } from 'react'
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import TopBar from './TopBar'
import {
  MessageSquare,
  LayoutDashboard,
  LogOut,
  Shield,
  Cpu,
  Database,
  ScanFace,
  ClipboardList,
  Briefcase,
  KanbanSquare,
  BarChart3,
  AlertTriangle,
  UserPlus,
  Users,
  ShieldAlert,
  Blocks,
  X,
} from 'lucide-react'
import { getRoleMeta, getRolePillClass, isManagerRole } from '../utils/roles'

export default function Layout() {
  const { user, logout, hasPermission } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const roleMeta = getRoleMeta(user?.role)
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  const isAdmin = user?.role === 'admin'
  const isManager = isManagerRole(user?.role)

  // Grouped to match the platform's section structure (AI Governance /
  // Security / Workforce / Communication / Admin). A section is omitted
  // entirely if the current user has no visible items in it, rather than
  // rendering an empty header.
  const sections = [
    {
      label: 'Overview',
      items: [{ to: '/my-dashboard', icon: LayoutDashboard, label: 'My Dashboard', desc: 'Usage, risk & tasks' }],
    },
    {
      label: 'AI Governance',
      items: [
        ...(hasPermission('use_ai_assistant')
          ? [{ to: '/chat', icon: Cpu, label: 'Governance Assistant', desc: 'Policy-grounded AI chat' }]
          : []),
        ...(hasPermission('manage_policies')
          ? [{ to: '/policy-sources', icon: Database, label: 'Policy Sources', desc: 'Governance corpus' }]
          : []),
      ],
    },
    {
      label: 'Workforce',
      items: [
        { to: '/attendance', icon: ScanFace, label: 'Attendance', desc: 'Face check-in/out' },
        { to: '/my-work', icon: Briefcase, label: 'My Work', desc: 'Assigned tasks' },
        { to: '/work-board', icon: KanbanSquare, label: 'Work Board', desc: 'Kanban status view' },
        { to: '/workload', icon: BarChart3, label: 'KPI / Workload', desc: 'Task analytics' },
        ...(isManager
          ? [
              { to: '/work-assignments', icon: ClipboardList, label: 'Work Assign', desc: 'Manager workspace' },
              { to: '/work-escalations', icon: AlertTriangle, label: 'Escalations', desc: 'Resolve risks' },
            ]
          : []),
      ],
    },
    {
      label: 'Communication',
      items: [
        { to: '/messages', icon: MessageSquare, label: 'Secure Msg', desc: 'Private comms' },
      ],
    },
    {
      label: 'Security',
      items: isAdmin
        ? [
            { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', desc: 'Audit & analytics' },
            { to: '/governance-cases', icon: ShieldAlert, label: 'Governance Cases', desc: 'Review & escalations' },
            { to: '/blockchain-explorer', icon: Blocks, label: 'Blockchain Explorer', desc: 'Audit hash chain' },
            { to: '/ghost-mode', icon: Shield, label: 'Ghost Mode', desc: 'Stealth monitoring' },
            { to: '/attack-sim', icon: Shield, label: 'Attack Simulator', desc: 'Security testing' },
          ]
        : [],
    },
    {
      label: 'Admin',
      items: isAdmin
        ? [
            { to: '/user-management', icon: Users, label: 'Users & Logins', desc: 'Login history & user CRUD' },
            { to: '/user-access', icon: UserPlus, label: 'User Access', desc: 'Create accounts' },
          ]
        : [],
    },
  ].filter((section) => section.items.length > 0)

  const sidebarContent = (
    <>
      <div className="ui-side__brand">
        <button type="button" className="ui-brand" onClick={() => navigate('/welcome')} aria-label="SecureAI home">
          <span className="ui-brand__mark"><Shield size={20} strokeWidth={1.8} /></span>
          <span className="ui-brand__name">SecureAI</span>
        </button>
        <button
          onClick={() => setMobileNavOpen(false)}
          className="lg:hidden ui-circle"
          aria-label="Close navigation"
        >
          <X size={14} />
        </button>
      </div>

      <div className="ui-side__user">
        <span className="ui-avatar">{user?.username?.[0]?.toUpperCase()}</span>
        <div className="min-w-0 flex-1">
          <p className="ui-side__username">{user?.username}</p>
          <p className="ui-side__email">{user?.email}</p>
        </div>
        <span className={`ui-role ${getRolePillClass(user?.role)}`}>{roleMeta.badge}</span>
      </div>

      <nav className="ui-side__nav" aria-label="Main">
        {sections.map((section) => (
          <div key={section.label} className="ui-side__group">
            <p className="ui-eyebrow ui-eyebrow--sm">{section.label}</p>
            <ul>
              {section.items.map(({ to, icon: Icon, label, desc }) => (
                <li key={to}>
                  <NavLink to={to} onClick={() => setMobileNavOpen(false)} title={desc}
                    className={({ isActive }) => `ui-navlink ${isActive ? 'is-active' : ''}`}>
                    {({ isActive }) => (
                      <>
                        {isActive && (
                          <motion.span
                            layoutId="ui-nav-active"
                            className="ui-navlink__bg"
                            transition={{ type: 'spring', stiffness: 170, damping: 28, mass: 1 }}
                          />
                        )}
                        <Icon size={15} strokeWidth={2} />
                        <span>{label}</span>
                      </>
                    )}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      <div className="ui-side__foot">
        <button type="button" className="ui-signout" onClick={() => { logout(); navigate('/login') }}>
          <LogOut size={14} /> Sign out
        </button>
      </div>
    </>
  )

  return (
    <div className="ui-app flex h-screen overflow-hidden">
      {/* Desktop sidebar */}
      <motion.aside
        initial={{ x: -80, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 1.1, ease: [0.22, 1, 0.36, 1] }}
        className="ui-side hidden lg:flex z-20"
      >
        {sidebarContent}
      </motion.aside>

      {/* Mobile sidebar overlay */}
      <AnimatePresence>
        {mobileNavOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileNavOpen(false)}
              className="fixed inset-0 bg-black/40 z-30 lg:hidden"
            />
            <motion.aside
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
              className="ui-side ui-side--mobile fixed inset-y-0 left-0 z-40 lg:hidden"
            >
              {sidebarContent}
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
        <TopBar onToggleMobileNav={() => setMobileNavOpen((v) => !v)} />
        <main className="ui-main flex-1 min-h-0 overflow-hidden">
          <div className="h-full overflow-hidden">
            <div key={location.pathname} className="ui-page h-full">
              <Outlet />
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
