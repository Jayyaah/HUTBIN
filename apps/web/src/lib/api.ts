const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:4000'

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}/api/v1${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'Unknown error' }))
    throw new Error(err.error ?? `HTTP ${res.status}`)
  }
  return res.json()
}

export type Card = {
  id: string
  cardType: string
  overall: number
  version?: string
  imageUrl?: string
  skating?: number; shooting?: number; passing?: number
  checking?: number; defense?: number; puckSkills?: number; physical?: number
  detailedStats?: Record<string, number>
  player: { id: string; fullName: string; position: string; team: { name: string; abbrev: string } }
  priceStats?: { priceAvg?: number; priceMin?: number; priceMax?: number; trend: string; trendPct: number; sampleSize: number }
}

export type PriceEntry = {
  id: string; priceAvg: number; priceMin: number; priceMax: number
  sampleSize: number; recordedAt: string
}

export type CardListResponse = {
  data: Card[]
  meta: { total: number; page: number; limit: number; totalPages: number }
}

export type PlayerCard = {
  id: string
  overall: number
  cardType: string
  version?: string
  imageUrl?: string
  skating?: number; shooting?: number; passing?: number
  checking?: number; defense?: number; puckSkills?: number; physical?: number
  priceStats?: { priceAvg?: number; priceMin?: number; priceMax?: number; trend: string; trendPct: number; sampleSize: number }
}

export type Player = {
  id: string
  firstName: string
  lastName: string
  fullName: string
  position: string
  nationality: string
  handedness: string
  birthDate?: string
  team: { id: string; name: string; abbrev: string }
  league?: { id: string; name: string; abbrev: string }
  cards: PlayerCard[]
}

export type PlayerListResponse = {
  data: Player[]
  meta: { total: number; page: number; limit: number }
}
