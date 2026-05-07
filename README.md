# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN
# HUTBIN

Plateforme communautaire de cartes joueurs pour NHL 26 HUT (Hockey Ultimate Team).  
Consultez les stats, suivez les prix et contribuez à la base de données.

---

## Stack

| Couche      | Technologie                        |
|-------------|------------------------------------|
| Frontend    | Next.js 15, Tailwind CSS, Chart.js |
| Backend     | Express.js (Node 20)               |
| Base de données | PostgreSQL 16 + Prisma ORM     |
| Auth        | JWT (sessions en base)             |
| Monorepo    | Turborepo + npm workspaces         |
| Dev local   | Docker Compose                     |

---

## Prérequis

- [Node.js 20+](https://nodejs.org)
- [Docker Desktop](https://www.docker.com/products/docker-desktop)

---

## Installation

### 1. Cloner et installer les dépendances

```bash
git clone https://github.com/your-username/HUTBIN.git
cd HUTBIN
npm install
```

### 2. Configurer les variables d'environnement

```bash
cp .env.example .env
cp packages/database/.env.example packages/database/.env
```

Les valeurs par défaut fonctionnent directement pour le développement local, aucune modification nécessaire.

### 3. Démarrer la base de données

```bash
docker compose up -d
```

Cela démarre PostgreSQL sur le port `5432` et Redis sur le port `6379`.

### 4. Créer les tables et insérer les données de démo

```bash
cd packages/database
npx prisma migrate dev --name init
npm run db:seed
cd ../..
```

Le seed insère :
- 10 équipes NHL
- 10 joueurs (McDavid, MacKinnon, Draisaitl, Kucherov, Ovechkin...)
- 20 cartes (BASE, TOTW, TOTY, ICON, FLASHBACK...)
- Des prix de démonstration pour chaque carte
- Un compte admin

### 5. Lancer l'application

Ouvrir **deux terminaux** :

```bash
# Terminal 1 — API (http://localhost:4000)
cd apps/api
npm run dev
```

```bash
# Terminal 2 — Frontend (http://localhost:3000)
cd apps/web
npm run dev
```

---

## URLs

| Service         | URL                          |
|-----------------|------------------------------|
| Frontend        | http://localhost:3000        |
| API             | http://localhost:4000        |
| Health check    | http://localhost:4000/health |
| Prisma Studio   | voir commande ci-dessous     |

```bash
# Interface visuelle pour explorer la base de données
cd packages/database && npx prisma studio
```

---

## Compte admin (créé par le seed)

| Champ       | Valeur              |
|-------------|---------------------|
| Email       | admin@hutbin.gg     |
| Mot de passe | admin123           |
| Rôle        | ADMIN               |

---

## Structure du projet

```
HUTBIN/
├── apps/
│   ├── api/                  API REST Express
│   │   └── src/
│   │       ├── routes/       cards, players, prices, auth, admin
│   │       └── middleware/   auth JWT, gestion des erreurs
│   └── web/                  Frontend Next.js
│       └── src/
│           ├── app/          Pages (/, /cards, /cards/[id])
│           └── components/   CardGrid, StatBar, PriceChart...
├── packages/
│   └── database/
│       ├── prisma/schema.prisma
│       └── src/seed.ts
├── docker-compose.yml
└── .env.example
```

---

## Endpoints API principaux

```
GET  /api/v1/cards                  Liste des cartes (filtres + pagination)
GET  /api/v1/cards/:id              Détail d'une carte
GET  /api/v1/cards/:id/prices       Historique des prix

GET  /api/v1/players                Liste des joueurs
GET  /api/v1/players/search?q=      Recherche par nom
GET  /api/v1/players/:id            Profil joueur + ses cartes

POST /api/v1/prices                 Soumettre un prix (auth requis)

POST /api/v1/auth/register          Créer un compte
POST /api/v1/auth/login             Connexion
GET  /api/v1/auth/me                Profil connecté

GET  /api/v1/admin/stats            Stats du dashboard (admin)
GET  /api/v1/admin/prices/pending   File de modération (admin)
```

Exemple de filtre sur les cartes :
```
GET /api/v1/cards?overall_min=90&position=C&card_type=TOTW&sort=price_desc&page=1
```

---

## Commandes utiles

```bash
# Réinitialiser la base de données
cd packages/database && npx prisma migrate reset --force

# Générer le client Prisma après modification du schéma
cd packages/database && npx prisma generate

# Vérifier les types TypeScript
cd apps/api && npx tsc --noEmit
cd apps/web && npx tsc --noEmit

# Arrêter Docker
docker compose down

# Arrêter Docker et supprimer les données
docker compose down -v
```

---

## Ajouter des cartes

Via l'API (compte admin requis) :

```bash
# 1. Se connecter
curl -X POST http://localhost:4000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@hutbin.gg","password":"admin123"}'

# 2. Créer une carte (remplacer TOKEN et PLAYER_ID)
curl -X POST http://localhost:4000/api/v1/cards \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "playerId": "PLAYER_ID",
    "cardType": "TOTW",
    "overall": 95,
    "version": "TOTW 12",
    "skating": 94,
    "shooting": 91,
    "passing": 88,
    "defense": 65,
    "puckSkills": 90,
    "physical": 80
  }'
```

Via Prisma Studio (plus simple) :
```bash
cd packages/database && npx prisma studio
```
