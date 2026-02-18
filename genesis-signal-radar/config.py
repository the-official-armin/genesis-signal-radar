"""
Signal Radar - Configuration
Credentials, search keywords, and scoring thresholds for pre-launch / market validation signals.
"""

import os
from pathlib import Path

# Load .env if present (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# --- Paths ---
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_POSTS_PATH = DATA_DIR / "raw_posts.json"
PROCESSED_PATH = DATA_DIR / "processed_posts.json"
HOT_COMPANIES_CSV = DATA_DIR / "hot_companies.csv"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# --- Reddit: public API, no credentials needed ---
# Reddit asks for a descriptive User-Agent; optional override via env
REDDIT_USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "SignalRadar/1.0 (pre-launch signal finder)")

# --- Scraping settings (safe delays to avoid rate limits) ---
BETWEEN_REQUESTS_SEC = 2
MAX_POSTS_TO_SCRAPE = 50  # Cap for MVP to keep runs short

# --- High-intent subreddits only (no r/offmychest etc.) ---
HIGH_INTENT_SUBREDDITS = [
    "startups",
    "Entrepreneur",
    "SaaS",
    "SideProject",
    "IndieHackers",
    "ProductManagement",
]

# --- Schedule: refresh data every N hours (for run_scheduled.py) ---
SCHEDULE_INTERVAL_HOURS = 6  # Use 6–12 for “data updated every 6–12 hours”

# --- Search keywords: pre-launch & market validation signals ---
SEARCH_KEYWORDS = [
    "validating an idea",
    "pre-launch",
    "launching soon",
    "testing product-market fit",
    "finding target customers",
    "market research for launch",
    "looking for growth opportunities",
    "exploring new markets",
    "analyzing competitors",
    "potential customer segments",
    "industry trends",
]

# --- Classifier: keyword groups for intent (MVP = keyword matching) ---
# High intent: strong pre-launch / validation language
HIGH_INTENT_KEYWORDS = [
    "pre-launch",
    "launching soon",
    "validating an idea",
    "testing product-market fit",
    "finding target customers",
    "market research for launch",
    "looking for beta testers",
    "early adopters",
    "MVP launch",
    "soft launch",
    "coming soon",
]

# Medium intent: exploratory / research
MEDIUM_INTENT_KEYWORDS = [
    "looking for growth opportunities",
    "exploring new markets",
    "analyzing competitors",
    "potential customer segments",
    "industry trends",
    "market validation",
    "customer discovery",
    "pilot program",
]

# --- Scoring weights (points per signal) ---
WEIGHT_HIGH = 100   # prelaunch_high
WEIGHT_MEDIUM = 50  # prelaunch_medium
WEIGHT_OTHER = 20   # other

# --- Sales Pressure Index (SPI) thresholds ---
SPI_HIGH_PRIORITY = 70   # SPI >= 70 -> High
SPI_MEDIUM_PRIORITY = 50  # SPI >= 50 -> Medium; else Low

# --- CSV export columns ---
EXPORT_COLUMNS = [
    "company",
    "author",
    "signal_type",
    "weight",
    "SPI",
    "priority",
    "content",
]
