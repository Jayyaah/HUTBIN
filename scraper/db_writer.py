"""
PostgreSQL writer for HUTbin scraper.

All writes use explicit transactions.  IDs are generated with cuid2
(compatible with Prisma's @default(cuid())).

Upsert logic:
  League  — SELECT by abbrev, INSERT if missing
  Team    — SELECT by abbrev, INSERT if missing
  Player  — upsert by eaId (if present) or (fullName, teamId)
  Card    — upsert by (playerId, cardType, COALESCE(version,''), season)
  PriceEntry  — always INSERT (append-only log)
  PriceStats  — upsert by (cardId, platform)
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import psycopg

from config import DATABASE_URL

logger = logging.getLogger(__name__)

# cuid2 with UUID fallback
try:
    from cuid2 import CUID as _CUID
    _cuid_gen = _CUID()

    def new_id() -> str:
        return _cuid_gen.generate()
except ImportError:
    import uuid
    logger.warning("cuid2 not installed — using UUID4 as ID generator")

    def new_id() -> str:  # type: ignore[misc]
        return str(uuid.uuid4()).replace("-", "")


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


class DBWriter:
    """Manages all PostgreSQL write operations for the scraper."""

    def __init__(self) -> None:
        self.conn = psycopg.connect(DATABASE_URL, autocommit=False)
        logger.info("Connected to PostgreSQL at %s", DATABASE_URL.split("@")[-1])

    def close(self) -> None:
        if self.conn and not self.conn.closed:
            self.conn.close()

    def __enter__(self) -> "DBWriter":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type:
            self.conn.rollback()
        self.close()

    # ── League ────────────────────────────────────────────────────────────────

    def get_or_create_league(self, name: str, abbrev: str) -> str:
        """Return existing league ID or create a new one."""
        with self.conn.cursor() as cur:
            cur.execute('SELECT id FROM "League" WHERE abbrev = %s', (abbrev,))
            row = cur.fetchone()
            if row:
                return row[0]

            league_id = new_id()
            cur.execute(
                """
                INSERT INTO "League" (id, name, abbrev, "createdAt", "updatedAt")
                VALUES (%s, %s, %s, %s, %s)
                """,
                (league_id, name, abbrev, _now(), _now()),
            )
            self.conn.commit()
            logger.debug("Created league '%s' (%s)", abbrev, league_id)
            return league_id

    # ── Team ─────────────────────────────────────────────────────────────────

    def get_or_create_team(
        self,
        name: str,
        abbrev: str,
        city: str = "",
        logo_url: str | None = None,
        league_id: str | None = None,
    ) -> str:
        """Return existing team ID or create a new one."""
        with self.conn.cursor() as cur:
            cur.execute('SELECT id FROM "Team" WHERE abbrev = %s', (abbrev,))
            row = cur.fetchone()
            if row:
                return row[0]

            team_id = new_id()
            cur.execute(
                """
                INSERT INTO "Team" (id, name, abbrev, city, "logoUrl", "leagueId", "createdAt", "updatedAt")
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (team_id, name, abbrev, city, logo_url, league_id, _now(), _now()),
            )
            self.conn.commit()
            logger.debug("Created team '%s' (%s)", abbrev, team_id)
            return team_id

    # ── Player ────────────────────────────────────────────────────────────────

    def upsert_player(self, data: dict) -> str:
        """
        Upsert a player.  Returns the player's DB id.

        data keys: ea_id, first_name, last_name, full_name, position,
                   nationality, handedness, team_id, league_id
        """
        ea_id: str | None = data.get("ea_id") or None
        full_name: str = data["full_name"]
        team_id: str = data["team_id"]

        with self.conn.cursor() as cur:
            # Look up by eaId first
            if ea_id:
                cur.execute('SELECT id FROM "Player" WHERE "eaId" = %s', (ea_id,))
                row = cur.fetchone()
                if row:
                    player_id = row[0]
                    cur.execute(
                        """
                        UPDATE "Player"
                        SET "firstName"=%s, "lastName"=%s, "fullName"=%s,
                            nationality=%s, position=%s::"Position",
                            "teamId"=%s, "leagueId"=%s, "updatedAt"=%s
                        WHERE id=%s
                        """,
                        (
                            data["first_name"], data["last_name"], full_name,
                            data.get("nationality", "CAN"),
                            data["position"],
                            team_id, data.get("league_id"),
                            _now(), player_id,
                        ),
                    )
                    self.conn.commit()
                    return player_id

            # Fall back to (fullName, teamId)
            cur.execute(
                'SELECT id FROM "Player" WHERE "fullName" = %s AND "teamId" = %s',
                (full_name, team_id),
            )
            row = cur.fetchone()
            if row:
                player_id = row[0]
                if ea_id:
                    cur.execute(
                        'UPDATE "Player" SET "eaId"=%s, "updatedAt"=%s WHERE id=%s',
                        (ea_id, _now(), player_id),
                    )
                    self.conn.commit()
                return player_id

            # Insert new player
            player_id = new_id()
            cur.execute(
                """
                INSERT INTO "Player"
                  (id, "eaId", "firstName", "lastName", "fullName",
                   nationality, position, "teamId", "leagueId", "createdAt", "updatedAt")
                VALUES (%s, %s, %s, %s, %s, %s, %s::"Position", %s, %s, %s, %s)
                """,
                (
                    player_id, ea_id,
                    data["first_name"], data["last_name"], full_name,
                    data.get("nationality", "CAN"),
                    data["position"],
                    team_id, data.get("league_id"),
                    _now(), _now(),
                ),
            )
            self.conn.commit()
            logger.debug("Created player '%s' (%s)", full_name, player_id)
            return player_id

    # ── Card ──────────────────────────────────────────────────────────────────

    def upsert_card(self, data: dict) -> str:
        """
        Upsert a card.  Returns the card's DB id.

        Logical key: (playerId, cardType, COALESCE(version,''), season)

        data keys: player_id, card_type, overall, version, season, image_url,
                   is_active, skating, shooting, passing, checking, defense,
                   puck_skills, physical, detailed_stats (dict)
        """
        player_id: str = data["player_id"]
        card_type: str = data["card_type"]
        version: str = data.get("version") or ""
        season: str = data.get("season", "NHL26")

        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT id FROM "Card"
                WHERE "playerId" = %s
                  AND "cardType" = %s::"CardType"
                  AND COALESCE(version, '') = %s
                  AND season = %s
                  AND "isActive" = true
                """,
                (player_id, card_type, version, season),
            )
            row = cur.fetchone()

            detailed_json = (
                json.dumps(data["detailed_stats"])
                if data.get("detailed_stats")
                else None
            )

            if row:
                card_id = row[0]
                cur.execute(
                    """
                    UPDATE "Card"
                    SET overall=%s, "imageUrl"=%s,
                        skating=%s, shooting=%s, passing=%s, checking=%s,
                        defense=%s, "puckSkills"=%s, physical=%s,
                        "detailedStats"=%s, "updatedAt"=%s
                    WHERE id=%s
                    """,
                    (
                        data["overall"], data.get("image_url"),
                        data.get("skating"), data.get("shooting"), data.get("passing"),
                        data.get("checking"), data.get("defense"),
                        data.get("puck_skills") or data.get("puckSkills"),
                        data.get("physical"),
                        detailed_json, _now(), card_id,
                    ),
                )
                self.conn.commit()
                return card_id

            # Insert
            card_id = new_id()
            cur.execute(
                """
                INSERT INTO "Card"
                  (id, "playerId", "cardType", overall, version, season,
                   "imageUrl", "isActive", "releaseDate",
                   skating, shooting, passing, checking,
                   defense, "puckSkills", physical, "detailedStats",
                   "createdAt", "updatedAt")
                VALUES
                  (%s, %s, %s::"CardType", %s, %s, %s,
                   %s, true, %s,
                   %s, %s, %s, %s,
                   %s, %s, %s, %s,
                   %s, %s)
                """,
                (
                    card_id, player_id, card_type, data["overall"],
                    version or None, season,
                    data.get("image_url"), data.get("release_date"),
                    data.get("skating"), data.get("shooting"), data.get("passing"),
                    data.get("checking"), data.get("defense"),
                    data.get("puck_skills") or data.get("puckSkills"),
                    data.get("physical"),
                    detailed_json,
                    _now(), _now(),
                ),
            )
            self.conn.commit()
            logger.debug("Created card %s OVR=%s for player %s", card_type, data["overall"], player_id)
            return card_id

    # ── PriceEntry ────────────────────────────────────────────────────────────

    def insert_price_entry(
        self,
        card_id: str,
        platform: str,
        price: int,
        sample_size: int = 1,
    ) -> None:
        """Append a new price snapshot."""
        entry_id = new_id()
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO "PriceEntry"
                  (id, "cardId", platform, "priceAvg", "priceMin", "priceMax",
                   "sampleSize", "recordedAt")
                VALUES (%s, %s, %s::"Platform", %s, %s, %s, %s, %s)
                """,
                (entry_id, card_id, platform, price, price, price, sample_size, _now()),
            )
            self.conn.commit()

    # ── PriceStats ────────────────────────────────────────────────────────────

    def upsert_price_stats(self, card_id: str, platform: str) -> None:
        """
        Recalculate and upsert PriceStats from the last 7 days of PriceEntry rows.
        Trend = UP   if avg(last 48h) > avg(prev 48h) by >2%
               DOWN  if avg(last 48h) < avg(prev 48h) by >2%
               STABLE otherwise
        """
        with self.conn.cursor() as cur:
            # Aggregate last 7 days
            cur.execute(
                """
                SELECT
                    AVG("priceAvg")::int  AS avg,
                    MIN("priceMin")       AS min,
                    MAX("priceMax")       AS max,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY "priceAvg")::int AS median,
                    COUNT(*)              AS cnt
                FROM "PriceEntry"
                WHERE "cardId" = %s
                  AND platform = %s::"Platform"
                  AND "recordedAt" >= NOW() - INTERVAL '7 days'
                """,
                (card_id, platform),
            )
            row = cur.fetchone()
            if not row or row[0] is None:
                return

            avg_price, min_price, max_price, median_price, sample_size = row

            # Trend calculation
            cur.execute(
                """
                SELECT AVG("priceAvg") FROM "PriceEntry"
                WHERE "cardId" = %s AND platform = %s::"Platform"
                  AND "recordedAt" >= NOW() - INTERVAL '48 hours'
                """,
                (card_id, platform),
            )
            recent_avg = (cur.fetchone() or [None])[0]

            cur.execute(
                """
                SELECT AVG("priceAvg") FROM "PriceEntry"
                WHERE "cardId" = %s AND platform = %s::"Platform"
                  AND "recordedAt" >= NOW() - INTERVAL '96 hours'
                  AND "recordedAt" <  NOW() - INTERVAL '48 hours'
                """,
                (card_id, platform),
            )
            prev_avg = (cur.fetchone() or [None])[0]

            trend = "STABLE"
            trend_pct = 0.0
            if recent_avg and prev_avg and prev_avg > 0:
                pct_change = ((recent_avg - prev_avg) / prev_avg) * 100
                trend_pct = round(pct_change, 2)
                if pct_change > 2:
                    trend = "UP"
                elif pct_change < -2:
                    trend = "DOWN"

            # Check if PriceStats row exists
            cur.execute(
                'SELECT id FROM "PriceStats" WHERE "cardId" = %s AND platform = %s::"Platform"',
                (card_id, platform),
            )
            existing = cur.fetchone()

            if existing:
                cur.execute(
                    """
                    UPDATE "PriceStats"
                    SET "priceAvg"=%s, "priceMin"=%s, "priceMax"=%s, "priceMedian"=%s,
                        trend=%s::"Trend", "trendPct"=%s, "sampleSize"=%s, "updatedAt"=%s
                    WHERE "cardId"=%s AND platform=%s::"Platform"
                    """,
                    (
                        avg_price, min_price, max_price, median_price,
                        trend, trend_pct, sample_size, _now(),
                        card_id, platform,
                    ),
                )
            else:
                stats_id = new_id()
                cur.execute(
                    """
                    INSERT INTO "PriceStats"
                      (id, "cardId", platform, "priceAvg", "priceMin", "priceMax",
                       "priceMedian", trend, "trendPct", "sampleSize", "updatedAt")
                    VALUES (%s, %s, %s::"Platform", %s, %s, %s, %s, %s::"Trend", %s, %s, %s)
                    """,
                    (
                        stats_id, card_id, platform,
                        avg_price, min_price, max_price, median_price,
                        trend, trend_pct, sample_size, _now(),
                    ),
                )
            self.conn.commit()

    # ── High-level write ──────────────────────────────────────────────────────

    def write_player_card(self, data: dict, platform: str) -> tuple[str, str]:
        """
        Full pipeline: League → Team → Player → Card → PriceEntry → PriceStats.
        Returns (player_id, card_id).
        """
        # 1. League
        league_id = self.get_or_create_league(
            name=data.get("league_name") or "NHL",
            abbrev=data.get("league_abbrev") or "NHL",
        )

        # 2. Team
        abbrev = data.get("team_abbrev") or _abbrev_from_name(data.get("team_name") or "UNK")
        team_id = self.get_or_create_team(
            name=data.get("team_name") or abbrev,
            abbrev=abbrev,
            league_id=league_id,
        )

        # 3. Player
        player_id = self.upsert_player({
            **data,
            "team_id": team_id,
            "league_id": league_id,
        })

        # 4. Card
        stats = data.get("stats") or {}
        card_id = self.upsert_card({
            "player_id": player_id,
            "card_type": data["card_type"],
            "overall": data["overall"],
            "version": data.get("version"),
            "season": data.get("season", "NHL26"),
            "image_url": data.get("image_url"),
            "skating": stats.get("skating"),
            "shooting": stats.get("shooting"),
            "passing": stats.get("passing"),
            "checking": stats.get("checking"),
            "defense": stats.get("defense"),
            "puck_skills": stats.get("puckSkills"),
            "physical": stats.get("physical"),
            "detailed_stats": data.get("detailed_stats"),
        })

        # 5. Prices
        for price_entry in data.get("prices") or []:
            p = price_entry.get("platform") or platform
            v = price_entry.get("price")
            if v:
                self.insert_price_entry(card_id, p, v)
                self.upsert_price_stats(card_id, p)

        return player_id, card_id

    # ── Incremental helpers ───────────────────────────────────────────────────

    def get_fresh_ea_ids(self, hours: int = 24) -> set[str]:
        """Return eaIds of players updated within the last `hours` hours."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT "eaId" FROM "Player"
                WHERE "eaId" IS NOT NULL
                  AND "updatedAt" >= NOW() - (%s * INTERVAL '1 hour')
                """,
                (hours,),
            )
            return {row[0] for row in cur.fetchall()}


def _abbrev_from_name(name: str) -> str:
    """Generate a 3-letter abbreviation from a team name."""
    words = name.upper().split()
    if len(words) >= 3:
        return "".join(w[0] for w in words[:3])
    if len(words) == 2:
        return words[0][:2] + words[1][0]
    return name[:3].upper()
