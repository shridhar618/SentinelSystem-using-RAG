import { Shield } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import ThemeToggle from './ThemeToggle'

/**
 * Landing-style header (logo, round theme toggle, stacked uppercase links)
 * shared by the full-screen pages: Welcome, Login, Face unlock.
 * links: [{ label, to?, onClick?, active?, tone? }] — the last one with tone 'end'
 * sits under the divider, like "Log in" on the landing page.
 */
export default function SiteHeader({ links = [] }) {
  const navigate = useNavigate()
  const main = links.filter((l) => l.tone !== 'end')
  const end = links.filter((l) => l.tone === 'end')
  const go = (l) => (e) => {
    e.preventDefault()
    if (l.onClick) l.onClick()
    else if (l.to) navigate(l.to)
  }
  return (
    <header className="sa-nav">
      <button type="button" className="sa-brand" onClick={() => navigate('/landing')} aria-label="SecureAI home">
        <span className="sa-brand__mark"><Shield size={22} strokeWidth={1.8} /></span>
        <span className="sa-brand__name">SecureAI</span>
      </button>
      <ThemeToggle className="sa-theme" size={17} />
      <nav className="sa-nav__links" aria-label="Page">
        <ul>
          {main.map((l) => (
            <li key={l.label}>
              <a href={l.to || '#'} onClick={go(l)} aria-current={l.active ? 'true' : undefined}>{l.label}</a>
            </li>
          ))}
          {end.map((l) => (
            <li key={l.label} className="sa-nav__login">
              <a href={l.to || '#'} onClick={go(l)} aria-current={l.active ? 'true' : undefined}>{l.label}</a>
            </li>
          ))}
        </ul>
      </nav>
    </header>
  )
}
