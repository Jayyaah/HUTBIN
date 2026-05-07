"""
Abstract base class for all HUTbin scrapers.
Handles: session management, rate limiting, retry with exponential backoff,
Next.js __NEXT_DATA__ extraction, and optional Playwright fallback.
"""
from __future__ import annotations

import abc
import json
import logging
import random
import time
from typing import Any

import requests
from bs4 import BeautifulSoup

from config import (
    BACKOFF_BASE,
    MAX_RETRIES,
    PLAYWRIGHT_TIMEOUT,
    RATE_LIMIT_MAX,
    RATE_LIMIT_MIN,
    USE_PLAYWRIGHT_FALLBACK,
)

logger = logging.getLogger(__name__)

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
}


class BaseScraper(abc.ABC):
    """
    Base class providing HTTP fetching with rate limiting and retry logic.

    Subclasses must implement:
        get_all_players() -> list[dict]
        get_player_detail(url: str) -> dict
    """

    def __init__(self) -> None:
        self._session = requests.Session()
        self._session.headers.update(_BROWSER_HEADERS)
        self._last_request_time: float = 0.0

    # ── Public interface ──────────────────────────────────────────────────────

    @abc.abstractmethod
    def get_all_players(self) -> list[dict]:
        """Paginate through all players and return a list of raw dicts."""

    @abc.abstractmethod
    def get_player_detail(self, url: str) -> dict:
        """Fetch and parse a single player / card detail page."""

    # ── HTTP helpers ──────────────────────────────────────────────────────────

    def fetch_html(self, url: str) -> str:
        """
        Fetch a URL and return the response body as a string.

        Strategy:
          1. requests (static HTML)
          2. Playwright headless browser (if USE_PLAYWRIGHT_FALLBACK and content looks empty)
        """
        resp = self._fetch_requests(url)
        html = resp.text if resp else ""

        # Heuristic: if the body has almost no visible text the page is probably
        # client-side rendered — switch to Playwright.
        if USE_PLAYWRIGHT_FALLBACK and self._looks_empty(html):
            logger.info("Static HTML looks empty for %s — trying Playwright", url)
            html = self._fetch_playwright(url) or html

        return html

    def fetch_json(self, url: str) -> Any:
        """Fetch a URL and parse JSON directly (for API endpoints)."""
        resp = self._fetch_requests(url, headers={"Accept": "application/json"})
        if resp is None:
            return None
        try:
            return resp.json()
        except Exception:
            logger.warning("Response from %s is not JSON", url)
            return None

    # ── Next.js helper ────────────────────────────────────────────────────────

    @staticmethod
    def extract_next_data(html: str) -> dict:
        """
        Extract the JSON object embedded in <script id="__NEXT_DATA__"> by Next.js.
        Returns an empty dict if not found.
        """
        soup = BeautifulSoup(html, "lxml")
        tag = soup.find("script", {"id": "__NEXT_DATA__"})
        if tag and tag.string:
            try:
                return json.loads(tag.string)
            except json.JSONDecodeError as exc:
                logger.warning("Failed to parse __NEXT_DATA__: %s", exc)
        return {}

    @staticmethod
    def dig(data: dict, dotpath: str) -> Any:
        """
        Traverse a nested dict using dot-notation.
        E.g. dig(d, "props.pageProps.players") → d["props"]["pageProps"]["players"]
        Returns None if any key is missing.
        """
        obj: Any = data
        for key in dotpath.split("."):
            if not isinstance(obj, dict):
                return None
            obj = obj.get(key)
        return obj

    # ── Probe / debug helper ──────────────────────────────────────────────────

    def probe(self, url: str) -> None:
        """
        Fetch a page and print diagnostic information to help identify selectors.
        Run via: python main.py --probe
        """
        print(f"\n{'='*70}")
        print(f"PROBE: {url}")
        print(f"{'='*70}\n")

        html = self.fetch_html(url)
        if not html:
            print("[ERROR] Could not fetch page.")
            return

        soup = BeautifulSoup(html, "lxml")

        # 1. Check for Next.js data
        next_data = self.extract_next_data(html)
        if next_data:
            print("✅ __NEXT_DATA__ found! Keys at props.pageProps:")
            page_props = self.dig(next_data, "props.pageProps") or {}
            for k, v in page_props.items():
                preview = str(v)[:120]
                print(f"  • {k}: {preview}")
            print()
            print("Full __NEXT_DATA__ (first 3000 chars):")
            print(json.dumps(next_data, indent=2)[:3000])
        else:
            print("❌ No __NEXT_DATA__ — static HTML parsing needed.\n")

        # 2. All unique class names (top 30)
        classes: set[str] = set()
        for tag in soup.find_all(class_=True):
            for c in tag.get("class", []):
                classes.add(c)
        print(f"\nUnique CSS classes ({len(classes)} total, showing first 50):")
        for c in sorted(classes)[:50]:
            print(f"  .{c}")

        # 3. data-* attributes
        data_attrs: set[str] = set()
        for tag in soup.find_all(True):
            for attr in tag.attrs:
                if attr.startswith("data-"):
                    data_attrs.add(f"{attr}={tag[attr]!r}")
        if data_attrs:
            print(f"\ndata-* attributes (first 30):")
            for a in sorted(data_attrs)[:30]:
                print(f"  {a}")

        # 4. First <a> links that look like player URLs
        print("\nLinks containing 'player' or 'card':")
        for a in soup.find_all("a", href=True)[:50]:
            href = a["href"]
            if any(k in href.lower() for k in ("player", "card", "/26/")):
                print(f"  {href}")

        # 5. Raw HTML (truncated)
        print(f"\n--- RAW HTML (first 4000 chars) ---\n{html[:4000]}")

    # ── Private ───────────────────────────────────────────────────────────────

    def _rate_limit(self) -> None:
        """Enforce minimum delay between requests."""
        elapsed = time.monotonic() - self._last_request_time
        wait = random.uniform(RATE_LIMIT_MIN, RATE_LIMIT_MAX)
        if elapsed < wait:
            time.sleep(wait - elapsed)
        self._last_request_time = time.monotonic()

    def _fetch_requests(
        self,
        url: str,
        headers: dict | None = None,
    ) -> requests.Response | None:
        self._rate_limit()
        for attempt in range(MAX_RETRIES):
            try:
                resp = self._session.get(
                    url,
                    headers=headers,
                    timeout=30,
                    allow_redirects=True,
                )
                if resp.status_code == 429:
                    wait = BACKOFF_BASE * (2 ** attempt)
                    logger.warning("429 rate-limited on %s — sleeping %ds", url, wait)
                    time.sleep(wait)
                    continue
                if resp.status_code == 404:
                    logger.warning("404 Not Found: %s", url)
                    return None
                resp.raise_for_status()
                logger.debug("GET %s → %d (%d bytes)", url, resp.status_code, len(resp.content))
                return resp
            except requests.RequestException as exc:
                wait = 2 ** attempt
                logger.warning("Request failed (%s) attempt %d/%d, retrying in %ds",
                               exc, attempt + 1, MAX_RETRIES, wait)
                time.sleep(wait)
        logger.error("Exhausted retries for %s", url)
        return None

    def _fetch_playwright(self, url: str) -> str | None:
        try:
            from playwright.sync_api import sync_playwright  # lazy import
        except ImportError:
            logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
            return None

        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_extra_http_headers(_BROWSER_HEADERS)
                page.goto(url, timeout=PLAYWRIGHT_TIMEOUT, wait_until="networkidle")
                html = page.content()
                browser.close()
                return html
        except Exception as exc:
            logger.error("Playwright failed for %s: %s", url, exc)
            return None

    @staticmethod
    def _looks_empty(html: str) -> bool:
        """Heuristic: less than 2 KB of useful content suggests a JS-rendered SPA."""
        if len(html) < 2000:
            return True
        soup = BeautifulSoup(html, "lxml")
        body = soup.body
        text = body.get_text(strip=True) if body else ""
        return len(text) < 500
