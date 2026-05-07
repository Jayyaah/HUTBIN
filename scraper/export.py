"""
Export data from PostgreSQL to JSON or CSV.

Usage (from main.py):
    python main.py --export json --output ./exports/cards.json
    python main.py --export csv  --output ./exports/cards.csv
"""
from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any

import psycopg
import psycopg.rows

from config import DATABASE_URL

logger = logging.getLogger(__name__)

_CARDS_QUERY = """
SELECT
    c.id              AS card_id,
    c."cardType"      AS card_type,
    c.overall,
    c.version,
    c.season,
    c."imageUrl"      AS image_url,
    c.skating, c.shooting, c.passing, c.checking,
    c.defense, c."puckSkills" AS puck_skills, c.physical,
    c."detailedStats" AS detailed_stats,
    p.id              AS player_id,
    p."eaId"          AS ea_id,
    p."fullName"      AS full_name,
    p."firstName"     AS first_name,
    p."lastName"      AS last_name,
    p.position,
    p.nationality,
    t.name            AS team_name,
    t.abbrev          AS team_abbrev,
    l.name            AS league_name,
    l.abbrev          AS league_abbrev,
    ps."priceAvg"     AS price_avg,
    ps."priceMin"     AS price_min,
    ps."priceMax"     AS price_max,
    ps."priceMedian"  AS price_median,
    ps.trend,
    ps."trendPct"     AS trend_pct,
    ps."sampleSize"   AS sample_size,
    ps.platform       AS price_platform,
    ps."updatedAt"    AS price_updated_at
FROM "Card" c
JOIN "Player" p  ON p.id = c."playerId"
JOIN "Team" t    ON t.id = p."teamId"
JOIN "League" l  ON l.id = p."leagueId"
LEFT JOIN "PriceStats" ps ON ps."cardId" = c.id
WHERE c."isActive" = true
{where_clause}
ORDER BY c.overall DESC, p."fullName"
"""


def _connect():
    return psycopg.connect(DATABASE_URL, row_factory=psycopg.rows.dict_row)


def _build_where(
    position: str | None = None,
    team: str | None = None,
    card_type: str | None = None,
    platform: str | None = None,
    min_overall: int | None = None,
    max_overall: int | None = None,
) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []

    if position:
        clauses.append('p.position = %s::"Position"')
        params.append(position.upper())
    if team:
        clauses.append("(t.abbrev ILIKE %s OR t.name ILIKE %s)")
        params.extend([team, f"%{team}%"])
    if card_type:
        clauses.append('c."cardType" = %s::"CardType"')
        params.append(card_type.upper())
    if platform:
        clauses.append('(ps.platform = %s::"Platform" OR ps.platform IS NULL)')
        params.append(platform.upper())
    if min_overall is not None:
        clauses.append("c.overall >= %s")
        params.append(min_overall)
    if max_overall is not None:
        clauses.append("c.overall <= %s")
        params.append(max_overall)

    where = "AND " + " AND ".join(clauses) if clauses else ""
    return where, params


def export_json(
    output_path: str | Path,
    *,
    position: str | None = None,
    team: str | None = None,
    card_type: str | None = None,
    platform: str | None = None,
    min_overall: int | None = None,
    max_overall: int | None = None,
) -> int:
    """
    Export cards to a JSON file.  Returns the number of records written.
    """
    where, params = _build_where(position, team, card_type, platform, min_overall, max_overall)
    query = _CARDS_QUERY.format(where_clause=where)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

        records = []
        for row in rows:
            record = dict(row)
            # detailed_stats is already a dict from psycopg2 json handling
            if record.get("detailed_stats") and isinstance(record["detailed_stats"], str):
                record["detailed_stats"] = json.loads(record["detailed_stats"])
            # Serialize datetime
            if record.get("price_updated_at"):
                record["price_updated_at"] = record["price_updated_at"].isoformat()
            records.append(record)

        output_path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Exported %d cards to %s", len(records), output_path)
        return len(records)
    finally:
        conn.close()


def export_csv(
    output_path: str | Path,
    *,
    position: str | None = None,
    team: str | None = None,
    card_type: str | None = None,
    platform: str | None = None,
    min_overall: int | None = None,
    max_overall: int | None = None,
) -> int:
    """
    Export cards to a CSV file.  Returns the number of records written.
    Note: detailed_stats is serialised as a JSON string in the CSV.
    """
    where, params = _build_where(position, team, card_type, platform, min_overall, max_overall)
    query = _CARDS_QUERY.format(where_clause=where)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

        if not rows:
            logger.warning("No records found for export.")
            return 0

        fieldnames = list(rows[0].keys())
        with output_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                record = dict(row)
                if record.get("detailed_stats") and not isinstance(record["detailed_stats"], str):
                    record["detailed_stats"] = json.dumps(record["detailed_stats"])
                if record.get("price_updated_at"):
                    record["price_updated_at"] = record["price_updated_at"].isoformat()
                writer.writerow(record)

        logger.info("Exported %d cards to %s", len(rows), output_path)
        return len(rows)
    finally:
        conn.close()


def export_price_history(
    output_path: str | Path,
    card_id: str,
    platform: str = "PS5",
    days: int = 30,
) -> int:
    """Export price history for a specific card."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT pe.*, c.overall, c."cardType", p."fullName"
                FROM "PriceEntry" pe
                JOIN "Card" c ON c.id = pe."cardId"
                JOIN "Player" p ON p.id = c."playerId"
                WHERE pe."cardId" = %s
                  AND pe.platform = %s::"Platform"
                  AND pe."recordedAt" >= NOW() - (%s * INTERVAL '1 day')
                ORDER BY pe."recordedAt" ASC
                """,
                (card_id, platform, days),
            )
            rows = cur.fetchall()

        records = []
        for row in rows:
            record = dict(row)
            if record.get("recordedAt"):
                record["recordedAt"] = record["recordedAt"].isoformat()
            records.append(record)

        output_path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Exported %d price entries to %s", len(records), output_path)
        return len(records)
    finally:
        conn.close()
