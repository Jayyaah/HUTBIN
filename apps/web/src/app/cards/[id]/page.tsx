import { notFound } from 'next/navigation'
import { Suspense } from 'react'
import { apiFetch, Card, PriceEntry } from '@/lib/api'
import { StatBar } from '@/components/StatBar'
import { PriceBadge } from '@/components/PriceBadge'
import { TrendBadge } from '@/components/TrendBadge'
import { PriceChartWrapper } from '@/components/PriceChartWrapper'
import { PriceSubmitForm } from '@/components/PriceSubmitForm'

const CARD_COLORS: Record<string, string> = {
  BASE: 'from-gray-600 to-gray-800',
  TOTW: 'from-yellow-600 to-yellow-900',
  TOTY: 'from-purple-600 to-purple-900',
  EVENT: 'from-blue-600 to-blue-900',
  FLASHBACK: 'from-orange-600 to-orange-900',
  ICON: 'from-yellow-400 to-yellow-700',
  ULTIMATE: 'from-red-600 to-red-900',
  HERO: 'from-teal-600 to-teal-900',
}

export default async function CardPage({
  params,
  searchParams,
}: {
  params: { id: string }
  searchParams: { platform?: string }
}) {
  const platform = searchParams.platform ?? 'PS5'

  const [card, priceHistory] = await Promise.all([
    apiFetch<Card>(`/cards/${params.id}`, { next: { revalidate: 300 } }).catch(() => null),
    apiFetch<PriceEntry[]>(`/cards/${params.id}/prices?platform=${platform}&days=30`, {
      next: { revalidate: 600 },
    }).catch(() => [] as PriceEntry[]),
  ])

  if (!card) notFound()

  const stats = [
    { label: 'Skating',    value: card.skating    ?? 0, color: '#3b82f6' },
    { label: 'Shooting',   value: card.shooting   ?? 0, color: '#ef4444' },
    { label: 'Passing',    value: card.passing    ?? 0, color: '#10b981' },
    { label: 'Puck Skills',value: card.puckSkills ?? 0, color: '#f59e0b' },
    { label: 'Defense',    value: card.defense    ?? 0, color: '#8b5cf6' },
    { label: 'Physical',   value: card.physical   ?? 0, color: '#6b7280' },
  ]

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">

      {/* Colonne gauche — Carte */}
      <div className="space-y-4 lg:col-span-1">
        <div className={`rounded-2xl bg-gradient-to-b ${CARD_COLORS[card.cardType] ?? CARD_COLORS.BASE} p-6 text-center`}>
          <span className="text-xs font-bold uppercase tracking-widest text-white/70">
            {card.cardType}{card.version ? ` · ${card.version}` : ''}
          </span>
          <div className="mt-2 text-7xl font-black">{card.overall}</div>
          <h1 className="mt-3 text-2xl font-bold">{card.player.fullName}</h1>
          <p className="text-white/70">{card.player.position} · {card.player.team.name}</p>
        </div>

        {/* Sélecteur de plateforme */}
        <div className="flex gap-2">
          {['PS5', 'XBOX', 'PC'].map(p => (
            <a key={p} href={`?platform=${p}`}
              className={`flex-1 rounded-lg border py-2 text-center text-sm font-semibold transition-colors ${
                platform === p
                  ? 'border-brand-500 bg-brand-500/20 text-brand-400'
                  : 'border-white/20 text-gray-400 hover:border-white/40'
              }`}>
              {p}
            </a>
          ))}
        </div>
      </div>

      {/* Colonne droite */}
      <div className="space-y-5 lg:col-span-2">

        {/* Prix */}
        <section className="rounded-xl bg-dark-800 p-5">
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-widest text-gray-400">
            Prix {platform}
          </h2>
          <div className="grid grid-cols-3 gap-3">
            <PriceBadge label="Moyen"  value={card.priceStats?.priceAvg} variant="primary" />
            <PriceBadge label="Min"    value={card.priceStats?.priceMin} variant="success" />
            <PriceBadge label="Max"    value={card.priceStats?.priceMax} variant="warning" />
          </div>
          {card.priceStats && (
            <div className="mt-3 flex items-center gap-3 text-sm text-gray-400">
              <TrendBadge trend={card.priceStats.trend} pct={card.priceStats.trendPct} />
              <span>{card.priceStats.sampleSize} soumissions (48h)</span>
            </div>
          )}
        </section>

        {/* Stats */}
        <section className="rounded-xl bg-dark-800 p-5">
          <h2 className="mb-4 text-xs font-semibold uppercase tracking-widest text-gray-400">Stats</h2>
          <div className="space-y-3">
            {stats.map(s => <StatBar key={s.label} {...s} />)}
          </div>
        </section>

        {/* Graphique */}
        {priceHistory.length > 0 && (
          <section className="rounded-xl bg-dark-800 p-5">
            <h2 className="mb-4 text-xs font-semibold uppercase tracking-widest text-gray-400">
              Historique des prix — 30 jours
            </h2>
            <Suspense fallback={<div className="h-48 animate-pulse rounded bg-dark-900" />}>
              <PriceChartWrapper data={priceHistory} />
            </Suspense>
          </section>
        )}

        {/* Soumission */}
        <PriceSubmitForm cardId={card.id} platform={platform} />
      </div>
    </div>
  )
}
