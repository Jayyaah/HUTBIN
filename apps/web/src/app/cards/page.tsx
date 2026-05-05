import { apiFetch, CardListResponse } from '@/lib/api'
import { CardGrid } from '@/components/CardGrid'
import { CardFilters } from '@/components/CardFilters'

type SearchParams = {
  overall_min?: string; overall_max?: string
  position?: string; team?: string; card_type?: string
  platform?: string; sort?: string; page?: string
}

export default async function CardsPage({ searchParams }: { searchParams: SearchParams }) {
  const params = new URLSearchParams()
  Object.entries(searchParams).forEach(([k, v]) => { if (v) params.set(k, v) })

  const data = await apiFetch<CardListResponse>(`/cards?${params.toString()}`, {
    next: { revalidate: 60 },
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Cards</h1>
        <span className="text-sm text-gray-400">{data.meta.total} cards</span>
      </div>
      <CardFilters current={searchParams} />
      <CardGrid cards={data.data} />
      <Pagination meta={data.meta} current={searchParams} />
    </div>
  )
}

function Pagination({ meta, current }: { meta: CardListResponse['meta']; current: SearchParams }) {
  const page = meta.page
  const params = (p: number) => {
    const q = new URLSearchParams(current as Record<string, string>)
    q.set('page', String(p))
    return `/cards?${q.toString()}`
  }
  return (
    <div className="flex items-center justify-center gap-2 py-4">
      {page > 1 && (
        <a href={params(page - 1)} className="rounded-md border border-white/20 px-4 py-2 text-sm hover:border-white/40">
          Prev
        </a>
      )}
      <span className="text-sm text-gray-400">Page {page} / {meta.totalPages}</span>
      {page < meta.totalPages && (
        <a href={params(page + 1)} className="rounded-md border border-white/20 px-4 py-2 text-sm hover:border-white/40">
          Next
        </a>
      )}
    </div>
  )
}
