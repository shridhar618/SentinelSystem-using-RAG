import { format, formatDistanceToNowStrict } from 'date-fns'

export const shortHash = (hash, head = 10, tail = 6) =>
  !hash ? '—' : hash.length <= head + tail + 1 ? hash : `${hash.slice(0, head)}…${hash.slice(-tail)}`

export const relTime = (iso) => {
  if (!iso) return '—'
  try {
    return `${formatDistanceToNowStrict(new Date(iso))} ago`
  } catch {
    return '—'
  }
}

export const fullTime = (iso) => {
  if (!iso) return '—'
  try {
    return format(new Date(iso), 'yyyy-MM-dd HH:mm:ss')
  } catch {
    return iso
  }
}

export const formatNumber = (n) => (typeof n === 'number' ? n.toLocaleString() : '—')

export const eventLabel = (type) => (type || 'ai_request').replace(/_/g, ' ')

const STATUS_TONE = { allowed: 'green', filtered: 'amber', blocked: 'red', success: 'green', failed: 'red' }
const RISK_TONE = { low: 'green', medium: 'amber', high: 'red' }

export const statusTone = (status) => STATUS_TONE[status] || 'blue'
export const riskTone = (risk) => RISK_TONE[risk] || 'blue'

// Which verification step each kind of chain break belongs to.
export const ISSUE_STEP = {
  content_mismatch: 'hashes',
  broken_link: 'links',
  sequence_gap: 'sequence',
  duplicate_sequence: 'sequence',
}

export const ISSUE_LABEL = {
  content_mismatch: 'Content modified',
  broken_link: 'Broken link',
  sequence_gap: 'Missing blocks',
  duplicate_sequence: 'Chain fork',
}
