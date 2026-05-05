import { Router } from 'express'
import { z } from 'zod'
import { prisma } from '@hutbin/database'
import { AppError } from '../middleware/error'
import { requireAuth, requireRole } from '../middleware/auth'

export const cardRouter = Router()

const listSchema = z.object({
  overall_min: z.coerce.number().int().min(1).max(99).optional(),
  overall_max: z.coerce.number().int().min(1).max(99).optional(),
  position: z.enum(['C', 'LW', 'RW', 'D', 'G']).optional(),
  team: z.string().optional(),
  card_type: z.string().optional(),
  platform: z.enum(['PS5', 'XBOX', 'PC']).optional(),
  sort: z.enum(['overall_desc', 'overall_asc', 'price_asc', 'price_desc', 'name_asc']).default('overall_desc'),
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(50).default(20),
})

cardRouter.get('/', async (req, res, next) => {
  try {
    const q = listSchema.parse(req.query)
    const skip = (q.page - 1) * q.limit

    const where: Record<string, unknown> = { isActive: true }
    if (q.overall_min || q.overall_max) {
      where.overall = {
        ...(q.overall_min && { gte: q.overall_min }),
        ...(q.overall_max && { lte: q.overall_max }),
      }
    }
    if (q.position) where.player = { position: q.position }
    if (q.team) where.player = { ...(where.player as object), team: { abbrev: q.team } }
    if (q.card_type) where.cardType = q.card_type.toUpperCase()

    const orderBy = buildOrderBy(q.sort)

    const [total, cards] = await Promise.all([
      prisma.card.count({ where }),
      prisma.card.findMany({
        where,
        include: {
          player: { include: { team: true } },
          priceStats: true,
        },
        orderBy,
        skip,
        take: q.limit,
      }),
    ])

    res.json({
      data: cards,
      meta: { total, page: q.page, limit: q.limit, totalPages: Math.ceil(total / q.limit) },
    })
  } catch (err) {
    next(err)
  }
})

cardRouter.get('/:id', async (req, res, next) => {
  try {
    const card = await prisma.card.findUnique({
      where: { id: req.params.id },
      include: {
        player: { include: { team: true, league: true } },
        priceStats: true,
      },
    })
    if (!card) return next(new AppError(404, 'Card not found'))
    res.json(card)
  } catch (err) {
    next(err)
  }
})

cardRouter.get('/:id/prices', async (req, res, next) => {
  try {
    const { platform = 'PS5', days = '30' } = req.query as Record<string, string>
    const since = new Date(Date.now() - Number(days) * 86_400_000)

    const entries = await prisma.priceEntry.findMany({
      where: {
        cardId: req.params.id,
        platform: platform as 'PS5' | 'XBOX' | 'PC',
        recordedAt: { gte: since },
      },
      orderBy: { recordedAt: 'asc' },
    })
    res.json(entries)
  } catch (err) {
    next(err)
  }
})

const createCardSchema = z.object({
  playerId: z.string(),
  cardType: z.enum(['BASE', 'TOTW', 'TOTY', 'EVENT', 'FLASHBACK', 'ICON', 'ULTIMATE', 'FANTASY', 'PROMO', 'HERO']),
  overall: z.number().int().min(1).max(99),
  version: z.string().optional(),
  imageUrl: z.string().url().optional(),
  skating: z.number().int().min(1).max(99).optional(),
  shooting: z.number().int().min(1).max(99).optional(),
  passing: z.number().int().min(1).max(99).optional(),
  checking: z.number().int().min(1).max(99).optional(),
  defense: z.number().int().min(1).max(99).optional(),
  puckSkills: z.number().int().min(1).max(99).optional(),
  physical: z.number().int().min(1).max(99).optional(),
  detailedStats: z.record(z.number()).optional(),
})

cardRouter.post('/', requireAuth, requireRole('ADMIN', 'MODERATOR'), async (req, res, next) => {
  try {
    const data = createCardSchema.parse(req.body)
    const card = await prisma.card.create({ data, include: { player: true } })
    res.status(201).json(card)
  } catch (err) {
    next(err)
  }
})

cardRouter.put('/:id', requireAuth, requireRole('ADMIN', 'MODERATOR'), async (req, res, next) => {
  try {
    const data = createCardSchema.partial().parse(req.body)
    const card = await prisma.card.update({
      where: { id: req.params.id },
      data,
      include: { player: true },
    })
    res.json(card)
  } catch (err) {
    next(err)
  }
})

function buildOrderBy(sort: string) {
  switch (sort) {
    case 'overall_asc': return { overall: 'asc' as const }
    case 'price_asc': return { priceStats: { priceAvg: 'asc' as const } }
    case 'price_desc': return { priceStats: { priceAvg: 'desc' as const } }
    case 'name_asc': return { player: { fullName: 'asc' as const } }
    default: return { overall: 'desc' as const }
  }
}
