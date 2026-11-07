import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Activity,
  Blocks,
  Boxes,
  Fingerprint,
  Layers,
  Lock,
  Moon,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  Sun,
} from 'lucide-react'
import './explorer.css'
import { useTheme } from '../../utils/theme'
import { EmptyState, HashText, Panel, StatTile } from './components'
import BlockTable from './BlockTable'
import BlockDetail from './BlockDetail'
import IntegrityPanel from './IntegrityPanel'
import { errorMessage, fetchBlocks, fetchStats, verifyChain } from './api'
import { eventLabel, formatNumber, fullTime, relTime, shortHash } from './format'

const REFRESH_MS = 20000
const EMPTY_FILTERS = { q: '', status: '', risk_level: '', event_type: '', page: 1 }

function useDebounced(value, ms = 300) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), ms)
    return () => clearTimeout(t)
  }, [value, ms])
  return debounced
}

export default function ExplorerPage() {
  const [theme, setTheme] = useTheme()
  const [stats, setStats] = useState({ data: null, error: null })
  const [latest, setLatest] = useState([])
  const [filters, setFilters] = useState(EMPTY_FILTERS)
  const [blocks, setBlocks] = useState({ data: null, loading: true, error: null })
  const [verify, setVerify] = useState({ result: null, running: false, error: null })
  const [openSeq, setOpenSeq] = useState(null)
  const [refreshing, setRefreshing] = useState(false)

  const q = useDebounced(filters.q)
  const query = useMemo(() => ({ ...filters, q, per_page: 20 }), [filters, q])
  const requestId = useRef(0)

  const closeDetail = useCallback(() => setOpenSeq(null), [])

  const toggleTheme = () => setTheme(theme === 'dark' ? 'light' : 'dark')

  const loadStats = useCallback(async () => {
    try {
      const [s, recent] = await Promise.all([fetchStats(), fetchBlocks({ per_page: 6 })])
      setStats({ data: s, error: null })
      setLatest(recent.blocks)
    } catch (err) {
      setStats((prev) => ({ ...prev, error: errorMessage(err, 'Could not load chain stats') }))
    }
  }, [])

  const loadBlocks = useCallback(async (params) => {
    const id = ++requestId.current
    setBlocks((prev) => ({ ...prev, loading: true }))
    try {
      const data = await fetchBlocks(params)
      if (id === requestId.current) setBlocks({ data, loading: false, error: null })
    } catch (err) {
      if (id === requestId.current) setBlocks((prev) => ({ ...prev, loading: false, error: errorMessage(err, 'Could not load blocks') }))
    }
  }, [])

  const runVerify = useCallback(async () => {
    setVerify((prev) => ({ ...prev, running: true, error: null }))
    try {
      const result = await verifyChain()
      setVerify({ result, running: false, error: null })
    } catch (err) {
      setVerify((prev) => ({ ...prev, running: false, error: errorMessage(err, 'Verification failed') }))
    }
  }, [])

  const refresh = useCallback(async () => {
    setRefreshing(true)
    await Promise.all([loadStats(), loadBlocks(query)])
    setRefreshing(false)
  }, [loadStats, loadBlocks, query])

  // Initial load + verify once on open.
  useEffect(() => {
    loadStats()
    runVerify()
  }, [loadStats, runVerify])

  useEffect(() => {
    loadBlocks(query)
  }, [loadBlocks, query])

  // Quiet background refresh while the tab is visible (verification is manual).
  useEffect(() => {
    const t = setInterval(() => {
      if (document.visibilityState === 'visible' && openSeq === null) {
        loadStats()
        loadBlocks(query)
      }
    }, REFRESH_MS)
    return () => clearInterval(t)
  }, [loadStats, loadBlocks, query, openSeq])

  const s = stats.data
  const flagged = useMemo(() => new Set((verify.result?.issues || []).map((i) => i.seq)), [verify.result])

  const integrityValue = verify.running
    ? 'Checking…'
    : verify.result
      ? verify.result.ok ? 'Intact' : `${formatNumber(verify.result.issue_count)} issue${verify.result.issue_count === 1 ? '' : 's'}`
      : verify.error ? 'Error' : '—'
  const integrityTone = verify.running || !verify.result ? undefined : verify.result.ok ? 'ok' : 'bad'

  return (
    <div className="rv" data-theme={theme}>
      <div className="rv-content">
        <div className="workspace">
          {/* ---------- Hero ---------- */}
          <section className="panel hero panel--corners">
            <div className="hero__grid" aria-hidden="true" />
            <div className="hero__text">
              <span className="label">SecureAI · Audit ledger</span>
              <h1 className="hero__title">Blockchain<br />Explorer</h1>
              <p className="hero__lead">
                Every audit event in SecureAI is sealed into a SHA-256 hash chain. Browse the blocks, inspect
                what each one records, and prove nothing has been edited or deleted since it was written.
              </p>
              <div className="hero__actions">
                <button type="button" className="btn btn--primary" onClick={runVerify} disabled={verify.running}>
                  {verify.running ? <span className="spinner" style={{ width: 14, height: 14 }} /> : <ShieldCheck className="icon" />}
                  {verify.running ? 'Verifying chain' : 'Verify chain'}
                </button>
                <button type="button" className="btn" onClick={refresh} disabled={refreshing}>
                  <RefreshCw className="icon" style={refreshing ? { animation: 'rv-spin 0.8s linear infinite' } : undefined} />
                  Refresh
                </button>
                <button
                  type="button"
                  className="btn btn--ghost btn--icon"
                  onClick={toggleTheme}
                  aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
                  title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
                >
                  {theme === 'dark' ? <Sun className="icon" /> : <Moon className="icon" />}
                </button>
              </div>
              <p className="hero__disclaimer">
                <Lock className="icon" aria-hidden="true" />
                <span>
                  Tamper-evident, not tamper-proof: anyone with direct database write access could rebuild the chain.
                  Export the head hash regularly to anchor it.
                </span>
              </p>
            </div>
            <div className="hero__visual" aria-hidden="true">
              <div className="hero__reticle">
                <span className="hero__ring" />
                <span className="hero__ring hero__ring--2" />
                <Blocks className="hero__mark" strokeWidth={1.6} />
              </div>
              <ol className="hero__flow">
                <li><span>01</span>Audit event recorded</li>
                <li><span>02</span>Hashed with the previous block</li>
                <li><span>03</span>Sealed into the chain</li>
                <li><span>04</span>Recomputed on every verify</li>
              </ol>
            </div>
          </section>

          {/* ---------- Stats ---------- */}
          <div className="stats">
            <StatTile
              icon={Layers}
              label="Chain height"
              loading={!s && !stats.error}
              value={s ? `#${formatNumber(s.height)}` : '—'}
              sub={s?.genesis_at ? `since ${fullTime(s.genesis_at).slice(0, 10)}` : 'no blocks yet'}
            />
            <StatTile
              icon={Activity}
              label="Blocks · 24h"
              loading={!s && !stats.error}
              value={s ? formatNumber(s.blocks_24h) : '—'}
              sub={s?.head ? `last ${relTime(s.head.timestamp)}` : ' '}
            />
            <StatTile
              icon={ShieldAlert}
              label="High-risk blocks"
              loading={!s && !stats.error}
              value={s ? formatNumber(s.high_risk) : '—'}
              sub={s ? `of ${formatNumber(s.blocks)} total` : ' '}
            />
            <StatTile
              icon={ShieldCheck}
              label="Integrity"
              value={integrityValue}
              tone={integrityTone}
              sub={verify.result ? `${formatNumber(verify.result.checked)} blocks checked` : 'run a verification'}
            />
          </div>

          {stats.error && (
            <div className="alert alert--error">
              <ShieldAlert className="icon" />
              <span><strong>Explorer unavailable.</strong> {stats.error}</span>
            </div>
          )}

          {/* ---------- Main grid ---------- */}
          <div className="workspace__grid">
            <BlockTable
              data={blocks.data}
              loading={blocks.loading}
              error={blocks.error}
              filters={filters}
              onFilters={setFilters}
              onOpen={setOpenSeq}
              flagged={flagged}
            />

            <div className="workspace__side">
              <IntegrityPanel
                result={verify.result}
                running={verify.running}
                error={verify.error}
                onVerify={runVerify}
                onOpen={setOpenSeq}
              />

              <Panel title="Chain head">
                {s?.head ? (
                  <dl className="kv">
                    <dt>Block</dt>
                    <dd className="mono">#{s.head.seq}</dd>
                    <dt>Hash</dt>
                    <dd><HashText hash={s.head.hash} full label="head hash" /></dd>
                    <dt>Sealed</dt>
                    <dd className="mono">{fullTime(s.head.timestamp)} UTC</dd>
                    <dt>Algorithm</dt>
                    <dd className="mono">{s.algorithm}</dd>
                    <dt>Genesis</dt>
                    <dd className="mono faint">{shortHash(s.genesis_hash, 8, 4)}</dd>
                  </dl>
                ) : (
                  <EmptyState compact icon={Fingerprint} title="No head yet" text="The first audit event becomes block #1." />
                )}
              </Panel>

              <Panel title="Latest blocks">
                {latest.length === 0 ? (
                  <EmptyState compact icon={Boxes} title="Waiting for blocks" />
                ) : (
                  <ul className="timeline">
                    {latest.map((b, i) => (
                      <li key={b.seq}>
                        <button
                          type="button"
                          className={`timeline__item ${i === 0 ? 'is-head' : ''} ${b.is_high_risk ? 'is-risk' : ''}`}
                          onClick={() => setOpenSeq(b.seq)}
                        >
                          <span className="timeline__node">
                            {b.is_high_risk ? <ShieldAlert className="icon" /> : <Blocks className="icon" />}
                          </span>
                          <span className="timeline__msg">
                            <strong className="mono">#{b.seq}</strong> · {eventLabel(b.event_type)} by {b.username}
                          </span>
                          <span className="timeline__time">{relTime(b.timestamp)}</span>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </Panel>
            </div>
          </div>
        </div>
      </div>

      {/* Outside .rv-content: its container query would trap position:fixed. */}
      {openSeq !== null && (
        <BlockDetail seq={openSeq} onNavigate={setOpenSeq} onClose={closeDetail} />
      )}
    </div>
  )
}
