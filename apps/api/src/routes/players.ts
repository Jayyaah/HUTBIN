import { Router } from 'express'
import { prisma } from '@hutbin/database'
import { AppError } from '../middleware/error'

export const playerRouter = Router()

playerRouter.get('/', async (req, res, next) => {
  try {
    const { page = '1', limit = '20', team, position, q } = req.query as Record<string, string>
    const skip = (Number(page) - 1) * Number(limit)

    const where: Record<string, unknown> = {}
    if (team) where.team = { abbrev: team }
    if (position) where.position = position.toUpperCase()
    if (q && q.length >= 2) where.fullName = { contains: q, mode: 'insensitive' }

    const [total, players] = await Promise.all([
      prisma.player.count({ where }),
      prisma.player.findMany({
        where,
        include: {
          team: true,
          cards: {
            where: { isActive: true },
            select: { id: true, overall: true, cardType: true, imageUrl: true },
            orderBy: { overall: 'desc' },
          },
        },
        skip,
        take: Number(limit),
        orderBy: { fullName: 'asc' },
      }),
    ])

    res.json({ data: players, meta: { total, page: Number(page), limit: Number(limit) } })
  } catch (err) {
    next(err)
  }
})

playerRouter.get('/search', async (req, res, next) => {
  try {
    const { q = '' } = req.query as Record<string, string>
    if (q.length < 2) return res.json([])

    const players = await prisma.player.findMany({
      where: { fullName: { contains: q, mode: 'insensitive' } },
      include: {
        team: true,
        cards: { where: { isActive: true }, orderBy: { overall: 'desc' }, take: 1 },
      },
      take: 10,
    })
    res.json(players)
  } catch (err) {
    next(err)
  }
})

playerRouter.get('/:id', async (req, res, next) => {
  try {
    const player = await prisma.player.findUnique({
      where: { id: req.params.id },
      include: {
        team: true,
        league: true,
        cards: {
          where: { isActive: true },
          include: { priceStats: true },
          orderBy: { overall: 'desc' },
        },
      },
    })
    if (!player) return next(new AppError(404, 'Player not found'))
    res.json(player)
  } catch (err) {
    next(err)
  }
})
