'use client'
import { useRouter } from 'next/navigation'
import { useCallback } from 'react'

const POSITIONS = ['C', 'LW', 'RW', 'D', 'G']
const CARD_TYPES = ['BASE', 'TOTW', 'TOTY', 'EVENT', 'FLASHBACK', 'ICON', 'ULTIMATE', 'HERO']
const SORT_OPTIONS = [
  { value: 'overall_desc', label: 'Overall ↓' },
  { value: 'overall_asc', label: 'Overall ↑' },
  { value: 'price_desc', label: 'Price ↓' },
  { value: 'price_asc', label: 'Price ↑' },
  { value: 'name_asc', label: 'Name A-Z' },
]

type Filters = {
  position?: string; card_type?: string; sort?: string
  overall_min?: string; overall_max?: string; team?: string
}

export function CardFilters({ current }: { current: Filters }) {
  const router = useRouter()

  const update = useCallback((key: string, value: string) => {
    const params = new URLSearchParams(current as Record<string, string>)
    if (value) params.set(key, value)
    else params.delete(key)
    params.delete('page')
    router.push(`/cards?${params.toString()}`)
  }, [current, router])

  const selectCls = "rounded-md border border-white/20 bg-dark-800 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-brand-500"

  return (
    <div className="flex flex-wrap items-center gap-3">
      <select className={selectCls} value={current.position ?? ''} onChange={e => update('position', e.target.value)}>
        <option value="">All Positions</option>
        {POSITIONS.map(p => <option key={p} value={p}>{p}</option>)}
      </select>

      <select className={selectCls} value={current.card_type ?? ''} onChange={e => update('card_type', e.target.value)}>
        <option value="">All Types</option>
        {CARD_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
      </select>

      <div className="flex items-center gap-2">
        <input type="number" placeholder="OVR min" min={1} max={99}
          className={`${selectCls} w-24`}
          value={current.overall_min ?? ''}
          onChange={e => update('overall_min', e.target.value)} />
        <span className="text-gray-500">—</span>
        <input type="number" placeholder="OVR max" min={1} max={99}
          className={`${selectCls} w-24`}
          value={current.overall_max ?? ''}
          onChange={e => update('overall_max', e.target.value)} />
      </div>

      <input type="text" placeholder="Team (e.g. EDM)"
        className={`${selectCls} w-28`}
        value={current.team ?? ''}
        onChange={e => update('team', e.target.value.toUpperCase())} />

      <select className={selectCls} value={current.sort ?? 'overall_desc'} onChange={e => update('sort', e.target.value)}>
        {SORT_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  )
}
