# Signal Radar

Finds **pre-launch / market validation opportunities** by scanning **Reddit** for relevant posts, classifying intent, and scoring companies by a Sales Pressure Index (SPI).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

No login or browser required — Reddit’s public JSON search API is used.

## Run

From project root:

```bash
python3 main.py
```

This will:

1. **Scrape** Reddit for configurable keywords (e.g. "pre-launch", "validating an idea", "testing product-market fit").
2. **Classify** each post: high intent (100 pts), medium (50 pts), other (20 pts).
3. **Extract** company and author from post content where possible.
4. **Score** companies by SPI (sum of signal weights) and set priority: High (SPI ≥ 70), Medium (≥ 50), Low otherwise.
5. **Export** results to `data/hot_companies.csv`.

Options:

- `--no-scrape` — skip scraping; only load cached data (requires existing `data/raw_posts.json`).
- `--use-cached` — use cached raw posts if present instead of scraping.
- `--max-posts N` — cap number of posts to scrape.
- `--demo` — run with mock data only; produces sample `hot_companies.csv`.

### Keep data updated every 6–12 hours

```bash
python3 run_scheduled.py           # every 6 hours (config.SCHEDULE_INTERVAL_HOURS)
python3 run_scheduled.py --hours 12
nohup python3 run_scheduled.py --hours 6 >> data/schedule.log 2>&1 &
```

Or cron: `0 */6 * * * cd /path/to/genesis-signal-radar && python3 main.py >> data/cron.log 2>&1`

## Output

- **data/raw_posts.json** — raw scraped posts.
- **data/processed_posts.json** — classified posts.
- **data/hot_companies.csv** — columns: `company`, `author`, `signal_type`, `weight`, `SPI`, `priority`, `content`.

## Project structure

- `config.py` — keywords, thresholds, Reddit User-Agent.
- `main.py` — orchestration.
- `modules/scraper.py` — Reddit scraping (public JSON API, no Selenium).
- `modules/classifier.py` — keyword-based intent classification.
- `modules/scorer.py` — SPI and priority per company.
- `modules/dashboard.py` — CSV export.
- `utils/helpers.py` — company/author extraction (regex).
- `data/` — raw and processed data, `hot_companies.csv`.

## Constraints

- Reddit public API only; no auth. Pre-launch / validation signals; modular for adding more platforms later.
