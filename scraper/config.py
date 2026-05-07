"""
Central configuration for the HUTbin scraper.
All CSS selectors live here — adjust after running: python main.py --probe
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql://hutbin:hutbin_dev_password@localhost:5432/hutbin",
)

# ── Season / URLs ─────────────────────────────────────────────────────────────
SEASON = "NHL26"
HUTDB_BASE = "https://www.hut-db.com"
HUTDB_SEASON_PREFIX = "/26"                        # e.g. /26/players
NHLHUT_BASE = "https://www.nhlhut.com"

# ── Rate limiting ─────────────────────────────────────────────────────────────
RATE_LIMIT_MIN = 1.0   # seconds between requests (lower bound)
RATE_LIMIT_MAX = 3.0   # seconds between requests (upper bound)
MAX_RETRIES = 5
BACKOFF_BASE = 5       # seconds × 2^attempt on 429

# ── Playwright fallback ───────────────────────────────────────────────────────
USE_PLAYWRIGHT_FALLBACK = True   # try Playwright if static HTML is empty
PLAYWRIGHT_TIMEOUT = 30_000     # ms

# ── Incremental threshold ────────────────────────────────────────────────────
INCREMENTAL_HOURS = 24  # skip cards updated within this many hours

# ─────────────────────────────────────────────────────────────────────────────
# CSS SELECTORS — hut-db.com
# Run `python main.py --probe` to dump the raw HTML and adjust these.
# The scraper tries the __NEXT_DATA__ JSON blob first (Next.js); if that
# fails it falls through to the selector strategy below.
# ─────────────────────────────────────────────────────────────────────────────
HUTDB_SELECTORS: dict = {
    # ── Player list page ──────────────────────────────────────────────────────
    # Container for a single player card in the grid
    "player_card": [
        "[data-player-id]",
        ".player-card",
        ".player-item",
        "li.player",
        "div.card",
    ],
    # Link to the player detail page (relative href)
    "player_link": ["a[href*='/player']", "a.player-link", "a"],
    # Overall rating number (e.g. "99")
    "overall": [".ovr", ".overall", "[class*='overall']", "[class*='ovr']", "span.rating"],
    # Card type label (e.g. "Gold", "Icon", "TOTW")
    "card_type": [".card-type", ".type", "[class*='type']", "span.badge"],
    # Player full name
    "name": [".player-name", ".name", "h3", "h4", "[class*='name']"],
    # Position
    "position": [".position", ".pos", "[class*='position']", "span.pos"],
    # Team name or abbreviation
    "team": [".team", ".team-name", "[class*='team']", "span.club"],
    # Pagination: element containing total page count or next-page link
    "pagination_total": ["[data-total-pages]", ".pagination", "nav.pages", ".pager"],
    "pagination_next": ["a[rel='next']", ".next", "a[aria-label='Next']", ".pagination-next a"],

    # ── Player detail page ────────────────────────────────────────────────────
    # Top-level stats block (skating, shooting, etc.)
    "stat_block": [".stats", ".player-stats", "[class*='stats']", "ul.attributes"],
    # Individual stat row — must contain label + value
    "stat_row": ["li", "tr", "div.stat", "[class*='stat-']"],
    # Image element on the detail page
    "card_image": ["img.player-image", "img.card-img", ".player-card img", "img[src*='player']"],
    # Price block (may not exist — hut-db shows community prices)
    "price_block": [".price", "[class*='price']", ".market-price"],
    "price_platform": [".platform", "[data-platform]"],
    "price_value": [".price-value", ".avg", "span.value"],
}

# ─────────────────────────────────────────────────────────────────────────────
# __NEXT_DATA__ key paths  (dot-notation, tried in order)
# These are educated guesses for a Next.js site — probe will show what's real.
# ─────────────────────────────────────────────────────────────────────────────
NEXTDATA_PLAYER_LIST_PATHS = [
    "props.pageProps.players",
    "props.pageProps.data.players",
    "props.pageProps.cards",
    "props.pageProps.data",
]
NEXTDATA_PAGINATION_PATHS = [
    "props.pageProps.pagination",
    "props.pageProps.meta",
    "props.pageProps.data.meta",
]

# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────
LOG_PATH = Path(__file__).parent / "scraper.log"

def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    root = logging.getLogger()
    root.setLevel(level)

    # Console
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(logging.Formatter(fmt))
    root.addHandler(ch)

    # Rotating file (5 MB × 3 backups)
    fh = RotatingFileHandler(LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=3)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(fmt))
    root.addHandler(fh)
