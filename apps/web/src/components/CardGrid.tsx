import Link from 'next/link'
import { Card } from '@/lib/api'
import { TrendBadge } from './TrendBadge'

const CARD_COLORS: Record<string, string> = {
  BASE: 'from-gray-700 to-gray-800',
  TOTW: 'from-yellow-700 to-yellow-900',
  TOTY: 'from-purple-700 to-purple-900',
  EVENT: 'from-blue-700 to-blue-900',
  FLASHBACK: 'from-orange-700 to-orange-900',
  ICON: 'from-yellow-500 to-yellow-700',
  ULTIMATE: 'from-red-700 to-red-900',
  HERO: 'from-teal-700 to-teal-900',
}

export function CardGrid({ cards }: { cards: Card[] }) {
  if (cards.length === 0) {
    return <p className="py-16 text-center text-gray-500">No cards found.</p>
  }

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
      {cards.map(card => (
        <Link key={card.id} href={`/cards/${card.id}`}
          className="group rounded-xl bg-dark-800 overflow-hidden hover:ring-2 hover:ring-brand-500 transition-all">
          <div className={`bg-gradient-to-b ${CARD_COLORS[card.cardType] ?? CARD_COLORS.BASE} p-4 text-center`}>
            <div className="text-3xl font-black">{card.overall}</div>
            <div className="text-xs font-bold uppercase tracking-widest opacity-80 mt-0.5">{card.cardType}</div>
          </div>
          <div className="p-3">
            <p className="font-semibold text-sm truncate">{card.player.fullName}</p>
            <p className="text-xs text-gray-400">{card.player.position} · {card.player.team.abbrev}</p>
            <div className="mt-2 flex items-center justify-between">
              <span className="text-sm font-bold text-brand-500">
                {card.priceStats?.priceAvg ? formatCoins(card.priceStats.priceAvg) : '—'}
              </span>
              {card.priceStats && <TrendBadge trend={card.priceStats.trend} pct={card.priceStats.trendPct} />}
            </div>
          </div>
        </Link>
      ))}
    </div>
  )
}

function formatCoins(n: number) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`
  return n.toString()
}
