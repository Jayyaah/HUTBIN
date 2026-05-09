"""
Scraper for https://www.hutdb.app (Supabase REST API).

Calls the Supabase REST API directly — no HTML scraping, no Playwright.
All player data is fetched in batches of SUPABASE_BATCH via offset pagination.
"""
from __future__ import annotations

import logging
from typing import Any

from base_scraper import BaseScraper
from config import (
    HUTDB_BASE,
    SEASON,
    SUPABASE_ANON_KEY,
    SUPABASE_BATCH,
    SUPABASE_STORAGE_BASE,
    SUPABASE_URL,
)
from mappers import map_card_type, map_nationality, map_position

logger = logging.getLogger(__name__)

_SUPABASE_HEADERS = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Accept": "application/json",
}


class HutDbScraper(BaseScraper):
    """Fetches player cards from hutdb.app via the Supabase REST API."""

    def __init__(self, platform: str = "PS5", incremental_ids: set[str] | None = None) -> None:
        super().__init__()
        self.platform = platform
        self.incremental_ids: set[str] = incremental_ids or set()
        self._session.headers.update(_SUPABASE_HEADERS)

    # ── Public API ────────────────────────────────────────────────────────────

    def get_all_players(self) -> list[dict]:
        results: list[dict] = []
        offset = 0

        while True:
            url = (
                f"{SUPABASE_URL}/rest/v1/players"
                f"?select=*&order=overall.desc&offset={offset}&limit={SUPABASE_BATCH}"
            )
            logger.info("Fetching players offset=%d — %s", offset, url)

            batch: list[dict] | None = self.fetch_json(url)
            if not batch:
                break

            players = [self._normalize(p) for p in batch]
            players = [p for p in players if p]

            if self.incremental_ids:
                before = len(players)
                players = [p for p in players if p.get("ea_id") not in self.incremental_ids]
                logger.debug("Incremental: skipped %d existing players", before - len(players))

            results.extend(players)
            logger.info("  → %d players (offset %d)", len(players), offset)

            if len(batch) < SUPABASE_BATCH:
                break
            offset += SUPABASE_BATCH

        logger.info("Total players collected: %d", len(results))
        return results

    def get_player_detail(self, url: str) -> dict:
        # All data is already in the list endpoint — no detail page needed.
        return {}

    def probe_page(self) -> None:
        self.probe(f"{HUTDB_BASE}/players")

    # ── Normalization ─────────────────────────────────────────────────────────

    def _normalize(self, raw: dict) -> dict | None:
        bio: dict = raw.get("bio") or {}
        stats_raw: dict = raw.get("stats") or {}
        market: dict = raw.get("market") or {}

        name_raw = raw.get("name") or bio.get("name") or ""
        if not name_raw:
            return None

        name = name_raw.title()
        first, last = _split_name(name)

        overall = raw.get("overall")
        if not overall:
            return None

        position_str = raw.get("position") or bio.get("position") or "C"
        card_type_str = bio.get("card") or raw.get("card_type") or "BASE"
        team = raw.get("team") or bio.get("team") or "UNK"
        league = bio.get("league") or "NHL"
        nationality = raw.get("nationality") or bio.get("nationality") or ""
        shoots = bio.get("shoots") or "RIGHT"

        image_url = raw.get("image_url")
        if image_url and not image_url.startswith("http"):
            image_url = f"{SUPABASE_STORAGE_BASE}{image_url}"

        stats = _compute_stats(stats_raw)
        detailed = _flatten_stats(stats_raw)

        price = market.get("price") or 0
        prices = [{"platform": self.platform, "price": price}] if price > 0 else []

        return {
            "ea_id": str(raw["id"]),
            "first_name": first,
            "last_name": last,
            "full_name": name,
            "overall": int(overall),
            "card_type": map_card_type(str(card_type_str)),
            "position": map_position(str(position_str)),
            "team_name": str(team),
            "team_abbrev": None,
            "league_name": str(league),
            "league_abbrev": str(league),
            "image_url": image_url,
            "detail_url": None,
            "nationality": map_nationality(str(nationality)),
            "handedness": "LEFT" if str(shoots).upper() == "LEFT" else "RIGHT",
            "stats": stats,
            "prices": prices,
            "season": SEASON,
            "detailed_stats": detailed or None,
        }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _split_name(full: str) -> tuple[str, str]:
    parts = full.strip().split(None, 1)
    return (parts[0], parts[1]) if len(parts) == 2 else (parts[0], "")


def _avg(d: dict) -> int | None:
    vals = [v for v in d.values() if isinstance(v, (int, float))]
    return round(sum(vals) / len(vals)) if vals else None


def _compute_stats(raw: dict) -> dict[str, Any]:
    skating_d = raw.get("skating") or {}
    shooting_d = raw.get("shooting") or {}
    hands_d = raw.get("hands") or {}
    checking_d = raw.get("checking") or {}
    defense_d = raw.get("defense") or {}

    passing_val = hands_d.get("passing")
    puck_keys = {k: v for k, v in hands_d.items() if k != "passing"}

    return {
        "skating":    _avg(skating_d),
        "shooting":   _avg(shooting_d),
        "passing":    int(passing_val) if passing_val is not None else _avg(hands_d),
        "puckSkills": _avg(puck_keys) if puck_keys else _avg(hands_d),
        "checking":   _avg(checking_d),
        "defense":    _avg(defense_d),
        "physical":   None,
    }


def _flatten_stats(raw: dict) -> dict[str, int]:
    flat: dict[str, int] = {}
    for category, sub in raw.items():
        if isinstance(sub, dict):
            for k, v in sub.items():
                if isinstance(v, (int, float)):
                    flat[f"{category}_{k}"] = int(v)
    return flat


# ── Shared HTML utilities (used by nhlhut_scraper) ────────────────────────────

import re as _re
from bs4 import BeautifulSoup as _BS, Tag as _Tag


def _normalize_hand(raw: str) -> str:
    r = raw.lower()
    if "left" in r or r == "l":
        return "LEFT"
    return "RIGHT"


def _find_first(soup: "_BS | _Tag", selectors: list[str]) -> list[_Tag]:
    for sel in selectors:
        try:
            results = soup.select(sel)
            if results:
                return results
        except Exception:
            continue
    return []


def _find_first_tag(element: _Tag, selectors: list[str]) -> "_Tag | None":
    for sel in selectors:
        try:
            found = element.select_one(sel)
            if found:
                return found
        except Exception:
            continue
    return None


def _text(element: _Tag, selectors: list[str]) -> "str | None":
    tag = _find_first_tag(element, selectors)
    return tag.get_text(strip=True) if tag else None


def _img_src(element: _Tag, selectors: list[str]) -> "str | None":
    for sel in selectors:
        try:
            img = element.select_one(sel)
            if img:
                src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
                if src:
                    return str(src)
        except Exception:
            continue
    return None