import express from 'express'
import cors from 'cors'
import helmet from 'helmet'
import morgan from 'morgan'
import { cardRouter } from './routes/cards'
import { playerRouter } from './routes/players'
import { priceRouter } from './routes/prices'
import { authRouter } from './routes/auth'
import { adminRouter } from './routes/admin'
import { errorHandler } from './middleware/error'

const app = express()
const PORT = process.env.PORT ?? 4000

app.use(helmet())
app.use(cors({ origin: process.env.FRONTEND_URL ?? 'http://localhost:3000' }))
app.use(morgan('dev'))
app.use(express.json())

app.get('/health', (_, res) => res.json({ status: 'ok', ts: new Date().toISOString() }))

app.use('/api/v1/cards', cardRouter)
app.use('/api/v1/players', playerRouter)
app.use('/api/v1/prices', priceRouter)
app.use('/api/v1/auth', authRouter)
app.use('/api/v1/admin', adminRouter)

app.use(errorHandler)

app.listen(PORT, () => console.log(`API running on http://localhost:${PORT}`))
