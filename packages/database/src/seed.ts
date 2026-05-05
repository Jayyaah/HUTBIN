import { PrismaClient, CardType, Position, Platform, Trend } from '@prisma/client'
import { hash } from 'crypto'

const db = new PrismaClient()

async function main() {
  console.log('Seeding database...')

  // ── Leagues ────────────────────────────────────────────────
  const nhl = await db.league.upsert({
    where: { name: 'NHL' },
    update: {},
    create: { name: 'NHL', abbrev: 'NHL' },
  })

  // ── Teams ──────────────────────────────────────────────────
  const teams = await Promise.all([
    db.team.upsert({ where: { abbrev: 'EDM' }, update: {}, create: { name: 'Edmonton Oilers', abbrev: 'EDM', city: 'Edmonton', leagueId: nhl.id } }),
    db.team.upsert({ where: { abbrev: 'COL' }, update: {}, create: { name: 'Colorado Avalanche', abbrev: 'COL', city: 'Denver', leagueId: nhl.id } }),
    db.team.upsert({ where: { abbrev: 'BOS' }, update: {}, create: { name: 'Boston Bruins', abbrev: 'BOS', city: 'Boston', leagueId: nhl.id } }),
    db.team.upsert({ where: { abbrev: 'TBL' }, update: {}, create: { name: 'Tampa Bay Lightning', abbrev: 'TBL', city: 'Tampa Bay', leagueId: nhl.id } }),
    db.team.upsert({ where: { abbrev: 'WSH' }, update: {}, create: { name: 'Washington Capitals', abbrev: 'WSH', city: 'Washington', leagueId: nhl.id } }),
    db.team.upsert({ where: { abbrev: 'PIT' }, update: {}, create: { name: 'Pittsburgh Penguins', abbrev: 'PIT', city: 'Pittsburgh', leagueId: nhl.id } }),
    db.team.upsert({ where: { abbrev: 'NYR' }, update: {}, create: { name: 'New York Rangers', abbrev: 'NYR', city: 'New York', leagueId: nhl.id } }),
    db.team.upsert({ where: { abbrev: 'FLA' }, update: {}, create: { name: 'Florida Panthers', abbrev: 'FLA', city: 'Sunrise', leagueId: nhl.id } }),
    db.team.upsert({ where: { abbrev: 'VGK' }, update: {}, create: { name: 'Vegas Golden Knights', abbrev: 'VGK', city: 'Las Vegas', leagueId: nhl.id } }),
    db.team.upsert({ where: { abbrev: 'CAR' }, update: {}, create: { name: 'Carolina Hurricanes', abbrev: 'CAR', city: 'Raleigh', leagueId: nhl.id } }),
  ])

  const teamMap = Object.fromEntries(teams.map(t => [t.abbrev, t]))

  // ── Players + Cards ────────────────────────────────────────
  const playerData = [
    {
      firstName: 'Connor', lastName: 'McDavid', nationality: 'CAN',
      position: Position.C, teamAbbrev: 'EDM',
      cards: [
        {
          cardType: CardType.BASE, overall: 99, version: 'Base',
          skating: 99, shooting: 95, passing: 99, checking: 45, defense: 55, puckSkills: 99, physical: 72,
          detailedStats: { acceleration: 99, speed: 99, agility: 99, balance: 92, endurance: 95, snapShot: 88, slap: 82, heelToe: 98, backhand: 92, offPuck: 99, vision: 99, positioning: 96 },
        },
        {
          cardType: CardType.TOTW, overall: 99, version: 'TOTW 3',
          skating: 99, shooting: 96, passing: 99, checking: 46, defense: 57, puckSkills: 99, physical: 73,
          detailedStats: { acceleration: 99, speed: 99, agility: 99, balance: 93, endurance: 96, snapShot: 90, slap: 84, heelToe: 99, backhand: 94, offPuck: 99, vision: 99, positioning: 97 },
        },
      ],
    },
    {
      firstName: 'Nathan', lastName: 'MacKinnon', nationality: 'CAN',
      position: Position.C, teamAbbrev: 'COL',
      cards: [
        {
          cardType: CardType.BASE, overall: 98, version: 'Base',
          skating: 98, shooting: 94, passing: 96, checking: 60, defense: 65, puckSkills: 97, physical: 82,
          detailedStats: { acceleration: 98, speed: 98, agility: 97, balance: 95, endurance: 97, snapShot: 89, slap: 87, heelToe: 96, backhand: 91, offPuck: 97, vision: 98, positioning: 95 },
        },
        {
          cardType: CardType.TOTY, overall: 99, version: 'Team of the Year',
          skating: 99, shooting: 96, passing: 97, checking: 62, defense: 67, puckSkills: 98, physical: 84,
          detailedStats: { acceleration: 99, speed: 99, agility: 98, balance: 96, endurance: 98, snapShot: 92, slap: 90, heelToe: 97, backhand: 93, offPuck: 98, vision: 99, positioning: 97 },
        },
      ],
    },
    {
      firstName: 'Leon', lastName: 'Draisaitl', nationality: 'DEU',
      position: Position.C, teamAbbrev: 'EDM',
      cards: [
        {
          cardType: CardType.BASE, overall: 97, version: 'Base',
          skating: 88, shooting: 97, passing: 95, checking: 65, defense: 60, puckSkills: 97, physical: 88,
          detailedStats: { acceleration: 87, speed: 88, agility: 85, balance: 94, endurance: 94, snapShot: 94, slap: 95, heelToe: 96, backhand: 97, offPuck: 96, vision: 97, positioning: 96 },
        },
      ],
    },
    {
      firstName: 'Nikita', lastName: 'Kucherov', nationality: 'RUS',
      position: Position.RW, teamAbbrev: 'TBL',
      cards: [
        {
          cardType: CardType.BASE, overall: 97, version: 'Base',
          skating: 91, shooting: 93, passing: 97, checking: 50, defense: 52, puckSkills: 97, physical: 70,
          detailedStats: { acceleration: 90, speed: 91, agility: 93, balance: 88, endurance: 90, snapShot: 91, slap: 85, heelToe: 97, backhand: 93, offPuck: 97, vision: 98, positioning: 96 },
        },
        {
          cardType: CardType.ICON, overall: 99, version: 'Icon',
          skating: 93, shooting: 95, passing: 99, checking: 52, defense: 54, puckSkills: 99, physical: 72,
          detailedStats: { acceleration: 92, speed: 93, agility: 95, balance: 90, endurance: 92, snapShot: 93, slap: 87, heelToe: 99, backhand: 95, offPuck: 99, vision: 99, positioning: 98 },
        },
      ],
    },
    {
      firstName: 'Alex', lastName: 'Ovechkin', nationality: 'RUS',
      position: Position.LW, teamAbbrev: 'WSH',
      cards: [
        {
          cardType: CardType.BASE, overall: 95, version: 'Base',
          skating: 84, shooting: 99, passing: 84, checking: 72, defense: 55, puckSkills: 91, physical: 94,
          detailedStats: { acceleration: 82, speed: 84, agility: 80, balance: 95, endurance: 88, snapShot: 98, slap: 99, heelToe: 90, backhand: 80, offPuck: 92, vision: 90, positioning: 95 },
        },
        {
          cardType: CardType.FLASHBACK, overall: 98, version: 'Flashback 2008',
          skating: 90, shooting: 99, passing: 86, checking: 75, defense: 58, puckSkills: 93, physical: 96,
          detailedStats: { acceleration: 88, speed: 90, agility: 85, balance: 96, endurance: 92, snapShot: 99, slap: 99, heelToe: 92, backhand: 83, offPuck: 94, vision: 92, positioning: 97 },
        },
      ],
    },
    {
      firstName: 'Sidney', lastName: 'Crosby', nationality: 'CAN',
      position: Position.C, teamAbbrev: 'PIT',
      cards: [
        {
          cardType: CardType.BASE, overall: 95, version: 'Base',
          skating: 90, shooting: 91, passing: 96, checking: 72, defense: 68, puckSkills: 97, physical: 88,
          detailedStats: { acceleration: 88, speed: 90, agility: 91, balance: 96, endurance: 96, snapShot: 88, slap: 84, heelToe: 97, backhand: 93, offPuck: 97, vision: 98, positioning: 97 },
        },
      ],
    },
    {
      firstName: 'Artemi', lastName: 'Panarin', nationality: 'RUS',
      position: Position.LW, teamAbbrev: 'NYR',
      cards: [
        {
          cardType: CardType.BASE, overall: 93, version: 'Base',
          skating: 88, shooting: 88, passing: 94, checking: 45, defense: 50, puckSkills: 95, physical: 68,
          detailedStats: { acceleration: 87, speed: 88, agility: 90, balance: 85, endurance: 88, snapShot: 86, slap: 80, heelToe: 95, backhand: 90, offPuck: 95, vision: 96, positioning: 93 },
        },
        {
          cardType: CardType.EVENT, overall: 95, version: 'Winter Series',
          skating: 90, shooting: 90, passing: 96, checking: 47, defense: 52, puckSkills: 97, physical: 70,
          detailedStats: { acceleration: 89, speed: 90, agility: 92, balance: 87, endurance: 90, snapShot: 88, slap: 82, heelToe: 97, backhand: 92, offPuck: 97, vision: 98, positioning: 95 },
        },
      ],
    },
    {
      firstName: 'Matthew', lastName: 'Tkachuk', nationality: 'USA',
      position: Position.LW, teamAbbrev: 'FLA',
      cards: [
        {
          cardType: CardType.BASE, overall: 93, version: 'Base',
          skating: 87, shooting: 88, passing: 91, checking: 80, defense: 72, puckSkills: 93, physical: 92,
          detailedStats: { acceleration: 85, speed: 87, agility: 86, balance: 92, endurance: 92, snapShot: 86, slap: 83, heelToe: 93, backhand: 88, offPuck: 94, vision: 92, positioning: 91 },
        },
      ],
    },
    {
      firstName: 'Mark', lastName: 'Stone', nationality: 'CAN',
      position: Position.RW, teamAbbrev: 'VGK',
      cards: [
        {
          cardType: CardType.BASE, overall: 91, version: 'Base',
          skating: 85, shooting: 85, passing: 90, checking: 75, defense: 82, puckSkills: 88, physical: 86,
          detailedStats: { acceleration: 83, speed: 85, agility: 84, balance: 88, endurance: 90, snapShot: 83, slap: 79, heelToe: 88, backhand: 85, offPuck: 90, vision: 93, positioning: 92 },
        },
      ],
    },
    {
      firstName: 'Sebastian', lastName: 'Aho', nationality: 'FIN',
      position: Position.C, teamAbbrev: 'CAR',
      cards: [
        {
          cardType: CardType.BASE, overall: 92, version: 'Base',
          skating: 92, shooting: 87, passing: 90, checking: 62, defense: 66, puckSkills: 90, physical: 80,
          detailedStats: { acceleration: 91, speed: 92, agility: 90, balance: 88, endurance: 93, snapShot: 85, slap: 82, heelToe: 90, backhand: 87, offPuck: 91, vision: 92, positioning: 91 },
        },
        {
          cardType: CardType.TOTW, overall: 93, version: 'TOTW 7',
          skating: 93, shooting: 89, passing: 91, checking: 63, defense: 67, puckSkills: 91, physical: 81,
          detailedStats: { acceleration: 92, speed: 93, agility: 91, balance: 89, endurance: 94, snapShot: 87, slap: 84, heelToe: 91, backhand: 88, offPuck: 92, vision: 93, positioning: 92 },
        },
      ],
    },
  ]

  let cardCount = 0

  for (const pd of playerData) {
    const team = teamMap[pd.teamAbbrev]

    const player = await db.player.upsert({
      where: { eaId: `${pd.firstName.toLowerCase()}_${pd.lastName.toLowerCase()}` },
      update: {},
      create: {
        eaId: `${pd.firstName.toLowerCase()}_${pd.lastName.toLowerCase()}`,
        firstName: pd.firstName,
        lastName: pd.lastName,
        fullName: `${pd.firstName} ${pd.lastName}`,
        nationality: pd.nationality,
        position: pd.position,
        teamId: team.id,
        leagueId: nhl.id,
      },
    })

    for (const cd of pd.cards) {
      const existingCard = await db.card.findFirst({
        where: { playerId: player.id, cardType: cd.cardType, version: cd.version },
      })

      if (!existingCard) {
        const card = await db.card.create({
          data: {
            playerId: player.id,
            cardType: cd.cardType,
            overall: cd.overall,
            version: cd.version,
            skating: cd.skating,
            shooting: cd.shooting,
            passing: cd.passing,
            checking: cd.checking,
            defense: cd.defense,
            puckSkills: cd.puckSkills,
            physical: cd.physical,
            detailedStats: cd.detailedStats,
          },
        })

        // Prix fictifs de démonstration
        await db.priceStats.create({
          data: {
            cardId: card.id,
            platform: Platform.PS5,
            priceAvg: getPriceForOverall(cd.overall),
            priceMin: Math.round(getPriceForOverall(cd.overall) * 0.85),
            priceMax: Math.round(getPriceForOverall(cd.overall) * 1.2),
            priceMedian: Math.round(getPriceForOverall(cd.overall) * 0.97),
            trend: [Trend.UP, Trend.DOWN, Trend.STABLE][Math.floor(Math.random() * 3)],
            trendPct: parseFloat((Math.random() * 10 - 5).toFixed(1)),
            sampleSize: Math.floor(Math.random() * 80) + 20,
          },
        })

        cardCount++
      }
    }
  }

  // ── Admin user ─────────────────────────────────────────────
  await db.user.upsert({
    where: { email: 'admin@hutbin.gg' },
    update: {},
    create: {
      email: 'admin@hutbin.gg',
      username: 'admin',
      passwordHash: hash('sha256', 'admin123'),
      role: 'ADMIN',
      reliabilityScore: 1.0,
    },
  })

  console.log(`Done! Seeded ${playerData.length} players and ${cardCount} cards.`)
}

function getPriceForOverall(overall: number): number {
  const base: Record<number, number> = {
    99: 850000, 98: 420000, 97: 180000, 96: 90000, 95: 45000,
    93: 18000, 92: 10000, 91: 6000, 90: 3500,
  }
  return base[overall] ?? 1500
}

main()
  .catch(console.error)
  .finally(() => db.$disconnect())
