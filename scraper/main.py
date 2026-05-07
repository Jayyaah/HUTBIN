#!/usr/bin/env python3
"""
HUTbin scraper — CLI entry point.

Examples:
  # Inspect hut-db.com and print selectors (run this first!)
  python main.py --probe

  # Full scrape of all cards (PS5 prices)
  python main.py --source hutdb --platform PS5

  # Only update stale cards (not updated in last 24h)
  python main.py --source hutdb --incremental

  # Scrape both sources
  python main.py --source all --platform PS5 --incremental

  # Export to JSON
  python main.py --export json --output exports/cards.json

  # Export to CSV filtered by position
  python main.py --export csv --output exports/cards.csv --position C

  # Export price history for a specific card
  python main.py --export json --output exports/prices.json --card-id <id>
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add scraper dir to path so imports work when run directly
sys.path.insert(0, str(Path(__file__).parent))

from config import INCREMENTAL_HOURS, setup_logging
from db_writer import DBWriter
from export import export_csv, export_json, export_price_history
from hut_db_scraper import HutDbScraper
from nhlhut_scraper import NhlHutScraper

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="hutbin-scraper",
        description="Scrape NHL HUT card data into PostgreSQL.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--source",
        choices=["hutdb", "nhlhut", "all"],
        default="hutdb",
        help="Data source to scrape (default: hutdb)",
    )
    parser.add_argument(
        "--platform",
        choices=["PS5", "XBOX", "PC"],
        default="PS5",
        help="Platform for price data (default: PS5)",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help=f"Skip players updated within the last {INCREMENTAL_HOURS}h",
    )
    parser.add_argument(
        "--export",
        choices=["json", "csv"],
        help="Export data from DB instead of scraping",
    )
    parser.add_argument(
        "--output",
        default="exports/cards",
        help="Output path for --export (extension added automatically)",
    )
    parser.add_argument(
        "--card-id",
        help="Export price history for a specific card ID",
    )

    # Export filters
    parser.add_argument("--position", choices=["C", "LW", "RW", "D", "G"])
    parser.add_argument("--team", help="Filter by team abbreviation or name")
    parser.add_argument("--card-type",
                        choices=["BASE", "TOTW", "TOTY", "EVENT", "FLASHBACK",
                                 "ICON", "ULTIMATE", "FANTASY", "PROMO", "HERO"])
    parser.add_argument("--min-overall", type=int)
    parser.add_argument("--max-overall", type=int)

    # Debug
    parser.add_argument("--probe", action="store_true",
                        help="Fetch one page and print structure for selector debugging")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--limit", type=int, default=0,
                        help="Max players to scrape (0 = all, useful for testing)")

    return parser.parse_args()


def run_export(args: argparse.Namespace) -> None:
    output = args.output
    filters = dict(
        position=args.position,
        team=args.team,
        card_type=args.card_type,
        platform=args.platform,
        min_overall=args.min_overall,
        max_overall=args.max_overall,
    )

    if args.card_id:
        path = f"{output}.json"
        count = export_price_history(path, args.card_id, args.platform)
        print(f"Exported {count} price entries → {path}")
        return

    if args.export == "json":
        path = output if output.endswith(".json") else f"{output}.json"
        count = export_json(path, **filters)
    else:
        path = output if output.endswith(".csv") else f"{output}.csv"
        count = export_csv(path, **filters)

    print(f"Exported {count} cards → {path}")


def run_scrape(args: argparse.Namespace) -> None:
    # Get incremental ID set from DB
    fresh_ids: set[str] = set()
    if args.incremental:
        with DBWriter() as db:
            fresh_ids = db.get_fresh_ea_ids(INCREMENTAL_HOURS)
        logger.info("Incremental mode: %d fresh players will be skipped", len(fresh_ids))

    scrapers: list = []
    if args.source in ("hutdb", "all"):
        scrapers.append(HutDbScraper(platform=args.platform, incremental_ids=fresh_ids))
    if args.source in ("nhlhut", "all"):
        scrapers.append(NhlHutScraper(platform=args.platform))

    total_written = 0

    for scraper in scrapers:
        source_name = type(scraper).__name__
        logger.info("Starting scraper: %s", source_name)

        # Step 1: Collect all player stubs from list pages
        players = scraper.get_all_players()
        if args.limit:
            players = players[: args.limit]
            logger.info("--limit %d applied → %d players", args.limit, len(players))

        logger.info("%s: %d players to process", source_name, len(players))

        # Step 2: Fetch detail pages and write to DB
        with DBWriter() as db:
            for i, player in enumerate(players, 1):
                try:
                    # Merge detail page data if we have a URL
                    if player.get("detail_url"):
                        logger.debug("[%d/%d] Detail: %s", i, len(players), player["detail_url"])
                        detail = scraper.get_player_detail(player["detail_url"])
                        if detail:
                            # Merge: detail overrides stub for stats/images
                            for key, val in detail.items():
                                if val and not player.get(key):
                                    player[key] = val
                            # Stats: merge dicts
                            if detail.get("stats"):
                                player.setdefault("stats", {}).update(detail["stats"])
                            if detail.get("detailed_stats"):
                                player["detailed_stats"] = detail["detailed_stats"]
                            if detail.get("prices"):
                                player.setdefault("prices", []).extend(detail["prices"])

                    player_id, card_id = db.write_player_card(player, args.platform)
                    total_written += 1
                    logger.info(
                        "[%d/%d] ✓ %s — %s OVR=%d → card=%s",
                        i, len(players),
                        player["full_name"], player["card_type"], player["overall"], card_id,
                    )

                except Exception as exc:
                    logger.error(
                        "[%d/%d] ✗ Failed for %s: %s",
                        i, len(players), player.get("full_name", "?"), exc,
                        exc_info=args.verbose,
                    )
                    continue

    logger.info("Done. Total records written/updated: %d", total_written)
    print(f"\n✓ Scrape complete — {total_written} cards written to database.")


def main() -> None:
    args = parse_args()
    setup_logging(args.verbose)

    # ── Probe mode ────────────────────────────────────────────────────────────
    if args.probe:
        scraper_cls = NhlHutScraper if args.source == "nhlhut" else HutDbScraper
        scraper = scraper_cls()
        scraper.probe_page()
        return

    # ── Export mode ───────────────────────────────────────────────────────────
    if args.export:
        run_export(args)
        return

    # ── Scrape mode ───────────────────────────────────────────────────────────
    run_scrape(args)


if __name__ == "__main__":
    main()
