"""
Signal Radar - Reddit post scraper
Uses Reddit's public JSON search API. Only scrapes high-intent subreddits.
No login, no Selenium.
"""

import json
import time
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote, urljoin

import config

# Subreddit search: restrict_sr=on keeps results inside that subreddit
REDDIT_SUBREDDIT_SEARCH_TEMPLATE = "https://www.reddit.com/r/{subreddit}/search.json"


def _fetch_subreddit_search(subreddit: str, keyword: str, limit: int = 25) -> List[dict]:
    """
    Fetch one page of search results from a single subreddit.
    Returns list of post dicts with content, author_name, subreddit, etc.
    """
    try:
        import urllib.request
        url = (
            REDDIT_SUBREDDIT_SEARCH_TEMPLATE.format(subreddit=quote(subreddit, safe=""))
            + f"?q={quote(keyword)}&restrict_sr=on&limit={min(limit, 100)}&sort=relevance"
        )
        req = urllib.request.Request(url, headers={"User-Agent": config.REDDIT_USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        if getattr(config, "DEBUG", True):
            print(f"  [debug] Reddit r/{subreddit} search failed for {keyword!r}: {e}")
        return []
    children = data.get("data", {}).get("children", [])
    out = []
    for child in children:
        d = child.get("data", {})
        title = (d.get("title") or "").strip()
        selftext = (d.get("selftext") or "").strip()
        content = f"{title}\n{selftext}".strip() or title
        if not content or len(content) < 10:
            continue
        author = d.get("author") or "[deleted]"
        if author == "[deleted]":
            author = "TBD"
        permalink = d.get("permalink") or ""
        post_url = urljoin("https://www.reddit.com", permalink) if permalink else ""
        sub = (d.get("subreddit") or "").strip()
        out.append({
            "content": content[:3000],
            "author_name": author,
            "author_profile_link": f"https://www.reddit.com/user/{author}" if author != "TBD" else "",
            "post_url": post_url,
            "subreddit": sub,
            "keyword_matched": keyword,
            "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
    return out


def scrape_posts(
    keywords: Optional[List[str]] = None,
    subreddits: Optional[List[str]] = None,
    max_posts: Optional[int] = None,
    save_path: Optional[Path] = None,
    debug: bool = True,
) -> List[dict]:
    """
    Search Reddit only in high-intent subreddits (r/startups, r/Entrepreneur, etc.).
    For each subreddit + keyword, fetches posts and dedupes by content.
    Returns list of post dicts. No login required.
    """
    keywords = keywords or config.SEARCH_KEYWORDS
    subreddits = subreddits or getattr(config, "HIGH_INTENT_SUBREDDITS", ["startups", "Entrepreneur"])
    max_posts = max_posts or config.MAX_POSTS_TO_SCRAPE
    save_path = save_path or config.RAW_POSTS_PATH
    delay_sec = getattr(config, "BETWEEN_REQUESTS_SEC", 2)

    all_posts: List[dict] = []
    seen_hashes: set = set()

    for subreddit in subreddits:
        if len(all_posts) >= max_posts:
            break
        for keyword in keywords:
            if len(all_posts) >= max_posts:
                break
            if debug:
                print(f"Searching r/{subreddit}: {keyword!r}")
            posts = _fetch_subreddit_search(
                subreddit, keyword,
                limit=min(25, max_posts - len(all_posts) + 5),
            )
            for p in posts:
                if len(all_posts) >= max_posts:
                    break
                h = hash(p["content"][:400])
                if h in seen_hashes:
                    continue
                seen_hashes.add(h)
                all_posts.append(p)
            time.sleep(delay_sec)

    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(all_posts, f, indent=2, ensure_ascii=False)

    return all_posts


def load_raw_posts(path: Optional[Path] = None) -> List[dict]:
    """Load previously scraped raw posts from JSON."""
    path = path or config.RAW_POSTS_PATH
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
