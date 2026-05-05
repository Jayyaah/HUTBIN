import { Router } from 'express'
import { z } from 'zod'
import { prisma, Platform, Trend } from '@hutbin/database'
import rateLimit from 'express-rate-limit'
import { AppError } from '../middleware/error'
import { requireAuth, AuthRequest } from '../middleware/auth'

export const priceRouter = Router()

const submitLimiter = rateLimit({
  windowMs: 60 * 60 * 1000,
  max: 5,
  message: { error: 'Too many price submissions, try again later' },
  keyGenerator: (req) => (req as AuthRequest).userId ?? req.ip!,
})

const submitSchema = z.object({
  cardId: z.string(),
  price: z.number().int().min(100).max(10_000_000),
  platform: z.enum(['PS5', 'XBOX', 'PC']),
})

priceRouter.post('/', requireAuth, submitLimiter, async (req: AuthRequest, res, next) => {
  try {
    const { cardId, price, platform } = submitSchema.parse(req.body)
    const userId = req.userId!

    const card = await prisma.card.findUnique({ where: { id: cardId } })
    if (!card) return next(new AppError(404, 'Card not found'))

    // Vérification anti-spam : écart > 50% de la médiane → rejeté
    const stats = await prisma.priceStats.findUnique({ where: { cardId } })
    if (stats?.priceMedian) {
      const deviation = Math.abs(price - stats.priceMedian) / stats.priceMedian
      if (deviation > 0.5) {
        return next(new AppError(422, `Price deviates too much from current median (${stats.priceMedian.toLocaleString()} coins)`))
      }
    }

    const user = await prisma.user.findUnique({ where: { id: userId } })!
    const confidence = Math.min((user!.reliabilityScore * (1 + user!.submissionCount / 100)), 1)

    const submission = await prisma.priceSubmission.create({
      data: { cardId, userId, price, platform, confidence },
    })

    // Incrémente le compteur de soumissions
    await prisma.user.update({
      where: { id: userId },
      data: { submissionCount: { increment: 1 } },
    })

    // Recalcul stats
    await recalcStats(cardId, platform as Platform)

    res.status(201).json(submission)
  } catch (err) {
    next(err)
  }
})

async function recalcStats(cardId: string, platform: Platform) {
  const since = new Date(Date.now() - 48 * 3600_000)

  const submissions = await prisma.priceSubmission.findMany({
    where: { cardId, platform, isValid: true, createdAt: { gte: since } },
    orderBy: { createdAt: 'desc' },
  })

  if (submissions.length === 0) return

  const prices = submissions.map(s => s.price)
  const totalWeight = submissions.reduce((s, e) => s + e.confidence, 0)
  const weightedAvg = Math.round(
    submissions.reduce((s, e) => s + e.price * e.confidence, 0) / totalWeight
  )

  const sorted = [...prices].sort((a, b) => a - b)
  const median = sorted[Math.floor(sorted.length / 2)]

  const prev = await prisma.priceEntry.findFirst({
    where: { cardId, platform },
    orderBy: { recordedAt: 'desc' },
  })

  const trendPct = prev ? +((weightedAvg - prev.priceAvg) / prev.priceAvg * 100).toFixed(1) : 0
  const trend: Trend = Math.abs(trendPct) < 2 ? 'STABLE' : trendPct > 0 ? 'UP' : 'DOWN'

  await prisma.priceStats.upsert({
    where: { cardId },
    create: {
      cardId, platform, priceAvg: weightedAvg,
      priceMin: Math.min(...prices), priceMax: Math.max(...prices),
      priceMedian: median, trend, trendPct, sampleSize: submissions.length,
    },
    update: {
      priceAvg: weightedAvg, priceMin: Math.min(...prices), priceMax: Math.max(...prices),
      priceMedian: median, trend, trendPct, sampleSize: submissions.length,
    },
  })

  // Archive si > 2h depuis dernier snapshot
  const lastEntry = await prisma.priceEntry.findFirst({
    where: { cardId, platform },
    orderBy: { recordedAt: 'desc' },
  })

  const twoHoursAgo = new Date(Date.now() - 7_200_000)
  if (!lastEntry || lastEntry.recordedAt < twoHoursAgo) {
    await prisma.priceEntry.create({
      data: {
        cardId, platform, priceAvg: weightedAvg,
        priceMin: Math.min(...prices), priceMax: Math.max(...prices),
        sampleSize: submissions.length,
      },
    })
  }
}
