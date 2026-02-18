"""
Signal Radar - Main orchestration
Run this script to: scrape Reddit (or load cached), classify, score, and export hot_companies.csv.
"""

import json
import argparse
from pathlib import Path

# Project root is expected as cwd or in PYTHONPATH
import config
from modules.scraper import scrape_posts, load_raw_posts
from modules.classifier import classify_posts
from modules.filter_posts import filter_by_signal_type
from modules.scorer import compute_spi_and_priority
from modules.dashboard import export_hot_companies


def run_pipeline(
    scrape: bool = True,
    max_posts: int = None,
    use_cached_raw: bool = False,
) -> Path:
    """
    Full pipeline: scrape (or load) -> classify -> score -> export CSV.
    Returns path to hot_companies.csv.
    """
    max_posts = max_posts or config.MAX_POSTS_TO_SCRAPE

    # Step 1: Get raw posts (scrape or load from previous run)
    if use_cached_raw and config.RAW_POSTS_PATH.exists():
        print("Loading cached raw posts from", config.RAW_POSTS_PATH)
        raw_posts = load_raw_posts()
    elif scrape:
        print("Scraping Reddit for pre-launch / validation keywords...")
        raw_posts = scrape_posts(max_posts=max_posts)
        print(f"Scraped {len(raw_posts)} posts.")
    else:
        raw_posts = load_raw_posts()
        if not raw_posts:
            print("No raw posts found. Run with --scrape or run once with --scrape to populate data/raw_posts.json")
            return config.HOT_COMPANIES_CSV

    if not raw_posts:
        print("No posts to process. Exporting empty CSV.")
        export_hot_companies([])
        return config.HOT_COMPANIES_CSV

    # Step 2: Classify each post (keyword-based intent + weight)
    print("Classifying posts by intent...")
    classified = classify_posts(raw_posts)
    with open(config.PROCESSED_PATH, "w", encoding="utf-8") as f:
        json.dump(classified, f, indent=2, ensure_ascii=False)

    # Step 3: Filter — only prelaunch_high and prelaunch_medium (drop "other" for actionable CSV)
    filtered = filter_by_signal_type(classified)
    print(f"Keeping {len(filtered)} high/medium intent posts (dropped {len(classified) - len(filtered)} other).")

    # Step 4: Aggregate per project/author, compute SPI and priority
    print("Computing SPI per project/author...")
    company_rows = compute_spi_and_priority(filtered)

    # Step 5: Export to CSV (only prelaunch_high/medium; SPI per project/author)
    out_path = export_hot_companies(company_rows)
    print("Exported to", out_path)
    return out_path


def run_demo() -> Path:
    """
    Run pipeline with mock data (no Selenium). Seeds data/raw_posts.json and produces hot_companies.csv.
    """
    mock_posts = [
        {
            "content": "We at BuildRight are pre-launch and validating an idea in construction tech. Looking for beta testers!",
            "author_name": "Jane Doe",
            "author_profile_link": "",
            "keyword_matched": "pre-launch",
            "scraped_at": "2025-02-16T12:00:00Z",
        },
        {
            "content": "Launching soon: FitTrack. Testing product-market fit in health wearables. Finding target customers in EU.",
            "author_name": "TBD",
            "author_profile_link": "",
            "keyword_matched": "launching soon",
            "scraped_at": "2025-02-16T12:00:00Z",
        },
        {
            "content": "Exploring new markets and analyzing competitors. Our team at DataFlow is doing market research for launch.",
            "author_name": "Alex Smith",
            "author_profile_link": "",
            "keyword_matched": "market research for launch",
            "scraped_at": "2025-02-16T12:00:00Z",
        },
    ]
    config.RAW_POSTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(config.RAW_POSTS_PATH, "w", encoding="utf-8") as f:
        json.dump(mock_posts, f, indent=2, ensure_ascii=False)
    print("Wrote mock data to", config.RAW_POSTS_PATH)
    return run_pipeline(scrape=False, use_cached_raw=False)


def main():
    parser = argparse.ArgumentParser(description="Signal Radar: pre-launch / market validation opportunity finder (Reddit)")
    parser.add_argument("--no-scrape", action="store_true", help="Do not scrape; use cached raw_posts.json only")
    parser.add_argument("--use-cached", action="store_true", help="Use cached raw posts if present (skip scrape)")
    parser.add_argument("--demo", action="store_true", help="Run with mock data only; produces sample hot_companies.csv")
    parser.add_argument("--max-posts", type=int, default=None, help="Max posts to scrape (default from config)")
    args = parser.parse_args()

    if args.demo:
        run_demo()
        return

    run_pipeline(
        scrape=not args.no_scrape and not args.use_cached,
        max_posts=args.max_posts,
        use_cached_raw=args.use_cached,
    )


if __name__ == "__main__":
    main()
