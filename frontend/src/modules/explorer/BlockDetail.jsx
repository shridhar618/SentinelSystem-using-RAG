import { useEffect, useState } from 'react'
import {
  AlertTriangle,
  ArrowDown,
  ChevronLeft,
  ChevronRight,
  FileJson,
  Fingerprint,
  Info,
  Link2,
  ShieldAlert,
  ShieldCheck,
} from 'lucide-react'
import { Chip, HashText, Modal, Tabs } from './components'
import { errorMessage, fetchBlock } from './api'
import { eventLabel, fullTime, relTime, riskTone, statusTone } from './format'

const TABS = [
  { id: 'overview', label: 'Overview', icon: Info },
  { id: 'payload', label: 'Payload', icon: FileJson },
  { id: 'chain', label: 'Chain', icon: Link2 },
]

export default function BlockDetail({ seq, onNavigate, onClose }) {
  const [state, setState] = useState({ loading: true, data: null, error: null })
  const [tab, setTab] = useState('overview')

  useEffect(() => {
    let alive = true
    setState((s) => ({ ...s, loading: true, error: null }))
    fetchBlock(seq)
      .then((data) => alive && setState({ loading: false, data, error: null }))
      .catch((err) => alive && setState({ loading: false, data: null, error: errorMessage(err, 'Could not load block') }))
    return () => { alive = false }
  }, [seq])

  const { data, loading, error } = state
  const block = data?.block
  const integrity = data?.integrity
  const valid = integrity && integrity.hash_valid && integrity.link_valid

  return (
    <Modal
      title={`Block #${seq}`}
      subtitle={block ? `${eventLabel(block.event_type)} · ${fullTime(block.timestamp)} UTC` : 'Loading'}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn btn--sm" disabled={!data?.prev_seq} onClick={() => onNavigate(data.prev_seq)}>
            <ChevronLeft className="icon" /> {data?.prev_seq ? `#${data.prev_seq}` : 'Genesis'}
          </button>
          <button type="button" className="btn btn--sm" disabled={!data?.next_seq} onClick={() => onNavigate(data.next_seq)}>
            {data?.next_seq ? `#${data.next_seq}` : 'Latest'} <ChevronRight className="icon" />
          </button>
        </>
      }
    >
      <Tabs tabs={TABS} value={tab} onChange={setTab} label="Block details" />
      <div className="modal__body">
        {error ? (
          <div className="alert alert--error"><AlertTriangle className="icon" /><span>{error}</span></div>
        ) : loading || !data ? (
          <div className="stack">
            {Array.from({ length: 5 }).map((_, i) => <div key={i} className="skeleton" style={{ height: 22 }} />)}
          </div>
        ) : tab === 'overview' ? (
          <div className="stack">
            {valid ? (
              <div className="alert alert--ok">
                <ShieldCheck className="icon" />
                <span><strong>Block verified.</strong> Its hash recomputes correctly and it links to block #{seq - 1 || 'genesis'}.</span>
              </div>
            ) : (
              <div className="alert alert--error">
                <ShieldAlert className="icon" />
                <span>
                  <strong>Integrity failure.</strong>{' '}
                  {!integrity.hash_valid && 'This block’s content no longer matches its sealed hash. '}
                  {!integrity.link_valid && 'Its previous-hash pointer does not match the block before it.'}
                </span>
              </div>
            )}
            <dl className="kv">
              <dt>Hash</dt>
              <dd><HashText hash={block.hash} full /></dd>
              <dt>Previous</dt>
              <dd><HashText hash={block.prev_hash} full label="previous hash" /></dd>
              <dt>Actor</dt>
              <dd>{block.username} <span className="faint">· {block.role}</span></dd>
              <dt>Event</dt>
              <dd><span className="tag">{eventLabel(block.event_type)}</span></dd>
              <dt>Status</dt>
              <dd><Chip tone={statusTone(block.status)}>{block.status}</Chip></dd>
              <dt>Risk</dt>
              <dd>
                <Chip tone={riskTone(block.risk_level)}>
                  {block.risk_level || '—'}{typeof block.risk_score === 'number' ? ` · ${block.risk_score.toFixed(2)}` : ''}
                </Chip>
              </dd>
              {block.resource && (<><dt>Resource</dt><dd className="mono">{block.resource}</dd></>)}
              <dt>Recorded</dt>
              <dd className="mono">{fullTime(block.timestamp)} UTC <span className="faint">({relTime(block.timestamp)})</span></dd>
              <dt>Audit log</dt>
              <dd className="mono">#{block.log_id}</dd>
            </dl>
          </div>
        ) : tab === 'payload' ? (
          <div className="stack">
            <p className="muted" style={{ fontSize: 12.5 }}>
              The audit record this block seals. Every field shown here is covered by the block hash.
            </p>
            <pre className="code">{JSON.stringify(data.payload, null, 2)}</pre>
          </div>
        ) : (
          <div className="links">
            <div className="link-card">
              <Fingerprint className="icon" />
              <div>
                <div className="label">{seq > 1 ? `Block #${seq - 1}` : 'Genesis'}</div>
                <HashText hash={integrity.expected_prev_hash} label="parent hash" />
              </div>
            </div>
            <div className="link-arrow"><ArrowDown className="icon" /></div>
            <div className="link-card is-current">
              <Fingerprint className="icon" />
              <div>
                <div className="label label--cyan">Block #{seq} · stored prev</div>
                <HashText hash={block.prev_hash} label="stored previous hash" />
              </div>
            </div>
            <dl className="kv" style={{ marginTop: 8 }}>
              <dt>Link</dt>
              <dd><Chip tone={integrity.link_valid ? 'green' : 'red'}>{integrity.link_valid ? 'matches parent' : 'broken'}</Chip></dd>
              <dt>Stored</dt>
              <dd><HashText hash={block.hash} full label="stored hash" /></dd>
              <dt>Recomputed</dt>
              <dd><HashText hash={integrity.recomputed_hash} full label="recomputed hash" /></dd>
              <dt>Content</dt>
              <dd><Chip tone={integrity.hash_valid ? 'green' : 'red'}>{integrity.hash_valid ? 'unchanged' : 'modified'}</Chip></dd>
            </dl>
          </div>
        )}
      </div>
    </Modal>
  )
}
