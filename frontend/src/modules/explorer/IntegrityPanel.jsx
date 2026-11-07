import { AlertTriangle, Check, ShieldCheck, ShieldAlert, X } from 'lucide-react'
import { Panel } from './components'
import { ISSUE_LABEL, ISSUE_STEP, formatNumber, fullTime, shortHash } from './format'

const STEPS = [
  { id: 'load', label: 'Load sealed blocks', detail: 'Read every block in sequence order' },
  { id: 'hashes', label: 'Recompute hashes', detail: 'SHA-256 over content + previous hash' },
  { id: 'links', label: 'Check links', detail: 'Each block points at the one before' },
  { id: 'sequence', label: 'Check sequence', detail: 'No missing or duplicated blocks' },
]

function stepState(id, running, result) {
  if (running) return 'active'
  if (!result) return 'idle'
  if (id === 'load') return 'done'
  const broken = result.issues?.some((issue) => ISSUE_STEP[issue.kind] === id)
  return broken ? 'warn' : 'done'
}

export default function IntegrityPanel({ result, running, error, onVerify, onOpen }) {
  return (
    <Panel
      title="Chain integrity"
      actions={
        <button type="button" className="btn btn--sm" onClick={onVerify} disabled={running}>
          {running ? <span className="spinner" style={{ width: 12, height: 12 }} /> : <ShieldCheck className="icon" />}
          {running ? 'Verifying' : 'Re-verify'}
        </button>
      }
    >
      <div className="stack">
        <ol className="pipeline">
          {STEPS.map((step, i) => {
            const state = stepState(step.id, running, result)
            return (
              <li key={step.id} className={`pipeline__step is-${state}`}>
                <span className="pipeline__node">
                  {state === 'done' ? <Check className="icon" /> : state === 'warn' ? <X className="icon" /> : i + 1}
                </span>
                <span className="pipeline__text">
                  <span className="pipeline__label">{step.label}</span>
                  <span className="pipeline__detail">{step.detail}</span>
                </span>
              </li>
            )
          })}
        </ol>

        {error && (
          <div className="alert alert--error">
            <AlertTriangle className="icon" />
            <span><strong>Verification failed to run.</strong> {error}</span>
          </div>
        )}

        {result && !running && (
          result.ok ? (
            <div className="alert alert--ok">
              <ShieldCheck className="icon" />
              <span>
                <strong>Chain intact.</strong> {formatNumber(result.checked)} blocks recomputed in{' '}
                {result.duration_ms} ms. No edits, deletions or forks found.
              </span>
            </div>
          ) : (
            <div className="alert alert--error">
              <ShieldAlert className="icon" />
              <span>
                <strong>{formatNumber(result.issue_count)} integrity issue{result.issue_count === 1 ? '' : 's'}.</strong>{' '}
                The first break is at block #{result.first_break?.seq}. Records from that point can't be trusted
                until it's investigated.
              </span>
            </div>
          )
        )}

        {result?.issues?.length > 0 && !running && (
          <ul className="issues">
            {result.issues.map((issue, i) => (
              <li key={`${issue.seq}-${issue.kind}-${i}`}>
                <button type="button" className="issue" onClick={() => onOpen(issue.seq)}>
                  <span className="issue__top">
                    <strong className="mono">#{issue.seq}</strong>
                    <span className="tag" style={{ color: 'var(--red-text)' }}>{ISSUE_LABEL[issue.kind] || issue.kind}</span>
                  </span>
                  <span>{issue.detail}</span>
                  {issue.expected && issue.kind !== 'sequence_gap' && (
                    <span className="mono faint" style={{ fontSize: 11 }}>
                      expected {shortHash(issue.expected)} · found {shortHash(issue.actual)}
                    </span>
                  )}
                </button>
              </li>
            ))}
          </ul>
        )}

        {result && !running && (
          <dl className="kv">
            <dt>Last run</dt>
            <dd className="mono">{fullTime(result.verified_at)}</dd>
            <dt>Head</dt>
            <dd className="mono">{shortHash(result.head_hash)}</dd>
            {result.unsealed > 0 && (
              <>
                <dt>Unsealed</dt>
                <dd className="mono">{formatNumber(result.unsealed)}</dd>
              </>
            )}
          </dl>
        )}
      </div>
    </Panel>
  )
}
