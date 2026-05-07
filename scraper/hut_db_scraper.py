"""
Scraper for https://www.hut-db.com

Parsing strategy (in order of preference):
  1. __NEXT_DATA__ JSON blob — cleanest, no selector fragility
  2. requests + BeautifulSoup (static HTML selectors from config.py)
  3. Playwright headless browser (JS-heavy pages, automatic fallback)

After running `python main.py --probe`, update HUTDB_SELECTORS in config.py
to match the real CSS classes on hut-db.com.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from base_scraper import BaseScraper
from config import (
    HUTDB_BASE,
    HUTDB_SEASON_PREFIX,
    HUTDB_SELECTORS,
    NEXTDATA_PAGINATION_PATHS,
    NEXTDATA_PLAYER_LIST_PATHS,
    SEASON,
)
from mappers import STAT_FIELD_MAP, TOP_LEVEL_STATS, map_card_type, map_nationality, map_position

logger = logging.getLogger(__name__)


class HutDbScraper(BaseScraper):
    """Scrapes player cards from hut-db.com."""

    def __init__(self, platform: str = "PS5", incremental_ids: set[str] | None = None) -> None:
        super().__init__()
        self.platform = platform
        # eaIds already in DB (used for --incremental skipping)
        self.incremental_ids: set[str] = incremental_ids or set()

    # ── Public API ────────────────────────────────────────────────────────────

    def get_all_players(self) -> list[dict]:
        """
        Paginate through all player pages and return a list of raw card dicts.
        Each dict has at minimum:
            ea_id, name, overall, card_type, position, team, league, image_url,
            detail_url, stats (partial), prices
        """
        results: list[dict] = []
        page = 1
        total_pages = None

        while True:
            url = self._list_url(page)
            logger.info("Fetching player list page %d%s — %s",
                        page, f"/{total_pages}" if total_pages else "", url)

            html = self.fetch_html(url)
            if not html:
                logger.error("Empty response for page %d, stopping.", page)
                break

            # Try Next.js JSON first
            next_data = self.extract_next_data(html)
            if next_data:
                players, total_pages = self._parse_nextdata_list(next_data)
            else:
                players, total_pages = self._parse_html_list(html, url)

            if not players:
                logger.info("No players found on page %d, stopping pagination.", page)
                break

            logger.info("  → %d players on page %d", len(players), page)

            # Incremental: skip players whose eaId is already known and fresh
            if self.incremental_ids:
                before = len(players)
                players = [p for p in players if p.get("ea_id") not in self.incremental_ids]
                logger.debug("  Incremental: skipped %d existing players", before - len(players))

            results.extend(players)

            if total_pages and page >= total_pages:
                break
            page += 1

        logger.info("Total players collected: %d", len(results))
        return results

    def get_player_detail(self, url: str) -> dict:
        """
        Fetch a player detail page and return full stats + prices.
        Merges with any partial data already in the dict from the list page.
        """
        html = self.fetch_html(url)
        if not html:
            return {}

        next_data = self.extract_next_data(html)
        if next_data:
            return self._parse_nextdata_detail(next_data, url)
        return self._parse_html_detail(html, url)

    def probe_page(self) -> None:
        """Print diagnostic info for the first players list page."""
        self.probe(self._list_url(1))

    # ── URL builders ──────────────────────────────────────────────────────────

    def _list_url(self, page: int) -> str:
        # Common patterns — the scraper tries the first one that returns content.
        # Adjust HUTDB_SEASON_PREFIX in config.py if needed.
        return f"{HUTDB_BASE}{HUTDB_SEASON_PREFIX}/players?page={page}"

    # ── Next.js JSON parsers ──────────────────────────────────────────────────

    def _parse_nextdata_list(self, data: dict) -> tuple[list[dict], int | None]:
        """Extract player list from __NEXT_DATA__. Returns (players, total_pages)."""
        players_raw: Any = None
        for path in NEXTDATA_PLAYER_LIST_PATHS:
            players_raw = self.dig(data, path)
            if players_raw:
                logger.debug("Found player list at __NEXT_DATA__.%s", path)
                break

        if not players_raw or not isinstance(players_raw, list):
            return [], None

        players = [self._normalize_nextdata_player(p) for p in players_raw]
        players = [p for p in players if p]  # filter None

        # Pagination
        total_pages = None
        for path in NEXTDATA_PAGINATION_PATHS:
            pagination = self.dig(data, path)
            if isinstance(pagination, dict):
                # try common keys
                total = pagination.get("totalPages") or pagination.get("total_pages") or pagination.get("pages")
                per_page = pagination.get("perPage") or pagination.get("per_page") or pagination.get("limit") or 20
                total_count = pagination.get("total") or pagination.get("count")
                if total:
                    total_pages = int(total)
                elif total_count and per_page:
                    total_pages = -(-int(total_count) // int(per_page))  # ceiling div
                break

        return players, total_pages

    def _normalize_nextdata_player(self, raw: dict) -> dict | None:
        """Convert a raw Next.js player dict to our internal format."""
        if not isinstance(raw, dict):
            return None

        # Try many possible field name conventions (camelCase, snake_case, etc.)
        def get(*keys: str) -> Any:
            for k in keys:
                if raw.get(k) is not None:
                    return raw[k]
            return None

        name = get("name", "fullName", "full_name", "playerName", "player_name")
        overall = get("overall", "ovr", "rating", "overallRating")
        position = get("position", "pos")
        card_type = get("cardType", "card_type", "type", "cardtype")
        team = get("team", "teamName", "team_name", "club")
        league = get("league", "leagueName", "league_name")
        image_url = get("imageUrl", "image_url", "image", "cardImage", "card_image", "img")
        ea_id = get("eaId", "ea_id", "id", "playerId", "player_id")
        detail_url = get("url", "href", "slug", "detailUrl", "detail_url")

        if not name or not overall:
            logger.debug("Skipping incomplete player: %s", raw)
            return None

        # Build detail URL
        if detail_url and not detail_url.startswith("http"):
            detail_url = urljoin(HUTDB_BASE, detail_url)

        # Split name
        first, last = _split_name(str(name))

        return {
            "ea_id": str(ea_id) if ea_id else None,
            "first_name": first,
            "last_name": last,
            "full_name": str(name),
            "overall": int(overall),
            "card_type": map_card_type(str(card_type)) if card_type else "BASE",
            "position": map_position(str(position)) if position else "C",
            "team_name": str(team) if team else None,
            "team_abbrev": get("teamAbbrev", "team_abbrev", "abbrev"),
            "league_name": str(league) if league else "NHL",
            "league_abbrev": get("leagueAbbrev", "league_abbrev"),
            "image_url": str(image_url) if image_url else None,
            "detail_url": detail_url,
            "nationality": map_nationality(str(get("nationality", "nation", "country") or "")),
            "handedness": _normalize_hand(str(get("shoots", "hand", "handedness") or "")),
            "stats": _extract_stats_from_dict(raw),
            "prices": _extract_prices_from_dict(raw, self.platform),
            "season": SEASON,
        }

    def _parse_nextdata_detail(self, data: dict, url: str) -> dict:
        """Extract full detail (stats + prices) from a player detail page's __NEXT_DATA__."""
        player_raw = (
            self.dig(data, "props.pageProps.player")
            or self.dig(data, "props.pageProps.card")
            or self.dig(data, "props.pageProps.data")
            or {}
        )
        if not player_raw:
            return {}

        base = self._normalize_nextdata_player(player_raw) or {}
        base["detail_url"] = url

        # Detailed stats (sub-attributes)
        detailed: dict[str, int] = {}
        for key in ("detailedStats", "detailed_stats", "attributes", "stats"):
            block = player_raw.get(key)
            if isinstance(block, dict):
                for k, v in block.items():
                    try:
                        detailed[k] = int(v)
                    except (TypeError, ValueError):
                        pass
        if detailed:
            base["detailed_stats"] = detailed

        return base

    # ── HTML / BeautifulSoup parsers ──────────────────────────────────────────

    def _parse_html_list(self, html: str, base_url: str) -> tuple[list[dict], int | None]:
        soup = BeautifulSoup(html, "lxml")
        players: list[dict] = []

        # Find player card containers using candidate selectors
        cards = _find_first(soup, HUTDB_SELECTORS["player_card"])
        if not cards:
            logger.warning(
                "Could not find player cards with selectors %s. "
                "Run --probe to inspect the page.",
                HUTDB_SELECTORS["player_card"],
            )
            return [], None

        for card in cards:
            parsed = self._parse_html_card(card, base_url)
            if parsed:
                players.append(parsed)

        # Pagination
        total_pages = _extract_total_pages(soup, HUTDB_SELECTORS)

        return players, total_pages

    def _parse_html_card(self, card: Tag, base_url: str) -> dict | None:
        """Parse a single player card element from the list page."""
        # EA ID from data attribute
        ea_id = (
            card.get("data-player-id")
            or card.get("data-id")
            or card.get("data-ea-id")
        )

        # Detail URL
        link_tag = _find_first_tag(card, HUTDB_SELECTORS["player_link"])
        detail_url = None
        if link_tag and link_tag.get("href"):
            href = str(link_tag["href"])
            detail_url = href if href.startswith("http") else urljoin(base_url, href)

        # Text fields
        name = _text(card, HUTDB_SELECTORS["name"])
        overall_str = _text(card, HUTDB_SELECTORS["overall"])
        card_type_str = _text(card, HUTDB_SELECTORS["card_type"])
        position_str = _text(card, HUTDB_SELECTORS["position"])
        team_str = _text(card, HUTDB_SELECTORS["team"])

        if not name or not overall_str:
            return None

        try:
            overall = int(re.sub(r"\D", "", overall_str))
        except ValueError:
            return None

        first, last = _split_name(name)

        return {
            "ea_id": str(ea_id).strip() if ea_id else None,
            "first_name": first,
            "last_name": last,
            "full_name": name.strip(),
            "overall": overall,
            "card_type": map_card_type(card_type_str) if card_type_str else "BASE",
            "position": map_position(position_str) if position_str else "C",
            "team_name": team_str.strip() if team_str else None,
            "team_abbrev": None,
            "league_name": "NHL",
            "league_abbrev": "NHL",
            "image_url": _img_src(card, HUTDB_SELECTORS["card_image"]),
            "detail_url": detail_url,
            "nationality": "CAN",
            "handedness": "RIGHT",
            "stats": {},
            "prices": [],
            "season": SEASON,
        }

    def _parse_html_detail(self, html: str, url: str) -> dict:
        """Parse a player detail page (HTML fallback)."""
        soup = BeautifulSoup(html, "lxml")
        detail: dict[str, Any] = {"detail_url": url}

        # Image
        detail["image_url"] = _img_src(soup, HUTDB_SELECTORS["card_image"])

        # Stats
        stats: dict[str, int] = {}
        detailed: dict[str, int] = {}
        stat_blocks = _find_first(soup, HUTDB_SELECTORS["stat_block"])

        for block in stat_blocks:
            rows = _find_first(block, HUTDB_SELECTORS["stat_row"])
            for row in rows:
                text_parts = [t.strip() for t in row.get_text(separator="|").split("|") if t.strip()]
                if len(text_parts) < 2:
                    continue
                label = text_parts[0].lower()
                value_str = text_parts[-1]
                try:
                    value = int(re.sub(r"\D", "", value_str))
                except ValueError:
                    continue

                field = STAT_FIELD_MAP.get(label)
                if field and field in TOP_LEVEL_STATS:
                    stats[field] = value
                else:
                    # Store as detailed stat
                    detailed[label] = value

        detail["stats"] = stats
        detail["detailed_stats"] = detailed if detailed else None

        # Prices
        prices: list[dict] = []
        price_blocks = _find_first(soup, HUTDB_SELECTORS["price_block"])
        for pb in price_blocks:
            platform_tag = _find_first_tag(pb, HUTDB_SELECTORS["price_platform"])
            value_tag = _find_first_tag(pb, HUTDB_SELECTORS["price_value"])
            if value_tag:
                raw_val = re.sub(r"[^\d]", "", value_tag.get_text())
                if raw_val:
                    platform = platform_tag.get_text(strip=True) if platform_tag else self.platform
                    prices.append({"platform": platform, "price": int(raw_val)})
        detail["prices"] = prices

        return detail


