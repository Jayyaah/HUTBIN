import { Request, Response, NextFunction } from 'express'
import jwt from 'jsonwebtoken'
import { prisma } from '@hutbin/database'
import { AppError } from './error'

export interface AuthRequest extends Request {
  userId?: string
  userRole?: string
}

export async function requireAuth(req: AuthRequest, _res: Response, next: NextFunction) {
  const token = req.headers.authorization?.replace('Bearer ', '')
  if (!token) return next(new AppError(401, 'Authentication required'))

  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET!) as { sub: string }
    const session = await prisma.session.findUnique({
      where: { token },
      include: { user: true },
    })
    if (!session || session.expiresAt < new Date()) {
      return next(new AppError(401, 'Session expired'))
    }
    req.userId = payload.sub
    req.userRole = session.user.role
    next()
  } catch {
    next(new AppError(401, 'Invalid token'))
  }
}

export function requireRole(...roles: string[]) {
  return (req: AuthRequest, _res: Response, next: NextFunction) => {
    if (!req.userRole || !roles.includes(req.userRole)) {
      return next(new AppError(403, 'Insufficient permissions'))
    }
    next()
  }
}
