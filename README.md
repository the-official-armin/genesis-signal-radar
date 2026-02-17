# Genesis Signal Radar

Genesis Signal Radar is a **no-AI scraping + lead intelligence pipeline** for the Genesis Launchpad sales motion.

It continuously discovers people on Reddit and X who are:
- prelaunch and validating ideas
- asking where to find customers
- struggling with go-to-market, outbound, or pipeline creation
- actively searching for tools/services to understand their market

The goal is simple: **log high-intent prospects with contact paths (DM/email) for Genesis outreach.**

## What this ships
- Real-time/interval scraping from Reddit + X.
- Deterministic rule-based signal classification (no LLM/API inference).
- Buying-intent, urgency, and signal-strength scoring using transparent heuristics.
- Contact extraction (emails in post text when available).
- Outreach channel tagging (`email`, `dm_x`, `dm_reddit`).
- Lead exports to:
  - `data/raw_posts.jsonl` (all scraped posts)
  - `data/lead_signals.jsonl` (enriched leads)
  - `data/lead_signals.csv` (CRM-ready export)

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Environment variables:
```bash
# Reddit API (required for Reddit scraping)
export REDDIT_CLIENT_ID=...
export REDDIT_CLIENT_SECRET=...
export REDDIT_USER_AGENT="genesis-signal-radar/1.0"
```

## Usage
Single run:
```bash
python signal_radar.py \
  --terms "prelaunch" "customer discovery" "need leads" "find users" \
  --subreddits startups SaaS Entrepreneur smallbusiness \
  --limit 30 \
  --min-intent 3
```

Continuous polling every 5 minutes:
```bash
python signal_radar.py \
  --terms "prelaunch" "validate my idea" "where to find customers" \
  --poll-seconds 300 \
  --limit 20 \
  --min-intent 4
```

## Data model (lead export)
Each lead row includes:
- `platform`, `author`, `author_profile_url`, `source_url`
- `signal_type`, `buying_intent`, `urgency`, `signal_strength`, `icp`
- `outreach_channel`, `emails_found`, `outreach_hook`
- `matched_terms`, `content_excerpt`

## Notes
- X scraping uses `snscrape` (no official X API key), and reliability can vary.
- Reddit requires API credentials.
- This repo intentionally avoids AI inference in the core pipeline.
