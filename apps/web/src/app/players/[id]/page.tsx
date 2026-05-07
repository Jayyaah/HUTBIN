import { notFound } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'
import { apiFetch, Player } from '@/lib/api'
import { TrendBadge } from '@/components/TrendBadge'
import { StatBar } from '@/components/StatBar'

const CARD_GRADIENTS: Record<string, string> = {
  BASE:      'from-slate-500 via-slate-700 to-slate-900',
  TOTW:      'from-amber-400 via-yellow-600 to-yellow-900',
  TOTY:      'from-purple-500 via-purple-700 to-indigo-900',
  EVENT:     'from-blue-500 via-blue-700 to-blue-900',
  FLASHBACK: 'from-orange-400 via-orange-600 to-orange-900',
  ICON:      'from-yellow-200 via-yellow-400 to-yellow-700',
  ULTIMATE:  'from-red-500 via-red-700 to-rose-900',
  HERO:      'from-teal-400 via-teal-600 to-cyan-900',
  PROMO:     'from-pink-500 via-pink-700 to-pink-900',
  FANTASY:   'from-violet-500 via-violet-700 to-violet-900',
}

const CARD_TYPE_BADGE: Record<string, string> = {
  BASE:      'bg-slate-600 text-slate-100',
  TOTW:      'bg-yellow-600 text-yellow-100',
  TOTY:      'bg-purple-600 text-purple-100',
  EVENT:     'bg-blue-600 text-blue-100',
  FLASHBACK: 'bg-orange-600 text-orange-100',
  ICON:      'bg-yellow-400 text-yellow-900',
  ULTIMATE:  'bg-red-600 text-red-100',
  HERO:      'bg-teal-600 text-teal-100',
  PROMO:     'bg-pink-600 text-pink-100',
  FANTASY:   'bg-violet-600 text-violet-100',
}

const POSITION_STYLE: Record<string, string> = {
  C:  'border-blue-600/50 bg-blue-900/30 text-blue-300',
  LW: 'border-red-600/50 bg-red-900/30 text-red-300',
  RW: 'border-orange-600/50 bg-orange-900/30 text-orange-300',
  D:  'border-teal-600/50 bg-teal-900/30 text-teal-300',
  G:  'border-yellow-600/50 bg-yellow-900/30 text-yellow-300',
}

const NATIONALITY_FLAG: Record<string, string> = {
  CAN: '🇨🇦', USA: '🇺🇸', RUS: '🇷🇺', SWE: '🇸🇪',
  FIN: '🇫🇮', CZE: '🇨🇿', SVK: '🇸🇰', GER: '🇩🇪',
  SUI: '🇨🇭', AUT: '🇦🇹', DEN: '🇩🇰', NOR: '🇳🇴',
  LAT: '🇱🇻', BLR: '🇧🇾', UKR: '🇺🇦', FRA: '🇫🇷',
}

