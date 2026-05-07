# HUTbin Scraper — Setup & Usage

## Installation

```bash
cd scraper
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium      # needed only if static HTML fails
```

## Configuration

Copy the root `.env` or create `scraper/.env`:
```env
DATABASE_URL=postgresql://hutbin:hutbin_dev_password@localhost:5432/hutbin
```

All selectors are in `config.py` under `HUTDB_SELECTORS`.

## Workflow

### Step 1 — Identify real CSS selectors
```bash
python main.py --probe
```
This fetches the first page of hut-db.com, prints:
- `__NEXT_DATA__` JSON keys (if Next.js — no selector work needed!)
- All CSS classes on the page
- All `data-*` attributes
- Links matching `/player` pattern

### Step 2 — Update selectors (only if no __NEXT_DATA__)
Edit `config.py → HUTDB_SELECTORS` with the real classes you found in Step 1.

### Step 3 — Test with a small batch
```bash
python main.py --source hutdb --limit 10 --verbose
```

### Step 4 — Full scrape
```bash
# All cards, PS5 prices
python main.py --source hutdb --platform PS5

# Incremental update (skip cards updated in last 24h)
python main.py --source hutdb --incremental

# Both sources
python main.py --source all --platform PS5
```

## Export

```bash
# All cards → JSON
python main.py --export json --output exports/cards.json

# Centres only → CSV
python main.py --export csv --output exports/centres.csv --position C

# Top-tier cards
python main.py --export json --output exports/elite.json --min-overall 95

# Price history for one card
python main.py --export json --output exports/mcdavid_prices.json --card-id <card_id>
```

## File structure

| File | Role |
|------|------|
| `config.py` | All knobs: URLs, selectors, DB URL, rate limits |
| `mappers.py` | CardType / Position / Nationality normalisation |
| `base_scraper.py` | HTTP, rate-limit, retry, Next.js JSON, Playwright fallback |
| `hut_db_scraper.py` | hut-db.com pagination + parsing |
| `nhlhut_scraper.py` | nhlhut.com (bonus) |
| `db_writer.py` | PostgreSQL upserts (League→Team→Player→Card→Prices) |
| `export.py` | JSON / CSV export from DB |
| `main.py` | CLI entry point |
| `scraper.log` | Rotating log (auto-created, 5 MB × 3) |
