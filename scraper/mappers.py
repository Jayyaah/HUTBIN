"""
Mapping tables: raw hut-db.com labels → PostgreSQL enum strings.

PostgreSQL enums (from Prisma schema):
  Position  : C, LW, RW, D, G
  CardType  : BASE, TOTW, TOTY, EVENT, FLASHBACK, ICON, ULTIMATE, FANTASY, PROMO, HERO
  Platform  : PS5, XBOX, PC
  Trend     : UP, DOWN, STABLE
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# ── CardType ──────────────────────────────────────────────────────────────────
# Keys are lowercase stripped versions of the label found on hut-db.com.
# Add / adjust entries after running --probe if the site uses different labels.
_CARD_TYPE_MAP: dict[str, str] = {
    # Base gold cards
    "gold":                   "BASE",
    "gold rare":              "BASE",
    "gold non-rare":          "BASE",
    "gold nonrare":           "BASE",
    "base":                   "BASE",
    "regular":                "BASE",
    # Team of the Week
    "team of the week":       "TOTW",
    "totw":                   "TOTW",
    "potm":                   "TOTW",   # Player of the Month → closest
    # Team of the Year
    "team of the year":       "TOTY",
    "toty":                   "TOTY",
    # Icons (legends)
    "icon":                   "ICON",
    "legend":                 "ICON",
    "all-time":               "ICON",
    # Flashback
    "flashback":              "FLASHBACK",
    "retro":                  "FLASHBACK",
    "throwback":              "FLASHBACK",
    # Ultimate
    "ultimate":               "ULTIMATE",
    "ultimate team":          "ULTIMATE",
    # Hero
    "hero":                   "HERO",
    # Fantasy / Concept
    "fantasy":                "FANTASY",
    "fantasy team":           "FANTASY",
    "concept":                "FANTASY",
    # Team of the Season
    "team of the season":     "PROMO",
    "tots":                   "PROMO",
    "season":                 "PROMO",
    "superstar origins":      "PROMO",
    "superstar":              "PROMO",
    "game breakers":          "PROMO",
    "game changer":           "PROMO",
    "breakout":               "PROMO",
    "dynamic duo":            "PROMO",
    "power play":             "PROMO",
    # Promo
    "promo":                  "PROMO",
    "promotional":            "PROMO",
    "signature":              "PROMO",
    "nhl awards":             "PROMO",
    "awards":                 "PROMO",
    "milestone":              "PROMO",
    # Spotlight / Weekly specials
    "spotlight":              "PROMO",
    "chel week":              "PROMO",
    "hut champions":          "PROMO",
    "next gen":               "PROMO",
    "xp":                     "PROMO",
    "trade quest":            "PROMO",
    "transactions":           "PROMO",
    "grudge match":           "PROMO",
    "marquee":                "PROMO",
    "rookies":                "PROMO",
    "captains":               "PROMO",
    "chase captains":         "PROMO",
    "alumni":                 "FLASHBACK",
    "fresh ice":              "PROMO",
    "pinnacle":               "PROMO",
    "record breakers":        "PROMO",
    "combo nexus":            "PROMO",
    "hut odr szn":            "PROMO",
    "ignited":                "PROMO",
    "hut beast mode":         "PROMO",
    "faceoff: inside the nhl": "EVENT",
    "check my game":          "PROMO",
    "stars of the month":     "PROMO",
    # Event / Limited
    "event":                  "EVENT",
    "winter":                 "EVENT",
    "holiday":                "EVENT",
    "spring":                 "EVENT",
    "playoff":                "EVENT",
    "playoffs":               "EVENT",
    "draft day":              "EVENT",
    "draft":                  "EVENT",
    "all-star":               "EVENT",
    "all star":               "EVENT",
    "international":          "EVENT",
    "world juniors":          "EVENT",
    "world championship":     "EVENT",
    "stanley cup":            "EVENT",
    "heritage classic":       "EVENT",
    "stadium series":         "EVENT",
    "winter classic":         "EVENT",
    "outdoor":                "EVENT",
    "launch":                 "EVENT",
    "series":                 "EVENT",
    "power up":               "EVENT",
    "birthday":               "EVENT",
}

def map_card_type(raw: str) -> str:
    """Map a raw card type string from hut-db.com to a PostgreSQL CardType enum value."""
    key = raw.strip().lower()
    result = _CARD_TYPE_MAP.get(key)
    if result is None:
        # Partial match fallback
        for pattern, mapped in _CARD_TYPE_MAP.items():
            if pattern in key or key in pattern:
                logger.debug("Partial card-type match '%s' → '%s' via '%s'", raw, mapped, pattern)
                return mapped
        logger.warning("Unknown card type '%s', defaulting to BASE", raw)
        return "BASE"
    return result


# ── Position ──────────────────────────────────────────────────────────────────
_POSITION_MAP: dict[str, str] = {
    "c":   "C",
    "cen": "C",
    "center": "C",
    "centre": "C",
    "lw":  "LW",
    "left wing": "LW",
    "leftwing":  "LW",
    "rw":  "RW",
    "right wing": "RW",
    "rightwing":  "RW",
    "d":   "D",
    "def": "D",
    "defense": "D",
    "defence": "D",
    "defenseman": "D",
    "defenceman": "D",
    "ld":  "D",   # left defense
    "rd":  "D",   # right defense
    "g":   "G",
    "goal": "G",
    "goalie": "G",
    "goaltender": "G",
    "goalkeeper": "G",
}

def map_position(raw: str) -> str:
    """Map a raw position string to a PostgreSQL Position enum value."""
    key = raw.strip().lower()
    result = _POSITION_MAP.get(key)
    if result is None:
        logger.warning("Unknown position '%s', defaulting to C", raw)
        return "C"
    return result


# ── Platform ─────────────────────────────────────────────────────────────────
_PLATFORM_MAP: dict[str, str] = {
    "ps5":  "PS5",
    "ps":   "PS5",
    "playstation": "PS5",
    "playstation 5": "PS5",
    "xbox": "XBOX",
    "xb":   "XBOX",
    "xbone": "XBOX",
    "xbx":  "XBOX",
    "pc":   "PC",
    "computer": "PC",
}

def map_platform(raw: str) -> str:
    key = raw.strip().lower()
    result = _PLATFORM_MAP.get(key)
    if result is None:
        logger.warning("Unknown platform '%s', defaulting to PS5", raw)
        return "PS5"
    return result


# ── Nationality → ISO 3-letter ────────────────────────────────────────────────
_NATIONALITY_MAP: dict[str, str] = {
    "canada":         "CAN",
    "canadian":       "CAN",
    "united states":  "USA",
    "usa":            "USA",
    "american":       "USA",
    "russia":         "RUS",
    "russian":        "RUS",
    "sweden":         "SWE",
    "swedish":        "SWE",
    "finland":        "FIN",
    "finnish":        "FIN",
    "czech republic": "CZE",
    "czechia":        "CZE",
    "czech":          "CZE",
    "slovakia":       "SVK",
    "slovak":         "SVK",
    "germany":        "GER",
    "german":         "GER",
    "switzerland":    "SUI",
    "swiss":          "SUI",
    "austria":        "AUT",
    "austrian":       "AUT",
    "denmark":        "DEN",
    "danish":         "DEN",
    "norway":         "NOR",
    "norwegian":      "NOR",
    "latvia":         "LAT",
    "latvian":        "LAT",
    "belarus":        "BLR",
    "belarusian":     "BLR",
    "ukraine":        "UKR",
    "ukrainian":      "UKR",
    "france":         "FRA",
    "french":         "FRA",
}

def map_nationality(raw: str) -> str:
    if not raw:
        return "CAN"
    key = raw.strip().lower()
    # If already a 3-letter code
    if len(key) == 3 and key.upper() in _NATIONALITY_MAP.values():
        return key.upper()
    result = _NATIONALITY_MAP.get(key)
    if result is None:
        logger.debug("Unknown nationality '%s', defaulting to CAN", raw)
        return "CAN"
    return result


# ── Stat name normalization ───────────────────────────────────────────────────
# Maps various labels found on card detail pages to the Prisma field names.
STAT_FIELD_MAP: dict[str, str] = {
    # Top-level
    "skating":    "skating",
    "ska":        "skating",
    "skate":      "skating",
    "shooting":   "shooting",
    "sho":        "shooting",
    "shoot":      "shooting",
    "passing":    "passing",
    "pas":        "passing",
    "pass":       "passing",
    "puck skills": "puckSkills",
    "puck":       "puckSkills",
    "psk":        "puckSkills",
    "puc":        "puckSkills",
    "defense":    "defense",
    "defence":    "defense",
    "def":        "defense",
    "checking":   "checking",
    "chk":        "checking",
    "check":      "checking",
    "physical":   "physical",
    "phy":        "physical",
    "phys":       "physical",
}

TOP_LEVEL_STATS = {"skating", "shooting", "passing", "puckSkills", "defense", "checking", "physical"}
