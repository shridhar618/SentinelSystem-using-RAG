import { useEffect, useRef, useState } from 'react'
import { Check, Copy, X } from 'lucide-react'
import toast from 'react-hot-toast'
import { shortHash } from './format'

// Revelio primitives, rendered with the scoped `.rv` classes in explorer.css.

export function Panel({ title, actions, children, className = '', bodyClassName = 'panel__body', flush = false }) {
  return (
    <section className={`panel ${className}`}>
      {(title || actions) && (
        <header className="panel__head">
          <h2 className="panel__title section-title">{title}</h2>
          {actions}
        </header>
      )}
      {flush ? children : <div className={bodyClassName}>{children}</div>}
    </section>
  )
}

export function StatTile({ icon: Icon, label, value, sub, tone, loading }) {
  return (
    <div className="panel stat">
      <div className="stat__top">
        <span className="label">{label}</span>
        {Icon && <Icon className="icon" aria-hidden="true" />}
      </div>
      {loading ? (
        <div className="skeleton" style={{ height: 32, width: '55%' }} />
      ) : (
        <div className={`stat__value ${tone ? `is-${tone}` : ''}`}>{value}</div>
      )}
      {sub && <div className="stat__sub mono">{sub}</div>}
    </div>
  )
}

export function Chip({ tone, icon: Icon, children }) {
  return (
    <span className={`chip ${tone ? `chip--${tone}` : ''}`}>
      {Icon && <Icon className="icon" aria-hidden="true" />}
      {children}
    </span>
  )
}

export function HashText({ hash, full = false, head, tail, label = 'hash' }) {
  const [copied, setCopied] = useState(false)
  const timer = useRef()
  useEffect(() => () => clearTimeout(timer.current), [])

  if (!hash) return <span className="hash faint">—</span>

  const copy = async (event) => {
    event.stopPropagation()
    try {
      await navigator.clipboard.writeText(hash)
      setCopied(true)
      clearTimeout(timer.current)
      timer.current = setTimeout(() => setCopied(false), 1400)
    } catch {
      toast.error('Could not copy to clipboard')
    }
  }

  return (
    <span className={`hash ${full ? 'hash--full' : ''}`} title={hash}>
      <span className="hash__text">{full ? hash : shortHash(hash, head, tail)}</span>
      <button type="button" className="hash__copy" onClick={copy} aria-label={`Copy ${label}`}>
        {copied ? <Check className="icon" /> : <Copy className="icon" />}
      </button>
    </span>
  )
}

export function EmptyState({ icon: Icon, title, text, action, compact = false }) {
  return (
    <div className={`empty ${compact ? 'empty--compact' : ''}`}>
      {Icon && (
        <div className="empty__icon">
          <span className="empty__ring" />
          <Icon className="icon" aria-hidden="true" />
        </div>
      )}
      <h3 className="empty__title">{title}</h3>
      {text && <p className="empty__text">{text}</p>}
      {action}
    </div>
  )
}

export function Tabs({ tabs, value, onChange, label }) {
  return (
    <div className="tabs" role="tablist" aria-label={label}>
      {tabs.map(({ id, label: tabLabel, icon: Icon }) => (
        <button
          key={id}
          type="button"
          role="tab"
          className="tabs__tab"
          aria-selected={value === id}
          onClick={() => onChange(id)}
        >
          {Icon && <Icon className="icon" aria-hidden="true" />}
          {tabLabel}
        </button>
      ))}
    </div>
  )
}

export function Modal({ title, subtitle, onClose, children, footer }) {
  const ref = useRef(null)

  useEffect(() => {
    const previous = document.activeElement
    ref.current?.focus()
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => {
      window.removeEventListener('keydown', onKey)
      previous?.focus?.()
    }
  }, [onClose])

  return (
    <div className="modal-scrim" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="panel modal" role="dialog" aria-modal="true" aria-label={title} tabIndex={-1} ref={ref}>
        <header className="panel__head">
          <div>
            <h2 className="panel__title section-title">{title}</h2>
            {subtitle && <div className="label" style={{ marginTop: 4 }}>{subtitle}</div>}
          </div>
          <button type="button" className="btn btn--ghost btn--icon btn--sm" onClick={onClose} aria-label="Close">
            <X className="icon" />
          </button>
        </header>
        {children}
        {footer && <footer className="modal__foot">{footer}</footer>}
      </div>
    </div>
  )
}
