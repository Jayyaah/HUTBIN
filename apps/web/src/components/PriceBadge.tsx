const VARIANTS = {
  primary: 'bg-brand-500/20 text-brand-400',
  success: 'bg-green-500/20 text-green-400',
  warning: 'bg-yellow-500/20 text-yellow-400',
}

function formatCoins(n?: number) {
  if (!n) return '—'
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`
  return n.toString()
}

export function PriceBadge({ label, value, variant }: {
  label: string; value?: number; variant: keyof typeof VARIANTS
}) {
  return (
    <div className={`rounded-lg p-3 text-center ${VARIANTS[variant]}`}>
      <div className="text-xs font-medium opacity-70">{label}</div>
      <div className="mt-1 text-lg font-black">{formatCoins(value)}</div>
    </div>
  )
}