# ── Utility functions ─────────────────────────────────────────────────────────

def _split_name(full: str) -> tuple[str, str]:
    """Split 'Connor McDavid' → ('Connor', 'McDavid').  Handles single names."""
    parts = full.strip().split(None, 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return parts[0], ""


def _normalize_hand(raw: str) -> str:
    r = raw.lower()
    if "left" in r or r == "l":
        return "LEFT"
    return "RIGHT"


def _extract_stats_from_dict(raw: dict) -> dict[str, int]:
    """Pull top-level stats from a raw dict, tolerating various key names."""
    stats: dict[str, int] = {}
    for raw_key, field in STAT_FIELD_MAP.items():
        if field not in TOP_LEVEL_STATS:
            continue
        for variant in (raw_key, raw_key.upper(), field, field.lower()):
            val = raw.get(variant)
            if val is not None:
                try:
                    stats[field] = int(val)
                except (TypeError, ValueError):
                    pass
                break
    return stats


def _extract_prices_from_dict(raw: dict, default_platform: str) -> list[dict]:
    """Extract price information from a raw dict."""
    prices: list[dict] = []
    # Common structures: {"ps5Price": 12000, "xboxPrice": 11500} or {"prices": [...]}
    platform_keys = {
        "ps5Price": "PS5", "ps5": "PS5", "psPrice": "PS5",
        "xboxPrice": "XBOX", "xbox": "XBOX",
        "pcPrice": "PC", "pc": "PC",
    }
    for key, platform in platform_keys.items():
        val = raw.get(key) or raw.get(key.lower())
        if val:
            try:
                prices.append({"platform": platform, "price": int(val)})
            except (TypeError, ValueError):
                pass

    if not prices and raw.get("price"):
        try:
            prices.append({"platform": default_platform, "price": int(raw["price"])})
        except (TypeError, ValueError):
            pass

    return prices


def _find_first(soup: BeautifulSoup | Tag, selectors: list[str]) -> list[Tag]:
    """Try CSS selectors in order, return the first non-empty result."""
    for sel in selectors:
        try:
            results = soup.select(sel)
            if results:
                return results
        except Exception:
            continue
    return []


def _find_first_tag(element: Tag, selectors: list[str]) -> Tag | None:
    for sel in selectors:
        try:
            found = element.select_one(sel)
            if found:
                return found
        except Exception:
            continue
    return None


def _text(element: Tag, selectors: list[str]) -> str | None:
    tag = _find_first_tag(element, selectors)
    return tag.get_text(strip=True) if tag else None


def _img_src(element: Tag, selectors: list[str]) -> str | None:
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


def _extract_total_pages(soup: BeautifulSoup, selectors: dict) -> int | None:
    # Try data-total-pages attribute
    for sel in selectors["pagination_total"]:
        try:
            el = soup.select_one(sel)
            if el:
                total = el.get("data-total-pages") or el.get("data-pages")
                if total:
                    return int(total)
                # Try text content like "Page 1 of 47"
                text = el.get_text()
                match = re.search(r"of\s+(\d+)", text, re.IGNORECASE)
                if match:
                    return int(match.group(1))
        except Exception:
            continue

    # Count page links
    page_links = soup.select("a[href*='page=']")
    page_nums: list[int] = []
    for a in page_links:
        m = re.search(r"page=(\d+)", a.get("href", ""))
        if m:
            page_nums.append(int(m.group(1)))
    if page_nums:
        return max(page_nums)

    return None
