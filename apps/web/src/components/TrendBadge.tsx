import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

export function TrendBadge({ trend, pct }: { trend: string; pct: number }) {
  if (trend === 'UP') return (
    <span className="flex items-center gap-0.5 text-xs font-semibold text-green-400">
      <TrendingUp size={12} />{Math.abs(pct).toFixed(1)}%
    </span>
  )
  if (trend === 'DOWN') return (
    <span className="flex items-center gap-0.5 text-xs font-semibold text-red-400">
      <TrendingDown size={12} />{Math.abs(pct).toFixed(1)}%
    </span>
  )
  return <span className="flex items-center gap-0.5 text-xs text-gray-500"><Minus size={12} /></span>
}
