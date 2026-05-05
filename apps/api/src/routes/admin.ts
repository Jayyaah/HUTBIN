import { Router } from 'express'
import { prisma } from '@hutbin/database'
import { requireAuth, requireRole } from '../middleware/auth'

export const adminRouter = Router()

adminRouter.use(requireAuth, requireRole('ADMIN', 'MODERATOR'))

adminRouter.get('/stats', async (_req, res, next) => {
  try {
    const [cards, players, users, submissionsToday] = await Promise.all([
      prisma.card.count(),
      prisma.player.count(),
      prisma.user.count(),
      prisma.priceSubmission.count({
        where: { createdAt: { gte: new Date(new Date().setHours(0, 0, 0, 0)) } },
      }),
    ])
    res.json({ cards, players, users, submissionsToday })
  } catch (err) {
    next(err)
  }
})

adminRouter.get('/prices/pending', async (_req, res, next) => {
  try {
    const submissions = await prisma.priceSubmission.findMany({
      where: { isValid: true },
      include: { card: { include: { player: true } }, user: { select: { username: true, reliabilityScore: true } } },
      orderBy: { createdAt: 'desc' },
      take: 50,
    })
    res.json(submissions)
  } catch (err) {
    next(err)
  }
})

adminRouter.put('/prices/:id/reject', async (req, res, next) => {
  try {
    const submission = await prisma.priceSubmission.update({
      where: { id: req.params.id },
      data: { isValid: false },
    })

    // Pénalise légèrement le score de fiabilité
    await prisma.user.update({
      where: { id: submission.userId },
      data: { reliabilityScore: { decrement: 0.05 } },
    })

    res.json(submission)
  } catch (err) {
    next(err)
  }
})

adminRouter.put('/prices/:id/approve', async (req, res, next) => {
  try {
    const submission = await prisma.priceSubmission.findUnique({
      where: { id: req.params.id },
    })
    if (!submission) return res.status(404).json({ error: 'Not found' })

    // Augmente le score de fiabilité
    await prisma.user.update({
      where: { id: submission.userId },
      data: {
        reliabilityScore: { increment: 0.02 },
        acceptedCount: { increment: 1 },
      },
    })

    res.json({ message: 'Approved' })
  } catch (err) {
    next(err)
  }
})
