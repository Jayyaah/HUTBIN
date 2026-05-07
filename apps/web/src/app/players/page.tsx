import Link from 'next/link'
import Image from 'next/image'
import { apiFetch, PlayerListResponse, Player } from '@/lib/api'

type SearchParams = {
  position?: string
  team?: string
  q?: string
  page?: string
}

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
  BASE:      'bg-slate-600 text-slate-200',
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
  C:  'border-blue-600/60 bg-blue-950/60 text-blue-300',
  LW: 'border-red-600/60 bg-red-950/60 text-red-300',
  RW: 'border-orange-600/60 bg-orange-950/60 text-orange-300',
  D:  'border-teal-600/60 bg-teal-950/60 text-teal-300',
  G:  'border-yellow-600/60 bg-yellow-950/60 text-yellow-300',
}

const NATIONALITY_FLAG: Record<string, string> = {
  CAN: '🇨🇦', USA: '🇺🇸', RUS: '🇷🇺', SWE: '🇸🇪',
  FIN: '🇫🇮', CZE: '🇨🇿', SVK: '🇸🇰', GER: '🇩🇪',
  SUI: '🇨🇭', AUT: '🇦🇹', DEN: '🇩🇰', NOR: '🇳🇴',
  LAT: '🇱🇻', BLR: '🇧🇾', UKR: '🇺🇦', FRA: '🇫🇷',
}

const POSITIONS = ['C', 'LW', 'RW', 'D', 'G']

