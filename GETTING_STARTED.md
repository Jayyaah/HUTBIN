# HUTBIN — Getting Started

## Prérequis
- Node.js 20+
- Docker Desktop

## 1. Variables d'environnement
```bash
cp .env.example .env
cp packages/database/.env.example packages/database/.env
```

## 2. Démarrer PostgreSQL
```bash
docker compose up -d
```

## 3. Installer les dépendances
```bash
npm install
```

## 4. Migration + Seed
```bash
cd packages/database
npx prisma migrate dev --name init
npm run db:seed
cd ../..
```

## 5. Lancer l'API et le frontend
```bash
# Terminal 1 — API (port 4000)
cd apps/api && npm run dev

# Terminal 2 — Frontend (port 3000)
cd apps/web && npm run dev
```

## URLs
- Frontend : http://localhost:3000
- API      : http://localhost:4000
- Prisma Studio : `cd packages/database && npx prisma studio`

## Compte admin (seed)
- Email : admin@hutbin.gg
- Mot de passe : admin123
