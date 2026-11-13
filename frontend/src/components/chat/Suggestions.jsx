import { useState } from 'react'
import { AlertTriangle, ArrowUpRight, Check, Lock, MinusCircle } from 'lucide-react'

import { SUGGESTION_GROUPS, suggestionAccess } from './chatConfig'

const ACCESS_TAG = {
  allowed: { icon: Check, text: 'Allowed for you', cls: 'text-success bg-success/10 border-success/30' },
  partial: { icon: MinusCircle, text: 'Partial for you', cls: 'text-warn bg-warn/10 border-warn/30' },
  denied: { icon: Lock, text: 'Not in your role', cls: 'text-danger bg-danger/10 border-danger/30' },
}

export default function Suggestions({ permissions, onPick, compact = false }) {
  const [active, setActive] = useState('role')
  const group = SUGGESTION_GROUPS.find(g => g.id === active) || SUGGESTION_GROUPS[0]

  return (
    <div>
      <div className="flex gap-1.5 overflow-x-auto pb-1 -mx-1 px-1" role="tablist" aria-label="Suggested questions">
        {SUGGESTION_GROUPS.map(g => (
          <button
            key={g.id}
            role="tab"
            aria-selected={g.id === active}
            onClick={() => setActive(g.id)}
            className={`whitespace-nowrap px-3 py-1.5 rounded-full text-[11.5px] border transition-colors ${
              g.id === active ? `${g.color.tab} font-semibold` : 'bg-white/5 border-white/8 text-slate-400 hover:text-slate-200'
            }`}
          >
            {g.warning && <AlertTriangle size={10} className="inline mr-1 -mt-0.5" />}
            {g.label}
          </button>
        ))}
      </div>
      <p className={`text-[11px] mt-2 mb-2.5 ${group.warning ? 'text-danger' : 'text-slate-500'}`}>{group.hint}</p>
      <div className={`grid gap-2 ${compact ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-1 md:grid-cols-2'}`}>
        {group.items.map(item => {
          const access = suggestionAccess(item, permissions)
          const tag = access ? ACCESS_TAG[access] : null
          const TagIcon = tag?.icon
          return (
            <button
              key={item.text}
              onClick={() => onPick(item.text)}
              className={`group text-left rounded-xl border border-l-[3px] px-3.5 py-2.5 transition-all hover:-translate-y-0.5 hover:shadow-card ${group.color.edge} ${group.color.card} ${
                group.warning ? 'bg-danger/5 border-danger/20' : 'bg-bg-800/80 border-white/8'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <span className="text-[12.5px] text-slate-200 leading-snug">{item.text}</span>
                <ArrowUpRight size={13} className={`flex-shrink-0 mt-0.5 opacity-60 group-hover:opacity-100 ${group.color.icon}`} />
              </div>
              {tag && (
                <span className={`inline-flex items-center gap-1 mt-1.5 px-1.5 py-0.5 rounded border text-[10px] font-mono ${tag.cls}`}>
                  <TagIcon size={9} />{tag.text}
                </span>
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}