export default async function PlayersPage({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const sp = await searchParams
  const params = new URLSearchParams()
  if (sp.position) params.set('position', sp.position)
  if (sp.team) params.set('team', sp.team)
  if (sp.q) params.set('q', sp.q)
  if (sp.page) params.set('page', sp.page)
  params.set('limit', '24')

  const data = await apiFetch<PlayerListResponse>(`/players?${params.toString()}`, {
    next: { revalidate: 60 },
  })

  const totalPages = Math.ceil(data.meta.total / 24)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-black tracking-tight">
            HUT<span className="text-brand-500">Players</span>
          </h1>
          <p className="mt-1 text-sm text-gray-400">{data.meta.total} joueurs dans la base</p>
        </div>
      </div>

      {/* Filters bar */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Search */}
        <form method="GET" action="/players" className="flex-1 min-w-48 max-w-xs">
          {sp.position && <input type="hidden" name="position" value={sp.position} />}
          {sp.team && <input type="hidden" name="team" value={sp.team} />}
          <div className="relative">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500"
              fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              name="q"
              defaultValue={sp.q}
              placeholder="Rechercher un joueur..."
              className="w-full rounded-xl bg-dark-800 border border-white/10 pl-9 pr-4 py-2.5 text-sm
                         placeholder-gray-500 focus:border-brand-500/60 focus:outline-none focus:ring-1 focus:ring-brand-500/30 transition"
            />
          </div>
        </form>

        {/* Position pills */}
        <div className="flex gap-1.5">
          <Link
            href={buildHref(sp, { position: undefined, page: undefined })}
            className={`rounded-xl px-3.5 py-2 text-sm font-semibold transition-colors ${
              !sp.position
                ? 'bg-brand-600 text-white shadow-lg shadow-brand-600/20'
                : 'bg-dark-800 text-gray-400 border border-white/10 hover:border-white/20 hover:text-white'
            }`}
          >
            Tous
          </Link>
          {POSITIONS.map(pos => (
            <Link
              key={pos}
              href={buildHref(sp, { position: pos, page: undefined })}
              className={`rounded-xl px-3.5 py-2 text-sm font-bold transition-colors ${
                sp.position === pos
                  ? 'bg-brand-600 text-white shadow-lg shadow-brand-600/20'
                  : 'bg-dark-800 text-gray-400 border border-white/10 hover:border-white/20 hover:text-white'
              }`}
            >
              {pos}
            </Link>
          ))}
        </div>
      </div>

      {/* Grid */}
      {data.data.length === 0 ? (
        <div className="py-20 text-center">
          <p className="text-2xl font-bold text-gray-600">Aucun joueur trouvé</p>
          <p className="mt-2 text-gray-500 text-sm">Essayez de modifier vos filtres.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
          {data.data.map(player => (
            <PlayerCard key={player.id} player={player} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 py-4">
          {data.meta.page > 1 && (
            <a href={buildHref(sp, { page: String(data.meta.page - 1) })}
              className="rounded-lg border border-white/20 px-4 py-2 text-sm hover:border-white/40 transition-colors">
              ← Précédent
            </a>
          )}
          <span className="text-sm text-gray-400">
            Page {data.meta.page} / {totalPages}
          </span>
          {data.meta.page < totalPages && (
            <a href={buildHref(sp, { page: String(data.meta.page + 1) })}
              className="rounded-lg border border-white/20 px-4 py-2 text-sm hover:border-white/40 transition-colors">
              Suivant →
            </a>
          )}
        </div>
      )}
    </div>
  )
}

function PlayerCard({ player }: { player: Player }) {
  const bestCard = player.cards[0]
  const gradient = CARD_GRADIENTS[bestCard?.cardType ?? 'BASE']
  const typeBadge = CARD_TYPE_BADGE[bestCard?.cardType ?? 'BASE'] ?? 'bg-slate-600 text-slate-200'
  const posStyle = POSITION_STYLE[player.position] ?? 'border-gray-600 bg-gray-900 text-gray-300'
  const flag = NATIONALITY_FLAG[player.nationality] ?? ''
  const initials = `${player.firstName[0]}${player.lastName[0]}`

  return (
    <Link href={`/players/${player.id}`} className="group block">
      <div className="rounded-2xl overflow-hidden bg-dark-800 border border-white/5
                      hover:border-brand-500/40 hover:shadow-2xl hover:shadow-brand-500/10
                      hover:-translate-y-1 transition-all duration-200">

        {/* Portrait area */}
        <div className={`relative h-44 bg-gradient-to-b ${gradient}`}>
          {/* Subtle texture */}
          <div className="absolute inset-0"
            style={{
              backgroundImage: 'radial-gradient(circle at 20% 80%, rgba(255,255,255,0.03) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(255,255,255,0.05) 0%, transparent 50%)'
            }} />

          {/* Card image or initials */}
          {bestCard?.imageUrl ? (
            <Image
              src={bestCard.imageUrl}
              alt={player.fullName}
              fill
              className="object-cover object-top"
              sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 16vw"
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="flex h-20 w-20 items-center justify-center rounded-full
                             bg-black/30 backdrop-blur-sm border-2 border-white/20 shadow-2xl">
                <span className="text-3xl font-black tracking-tighter text-white">
                  {initials}
                </span>
              </div>
            </div>
          )}

          {/* OVR + type badge — top left */}
          {bestCard && (
            <div className="absolute top-2.5 left-2.5 drop-shadow-xl">
              <div className="text-3xl font-black leading-none text-white"
                style={{ textShadow: '0 2px 8px rgba(0,0,0,0.8)' }}>
                {bestCard.overall}
              </div>
              <span className={`mt-0.5 inline-block rounded px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider ${typeBadge}`}>
                {bestCard.cardType}
              </span>
            </div>
          )}

          {/* Nationality flag — top right */}
          {flag && (
            <div className="absolute top-2.5 right-2.5 text-xl drop-shadow-md">
              {flag}
            </div>
          )}

          {/* Card count — bottom right */}
          {player.cards.length > 1 && (
            <div className="absolute bottom-2 right-2.5 rounded-full bg-black/50 backdrop-blur-sm
                           px-2 py-0.5 text-[10px] font-medium text-white/70">
              {player.cards.length} cartes
            </div>
          )}

          {/* Bottom gradient fade */}
          <div className="absolute bottom-0 inset-x-0 h-8 bg-gradient-to-t from-dark-800 to-transparent" />
        </div>

        {/* Info */}
        <div className="px-3 pb-3 pt-1">
          <p className="font-bold text-sm text-white truncate group-hover:text-brand-400 transition-colors leading-snug">
            {player.fullName}
          </p>
          <div className="mt-1.5 flex items-center gap-1.5">
            <span className={`rounded-md border px-1.5 py-0.5 text-[10px] font-black uppercase tracking-wide ${posStyle}`}>
              {player.position}
            </span>
            <span className="text-xs text-gray-500 font-medium">{player.team.abbrev}</span>
            <span className="ml-auto text-[10px] text-gray-600 font-medium">
              {player.handedness === 'LEFT' ? 'L' : 'R'}
            </span>
          </div>
        </div>
      </div>
    </Link>
  )
}

function buildHref(current: SearchParams, overrides: Partial<SearchParams>): string {
  const merged = { ...current, ...overrides }
  const q = new URLSearchParams()
  if (merged.position) q.set('position', merged.position)
  if (merged.team) q.set('team', merged.team)
  if (merged.q) q.set('q', merged.q)
  if (merged.page) q.set('page', merged.page)
  const qs = q.toString()
  return `/players${qs ? `?${qs}` : ''}`
}
