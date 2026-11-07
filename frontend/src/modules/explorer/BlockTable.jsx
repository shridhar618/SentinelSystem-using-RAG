import { Boxes, ChevronLeft, ChevronRight, Search } from 'lucide-react'
import { Chip, EmptyState, HashText } from './components'
import { eventLabel, formatNumber, fullTime, relTime, riskTone, statusTone } from './format'

const STATUSES = ['allowed', 'filtered', 'blocked']
const RISKS = ['low', 'medium', 'high']

export default function BlockTable({
  data,
  loading,
  error,
  filters,
  onFilters,
  onOpen,
  flagged,
}) {
  const blocks = data?.blocks || []
  const set = (key) => (e) => onFilters({ ...filters, [key]: e.target.value, page: 1 })
  const hasFilters = Boolean(filters.q || filters.status || filters.risk_level || filters.event_type)

  return (
    <section className="panel">
      <header className="panel__head">
        <h2 className="panel__title section-title">Blocks</h2>
        <span className="label">{data ? `${formatNumber(data.total)} matching` : ' '}</span>
      </header>

      <div className="toolbar">
        <label className="search">
          <span className="sr-only">Search blocks</span>
          <Search className="icon" aria-hidden="true" />
          <input
            className="input"
            type="search"
            placeholder="Block #, hash prefix, user or resource"
            value={filters.q}
            onChange={set('q')}
          />
        </label>
        <select className="select" value={filters.status} onChange={set('status')} aria-label="Filter by status">
          <option value="">All statuses</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select className="select" value={filters.risk_level} onChange={set('risk_level')} aria-label="Filter by risk">
          <option value="">All risk</option>
          {RISKS.map((r) => <option key={r} value={r}>{r}</option>)}
        </select>
        <select className="select" value={filters.event_type} onChange={set('event_type')} aria-label="Filter by event">
          <option value="">All events</option>
          {(data?.event_types || []).map((t) => <option key={t} value={t}>{eventLabel(t)}</option>)}
        </select>
      </div>

      {error ? (
        <div className="panel__body"><div className="alert alert--error"><span>{error}</span></div></div>
      ) : loading && !data ? (
        <div className="panel__body stack">
          {Array.from({ length: 6 }).map((_, i) => <div key={i} className="skeleton" style={{ height: 34 }} />)}
        </div>
      ) : blocks.length === 0 ? (
        <EmptyState
          compact
          icon={Boxes}
          title={hasFilters ? 'No blocks match' : 'The chain is empty'}
          text={hasFilters
            ? 'Try a shorter hash prefix or clear a filter.'
            : 'Blocks appear here as soon as SecureAI records its first audit event.'}
        />
      ) : (
        <div className="ledger-wrap">
          <table className="ledger">
            <thead>
              <tr>
                <th>Block</th>
                <th>Hash</th>
                <th>Actor</th>
                <th>Event</th>
                <th>Status</th>
                <th>Risk</th>
                <th>Age</th>
              </tr>
            </thead>
            <tbody>
              {blocks.map((b, i) => (
                <tr
                  key={b.seq}
                  className={flagged?.has(b.seq) ? 'is-flagged' : ''}
                  style={{ animationDelay: `${Math.min(i, 10) * 25}ms` }}
                  tabIndex={0}
                  onClick={() => onOpen(b.seq)}
                  onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), onOpen(b.seq))}
                  aria-label={`Open block ${b.seq}`}
                >
                  <td data-col="seq"><span className="ledger__seq mono">#{b.seq}</span></td>
                  <td data-col="hash"><HashText hash={b.hash} head={8} tail={4} label={`hash of block ${b.seq}`} /></td>
                  <td data-col="actor">
                    <span className="ledger__actor">
                      <strong>{b.username}</strong>
                      <span>{b.role}</span>
                    </span>
                  </td>
                  <td data-col="event"><span className="tag">{eventLabel(b.event_type)}</span></td>
                  <td data-col="status"><Chip tone={statusTone(b.status)}>{b.status}</Chip></td>
                  <td data-col="risk"><Chip tone={riskTone(b.risk_level)}>{b.risk_level || '—'}</Chip></td>
                  <td data-col="time" className="ledger__time mono" title={fullTime(b.timestamp)}>{relTime(b.timestamp)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data && data.pages > 1 && (
        <footer className="pager">
          <span className="mono faint">Page {data.page} / {data.pages}</span>
          <div className="pager__btns">
            <button
              type="button"
              className="btn btn--sm"
              disabled={data.page <= 1 || loading}
              onClick={() => onFilters({ ...filters, page: data.page - 1 })}
            >
              <ChevronLeft className="icon" /> Newer
            </button>
            <button
              type="button"
              className="btn btn--sm"
              disabled={data.page >= data.pages || loading}
              onClick={() => onFilters({ ...filters, page: data.page + 1 })}
            >
              Older <ChevronRight className="icon" />
            </button>
          </div>
        </footer>
      )}
    </section>
  )
}
