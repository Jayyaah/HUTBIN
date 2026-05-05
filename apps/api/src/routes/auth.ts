import { Router } from 'express'
import { z } from 'zod'
import bcrypt from 'bcryptjs'
import jwt from 'jsonwebtoken'
import { prisma } from '@hutbin/database'
import { AppError } from '../middleware/error'
import { requireAuth, AuthRequest } from '../middleware/auth'

export const authRouter = Router()

const registerSchema = z.object({
  email: z.string().email(),
  username: z.string().min(3).max(20).regex(/^[a-zA-Z0-9_]+$/),
  password: z.string().min(8),
})

authRouter.post('/register', async (req, res, next) => {
  try {
    const { email, username, password } = registerSchema.parse(req.body)

    const exists = await prisma.user.findFirst({
      where: { OR: [{ email }, { username }] },
    })
    if (exists) return next(new AppError(409, 'Email or username already taken'))

    const passwordHash = await bcrypt.hash(password, 12)
    const user = await prisma.user.create({
      data: { email, username, passwordHash },
      select: { id: true, email: true, username: true, role: true },
    })

    res.status(201).json(user)
  } catch (err) {
    next(err)
  }
})

authRouter.post('/login', async (req, res, next) => {
  try {
    const { email, password } = z.object({
      email: z.string().email(),
      password: z.string(),
    }).parse(req.body)

    const user = await prisma.user.findUnique({ where: { email } })
    if (!user?.passwordHash) return next(new AppError(401, 'Invalid credentials'))

    const valid = await bcrypt.compare(password, user.passwordHash)
    if (!valid) return next(new AppError(401, 'Invalid credentials'))

    const token = jwt.sign({ sub: user.id }, process.env.JWT_SECRET!, { expiresIn: '7d' })

    await prisma.session.create({
      data: {
        userId: user.id,
        token,
        expiresAt: new Date(Date.now() + 7 * 86_400_000),
      },
    })

    res.json({
      token,
      user: { id: user.id, email: user.email, username: user.username, role: user.role },
    })
  } catch (err) {
    next(err)
  }
})

authRouter.post('/logout', requireAuth, async (req: AuthRequest, res, next) => {
  try {
    const token = req.headers.authorization?.replace('Bearer ', '')!
    await prisma.session.delete({ where: { token } })
    res.json({ message: 'Logged out' })
  } catch (err) {
    next(err)
  }
})

authRouter.get('/me', requireAuth, async (req: AuthRequest, res, next) => {
  try {
    const user = await prisma.user.findUnique({
      where: { id: req.userId },
      select: { id: true, email: true, username: true, role: true, reliabilityScore: true, submissionCount: true, acceptedCount: true },
    })
    res.json(user)
  } catch (err) {
    next(err)
  }
})