function formatCoins(n: number) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`
  return n.toString()
}

export default async function PlayerPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const player = await apiFetch<Player>(`/players/${id}`, { next: { revalidate: 300 } }).catch(() => null)
  if (!player) notFound()

  const bestCard = player.cards[0]
  const heroGradient = CARD_GRADIENTS[bestCard?.cardType ?? 'BASE']
  const flag = NATIONALITY_FLAG[player.nationality] ?? ''
  const initials = `${player.firstName[0]}${player.lastName[0]}`
  const posStyle = POSITION_STYLE[player.position] ?? 'border-gray-600 bg-gray-900/30 text-gray-300'

  const bestStats = bestCard ? [
    { label: 'Skating',    value: bestCard.skating    ?? 0, color: '#3b82f6' },
    { label: 'Shooting',   value: bestCard.shooting   ?? 0, color: '#ef4444' },
    { label: 'Passing',    value: bestCard.passing    ?? 0, color: '#10b981' },
    { label: 'Puck Skills',value: bestCard.puckSkills ?? 0, color: '#f59e0b' },
    { label: 'Defense',    value: bestCard.defense    ?? 0, color: '#8b5cf6' },
    { label: 'Physical',   value: bestCard.physical   ?? 0, color: '#6b7280' },
  ] : []

  return (
    <div className="space-y-8">
      {/* Back */}
      <Link href="/players"
        className="inline-flex items-center gap-1.5 text-sm text-gray-400 hover:text-white transition-colors">
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Retour aux joueurs
      </Link>

      {/* Hero */}
      <div className={`relative rounded-3xl overflow-hidden bg-gradient-to-br ${heroGradient} border border-white/5`}>
        {/* Background texture */}
        <div className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: 'radial-gradient(circle at 10% 90%, rgba(255,255,255,0.15) 0%, transparent 40%), radial-gradient(circle at 90% 10%, rgba(255,255,255,0.1) 0%, transparent 40%)'
          }} />

        <div className="relative flex flex-col items-center gap-8 p-8 sm:flex-row sm:items-end">
          {/* Player image / initials */}
          <div className="relative shrink-0">
            <div className="relative h-48 w-40 rounded-2xl overflow-hidden shadow-2xl border border-white/10">
              {bestCard?.imageUrl ? (
                <Image
                  src={bestCard.imageUrl}
                  alt={player.fullName}
                  fill
                  className="object-cover object-top"
                  sizes="160px"
                  priority
                />
              ) : (
                <div className={`h-full w-full bg-gradient-to-b ${heroGradient} flex items-center justify-center`}>
                  <span className="text-6xl font-black tracking-tighter text-white/80">
                    {initials}
                  </span>
                </div>
              )}
            </div>
            {/* OVR badge */}
            {bestCard && (
              <div className="absolute -bottom-3 -right-3 flex h-14 w-14 items-center justify-center
                             rounded-2xl bg-dark-950 border-2 border-white/10 shadow-xl">
                <span className="text-2xl font-black text-white">{bestCard.overall}</span>
              </div>
            )}
          </div>

          {/* Player info */}
          <div className="text-center sm:text-left">
            {flag && (
              <div className="mb-2 text-3xl">{flag}</div>
            )}
            <h1 className="text-4xl font-black tracking-tight text-white sm:text-5xl"
              style={{ textShadow: '0 2px 12px rgba(0,0,0,0.5)' }}>
              {player.firstName}
              <br />
              <span className="opacity-90">{player.lastName}</span>
            </h1>
            <div className="mt-3 flex flex-wrap items-center justify-center gap-2 sm:justify-start">
              <span className={`rounded-xl border px-3 py-1 text-sm font-bold uppercase tracking-wide ${posStyle}`}>
                {player.position}
              </span>
              <span className="rounded-xl bg-white/10 px-3 py-1 text-sm font-semibold text-white/80">
                {player.team.name}
              </span>
              {player.league && (
                <span className="rounded-xl bg-white/10 px-3 py-1 text-sm text-white/60">
                  {player.league.abbrev}
                </span>
              )}
              <span className="rounded-xl bg-white/10 px-3 py-1 text-sm text-white/60">
                {player.handedness === 'LEFT' ? 'Gauche' : 'Droite'}
              </span>
            </div>
            <p className="mt-2 text-sm text-white/40">
              {player.cards.length} carte{player.cards.length > 1 ? 's' : ''} disponible{player.cards.length > 1 ? 's' : ''}
            </p>
          </div>

          {/* Best card stats (only if card has stats) */}
          {bestStats.some(s => s.value > 0) && (
            <div className="hidden xl:block ml-auto min-w-52 rounded-2xl bg-black/20 backdrop-blur-sm p-4 border border-white/10">
              <p className="mb-3 text-[10px] font-bold uppercase tracking-widest text-white/50">
                Stats — {bestCard?.cardType}
              </p>
              <div className="space-y-2">
                {bestStats.map(s => <StatBar key={s.label} {...s} />)}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Mobile stats */}
      {bestStats.some(s => s.value > 0) && (
        <section className="xl:hidden rounded-2xl bg-dark-800 border border-white/5 p-5">
          <h2 className="mb-4 text-xs font-bold uppercase tracking-widest text-gray-400">
            Stats — {bestCard?.cardType}
          </h2>
          <div className="space-y-3">
            {bestStats.map(s => <StatBar key={s.label} {...s} />)}
          </div>
        </section>
      )}

      {/* Cards section */}
      <div>
        <h2 className="mb-4 text-lg font-bold">
          Cartes disponibles
          <span className="ml-2 text-sm font-normal text-gray-500">({player.cards.length})</span>
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {player.cards.map(card => {
            const gradient = CARD_GRADIENTS[card.cardType] ?? CARD_GRADIENTS.BASE
            const typeBadge = CARD_TYPE_BADGE[card.cardType] ?? 'bg-slate-600 text-slate-100'
            return (
              <Link key={card.id} href={`/cards/${card.id}`}
                className="group rounded-2xl bg-dark-800 border border-white/5 overflow-hidden
                           hover:border-brand-500/40 hover:shadow-xl hover:shadow-brand-500/10 transition-all">

                {/* Card header */}
                <div className={`relative flex items-center gap-4 bg-gradient-to-r ${gradient} p-4`}>
                  <div>
                    <div className="text-4xl font-black text-white leading-none"
                      style={{ textShadow: '0 2px 8px rgba(0,0,0,0.6)' }}>
                      {card.overall}
                    </div>
                    <span className={`mt-1 inline-block rounded px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${typeBadge}`}>
                      {card.cardType}
                    </span>
                  </div>
                  {card.version && (
                    <span className="ml-auto text-sm font-medium text-white/60 italic">
                      {card.version}
                    </span>
                  )}
                  <svg className="ml-auto h-4 w-4 text-white/30 group-hover:text-white/60 transition-colors"
                    fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>

                {/* Price info */}
                <div className="p-4">
                  {card.priceStats ? (
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-xs text-gray-500 uppercase tracking-wide">Prix moyen</p>
                          <p className="text-xl font-black text-brand-400">
                            {card.priceStats.priceAvg ? formatCoins(card.priceStats.priceAvg) : '—'}
                            <span className="ml-1 text-sm font-normal text-gray-500">coins</span>
                          </p>
                        </div>
                        <TrendBadge trend={card.priceStats.trend} pct={card.priceStats.trendPct} />
                      </div>
                      <div className="flex gap-4 text-sm">
                        <div>
                          <span className="text-gray-500">Min </span>
                          <span className="font-semibold text-green-400">
                            {card.priceStats.priceMin ? formatCoins(card.priceStats.priceMin) : '—'}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-500">Max </span>
                          <span className="font-semibold text-yellow-400">
                            {card.priceStats.priceMax ? formatCoins(card.priceStats.priceMax) : '—'}
                          </span>
                        </div>
                        <div className="ml-auto text-xs text-gray-600">
                          {card.priceStats.sampleSize} soumissions
                        </div>
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-600 italic">Aucun prix soumis</p>
                  )}

                  {/* Mini stats */}
                  {(card.skating || card.shooting || card.passing) && (
                    <div className="mt-3 flex gap-2 pt-3 border-t border-white/5">
                      {[
                        { label: 'SKA', value: card.skating, color: 'text-blue-400' },
                        { label: 'SHO', value: card.shooting, color: 'text-red-400' },
                        { label: 'PAS', value: card.passing, color: 'text-green-400' },
                        { label: 'CHK', value: card.checking, color: 'text-orange-400' },
                        { label: 'DEF', value: card.defense, color: 'text-purple-400' },
                        { label: 'PHY', value: card.physical, color: 'text-gray-400' },
                      ].map(({ label, value, color }) => value ? (
                        <div key={label} className="flex-1 text-center">
                          <div className={`text-sm font-black ${color}`}>{value}</div>
                          <div className="text-[9px] text-gray-600 uppercase">{label}</div>
                        </div>
                      ) : null)}
                    </div>
                  )}
                </div>
              </Link>
            )
          })}
        </div>
      </div>
    </div>
  )
}
