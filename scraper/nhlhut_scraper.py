"""
Bonus scraper for https://www.nhlhut.com
Structure may differ significantly from hut-db.com.
Run `python main.py --probe --source nhlhut` to inspect.
"""
from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from base_scraper import BaseScraper
from config import NHLHUT_BASE, SEASON
from mappers import STAT_FIELD_MAP, TOP_LEVEL_STATS, map_card_type, map_nationality, map_position
from hut_db_scraper import _split_name, _normalize_hand, _find_first, _find_first_tag, _text, _img_src

logger = logging.getLogger(__name__)

# nhlhut.com selectors (adjust after --probe)
_SELECTORS: dict[str, list[str]] = {
    "player_card": [".player", ".player-card", ".card", "[data-id]"],
    "player_link": ["a[href*='/player']", "a"],
    "overall":     [".ovr", ".overall", ".rating"],
    "card_type":   [".type", ".card-type", ".badge"],
    "name":        [".name", ".player-name", "h3"],
    "position":    [".position", ".pos"],
    "team":        [".team", ".club"],
}


class NhlHutScraper(BaseScraper):
    """Scrapes player cards from nhlhut.com."""

    def __init__(self, platform: str = "PS5") -> None:
        super().__init__()
        self.platform = platform

    # ── Public API ────────────────────────────────────────────────────────────

    def get_all_players(self) -> list[dict]:
        results: list[dict] = []
        page = 1

        while True:
            url = f"{NHLHUT_BASE}/players?page={page}"
            logger.info("nhlhut page %d — %s", page, url)

            html = self.fetch_html(url)
            if not html:
                break

            # Try Next.js JSON
            next_data = self.extract_next_data(html)
            if next_data:
                players = self._parse_nextdata(next_data)
            else:
                players = self._parse_html(html, url)

            if not players:
                break

            results.extend(players)
            logger.info("  → %d players", len(players))
            page += 1

        return results

    def get_player_detail(self, url: str) -> dict:
        html = self.fetch_html(url)
        if not html:
            return {}
        next_data = self.extract_next_data(html)
        if next_data:
            raw = (
                self.dig(next_data, "props.pageProps.player")
                or self.dig(next_data, "props.pageProps.data")
                or {}
            )
            return self._normalize(raw) or {}
        return self._parse_html_detail(html, url)

    def probe_page(self) -> None:
        self.probe(f"{NHLHUT_BASE}/players")

    # ── Parsers ───────────────────────────────────────────────────────────────

    def _parse_nextdata(self, data: dict) -> list[dict]:
        for path in ("props.pageProps.players", "props.pageProps.data.players", "props.pageProps.data"):
            raw = self.dig(data, path)
            if isinstance(raw, list):
                return [r for r in (self._normalize(p) for p in raw) if r]
        return []

    def _normalize(self, raw: dict) -> dict | None:
        if not isinstance(raw, dict):
            return None

        def get(*keys: str) -> Any:
            for k in keys:
                if raw.get(k) is not None:
                    return raw[k]
            return None

        name = get("name", "fullName", "full_name")
        overall = get("overall", "ovr", "rating")
        if not name or not overall:
            return None

        first, last = _split_name(str(name))
        card_type = get("cardType", "card_type", "type")
        position = get("position", "pos")
        team = get("team", "teamName", "club")
        detail_url = get("url", "href", "slug")
        if detail_url and not str(detail_url).startswith("http"):
            detail_url = urljoin(NHLHUT_BASE, str(detail_url))

        stats: dict[str, int] = {}
        for raw_key, field in STAT_FIELD_MAP.items():
            if field not in TOP_LEVEL_STATS:
                continue
            for variant in (raw_key, raw_key.upper(), field):
                val = raw.get(variant)
                if val is not None:
                    try:
                        stats[field] = int(val)
                    except (TypeError, ValueError):
                        pass
                    break

        return {
            "ea_id": str(get("eaId", "ea_id", "id") or ""),
            "first_name": first,
            "last_name": last,
            "full_name": str(name),
            "overall": int(overall),
            "card_type": map_card_type(str(card_type)) if card_type else "BASE",
            "position": map_position(str(position)) if position else "C",
            "team_name": str(team) if team else None,
            "team_abbrev": get("teamAbbrev", "abbrev"),
            "league_name": "NHL",
            "league_abbrev": "NHL",
            "image_url": str(get("imageUrl", "image_url", "image") or ""),
            "detail_url": detail_url,
            "nationality": map_nationality(str(get("nationality", "country") or "")),
            "handedness": _normalize_hand(str(get("shoots", "hand") or "")),
            "stats": stats,
            "prices": [],
            "season": SEASON,
        }

    def _parse_html(self, html: str, base_url: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        players = []
        cards = _find_first(soup, _SELECTORS["player_card"])
        for card in cards:
            name = _text(card, _SELECTORS["name"])
            overall_str = _text(card, _SELECTORS["overall"])
            if not name or not overall_str:
                continue
            try:
                overall = int(re.sub(r"\D", "", overall_str))
            except ValueError:
                continue

            link_tag = _find_first_tag(card, _SELECTORS["player_link"])
            href = link_tag["href"] if link_tag else None
            detail_url = (
                urljoin(base_url, str(href))
                if href and not str(href).startswith("http")
                else href
            )

            first, last = _split_name(name)
            players.append({
                "ea_id": card.get("data-id") or card.get("data-player-id"),
                "first_name": first,
                "last_name": last,
                "full_name": name.strip(),
                "overall": overall,
                "card_type": map_card_type(_text(card, _SELECTORS["card_type"]) or ""),
                "position": map_position(_text(card, _SELECTORS["position"]) or ""),
                "team_name": _text(card, _SELECTORS["team"]),
                "team_abbrev": None,
                "league_name": "NHL",
                "league_abbrev": "NHL",
                "image_url": _img_src(card, _SELECTORS.get("card_image", [])),
                "detail_url": detail_url,
                "nationality": "CAN",
                "handedness": "RIGHT",
                "stats": {},
                "prices": [],
                "season": SEASON,
            })
        return players

    def _parse_html_detail(self, html: str, url: str) -> dict:
        soup = BeautifulSoup(html, "lxml")
        stats: dict[str, int] = {}
        for label_el in soup.select("[class*='label'], [class*='stat-name'], dt"):
            label = label_el.get_text(strip=True).lower()
            value_el = label_el.find_next_sibling()
            if not value_el:
                continue
            raw_val = re.sub(r"\D", "", value_el.get_text())
            if raw_val:
                field = STAT_FIELD_MAP.get(label)
                if field and field in TOP_LEVEL_STATS:
                    stats[field] = int(raw_val)
        return {"detail_url": url, "stats": stats, "prices": []}
