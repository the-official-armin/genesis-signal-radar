#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

SIGNAL_RULES: Dict[str, List[str]] = {
    "Pain complaint": [
        "frustrated",
        "struggling",
        "stuck",
        "pain point",
        "this sucks",
        "problem",
    ],
    "Tool dissatisfaction": [
        "hate",
        "too expensive",
        "buggy",
        "switching from",
        "alternatives to",
        "replace",
    ],
    "Active buying search": [
        "looking for",
        "recommend",
        "any tool",
        "need software",
        "what should i use",
    ],
    "Workflow inefficiency": [
        "manual",
        "time consuming",
        "spreadsheet",
        "bottleneck",
        "inefficient",
    ],
    "Trend observation": [
        "seeing more",
        "trend",
        "everyone is",
        "market is",
        "shifting",
    ],
    "Hiring signal": [
        "hiring",
        "looking for contractor",
        "need an sdr",
        "need sales help",
    ],
    "Revenue struggle": [
        "no leads",
        "pipeline is dry",
        "no revenue",
        "can\'t close",
        "low conversion",
    ],
    "Scaling issue": [
        "can\'t scale",
        "breaking at scale",
        "too many leads",
        "follow up is hard",
    ],
    "Operational bottleneck": [
        "process is broken",
        "ops issue",
        "handoff",
        "crm mess",
    ],
}

ICP_RULES: Dict[str, List[str]] = {
    "Founder": ["founder", "startup", "cofounder", "bootstrapped", "prelaunch", "mvp"],
    "SaaS company": ["saas", "b2b software", "trial users", "churn"],
    "Agency": ["agency", "clients", "retainer", "freelance studio"],
    "Consultant": ["consultant", "advisor", "fractional"],
    "Ecommerce": ["shopify", "ecommerce", "store", "dtc", "amazon"],
    "Enterprise": ["enterprise", "procurement", "security review", "soc2"],
}

HIGH_INTENT_TERMS = [
    "need",
    "asap",
    "urgent",
    "help",
    "recommend",
    "looking for",
    "anyone know",
    "prelaunch",
    "validate",
]

VALIDATION_KEYWORDS = [
    "prelaunch",
    "beta users",
    "validating",
    "looking for feedback",
    "launching soon",
    "problem with",
    "need a better",
    "any tool for",
    "manual process",
    "where do i find",
]


@dataclass
class Post:
    platform: str
    author: str
    author_profile_url: str
    content: str
    engagement: str
    url: str
    created_at: str
    subreddit: Optional[str] = None


@dataclass
class LeadSignal:
    platform: str
    author: str
    author_profile_url: str
    source_url: str
    created_at: str
    signal_type: str
    buying_intent: int
    urgency: int
    signal_strength: int
    icp: str
    outreach_channel: str
    emails_found: str
    outreach_hook: str
    matched_terms: str
    content_excerpt: str


def now_utc_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def keyword_query(base_terms: List[str]) -> str:
    term_query = " OR ".join(f'"{t}"' for t in base_terms)
    validation = " OR ".join(f'"{k}"' for k in VALIDATION_KEYWORDS)
    return f"({term_query}) ({validation})"


def extract_emails(text: str) -> List[str]:
    return sorted(set(EMAIL_REGEX.findall(text or "")))


def matched_keywords(text: str, terms: List[str]) -> List[str]:
    lower = (text or "").lower()
    return [term for term in terms if term.lower() in lower]


def classify_signal_type(text: str) -> Tuple[str, List[str]]:
    lower = (text or "").lower()
    best_type = "Other"
    best_hits: List[str] = []
    for signal_type, rules in SIGNAL_RULES.items():
        hits = [rule for rule in rules if rule in lower]
        if len(hits) > len(best_hits):
            best_type = signal_type
            best_hits = hits
    return best_type, best_hits


def classify_icp(text: str) -> str:
    lower = (text or "").lower()
    best_icp = "Other"
    best_score = 0
    for icp, rules in ICP_RULES.items():
        score = sum(1 for rule in rules if rule in lower)
        if score > best_score:
            best_score = score
            best_icp = icp
    return best_icp


def score_buying_intent(text: str) -> int:
    lower = (text or "").lower()
    matches = sum(1 for t in HIGH_INTENT_TERMS if t in lower)
    q_bonus = 1 if "?" in lower else 0
    score = 1 + min(4, matches + q_bonus)
    return max(1, min(5, score))


def score_urgency(text: str) -> int:
    lower = (text or "").lower()
    urgency_terms = ["asap", "urgent", "immediately", "today", "now", "this week"]
    score = 1 + sum(1 for t in urgency_terms if t in lower)
    return max(1, min(5, score))


def score_signal_strength(buying_intent: int, urgency: int, engagement: str, matched_rule_count: int) -> int:
    digits = [int(x) for x in re.findall(r"\d+", engagement or "")]
    engagement_score = 0
    if digits:
        total = sum(digits)
        if total >= 100:
            engagement_score = 3
        elif total >= 25:
            engagement_score = 2
        elif total >= 5:
            engagement_score = 1
    raw = buying_intent + urgency + engagement_score + min(2, matched_rule_count)
    return max(1, min(10, raw))


def outreach_channel_for(post: Post, emails: List[str]) -> str:
    if emails:
        return "email"
    if post.platform == "X":
        return "dm_x"
    if post.platform == "Reddit":
        return "dm_reddit"
    return "unknown"


def build_outreach_hook(signal_type: str, icp: str, text: str) -> str:
    snippet = " ".join((text or "").strip().split())[:120]
    return (
        f"Saw your post about {signal_type.lower()} ({icp}). "
        f"Genesis builds market snapshots + outbound-ready lead insights for prelaunch teams. "
        f"Happy to share a focused snapshot from your category. Context: '{snippet}...'"
    )


class RedditSource:
    def __init__(self):
        self.available = False
        self.client = None
        try:
            import praw  # type: ignore

            cid = os.getenv("REDDIT_CLIENT_ID")
            secret = os.getenv("REDDIT_CLIENT_SECRET")
            agent = os.getenv("REDDIT_USER_AGENT", "genesis-signal-radar/1.0")
            if cid and secret:
                self.client = praw.Reddit(client_id=cid, client_secret=secret, user_agent=agent)
                self.available = True
        except Exception:
            self.available = False

    def search(self, subreddits: List[str], terms: List[str], limit: int) -> List[Post]:
        if not self.available:
            return []

        query = keyword_query(terms)
        results: List[Post] = []
        for sub in subreddits:
            for post in self.client.subreddit(sub).search(query, sort="new", limit=limit):
                author = str(post.author) if post.author else "[deleted]"
                results.append(
                    Post(
                        platform="Reddit",
                        subreddit=sub,
                        author=author,
                        author_profile_url=f"https://reddit.com/user/{author}" if author != "[deleted]" else "",
                        engagement=f"score={post.score},comments={post.num_comments}",
                        content=(post.title or "") + "\n" + (post.selftext or ""),
                        url=f"https://reddit.com{post.permalink}",
                        created_at=datetime.fromtimestamp(post.created_utc, tz=timezone.utc).isoformat(),
                    )
                )
        return results


class XSource:
    def __init__(self):
        self.available = False
        self.scraper = None
        try:
            import snscrape.modules.twitter as sntwitter  # type: ignore

            self.scraper = sntwitter
            self.available = True
        except Exception:
            self.available = False

    def search(self, terms: List[str], limit: int) -> List[Post]:
        if not self.available:
            return []

        query = keyword_query(terms) + " lang:en"
        results: List[Post] = []
        for i, tweet in enumerate(self.scraper.TwitterSearchScraper(query).get_items()):
            if i >= limit:
                break
            username = tweet.user.username
            results.append(
                Post(
                    platform="X",
                    author=username,
                    author_profile_url=f"https://x.com/{username}",
                    content=tweet.rawContent,
                    engagement=f"likes={tweet.likeCount},replies={tweet.replyCount},retweets={tweet.retweetCount}",
                    url=tweet.url,
                    created_at=tweet.date.astimezone(timezone.utc).isoformat(),
                )
            )
        return results


def dedupe(posts: List[Post]) -> List[Post]:
    seen = set()
    out: List[Post] = []
    for p in posts:
        if p.url in seen:
            continue
        seen.add(p.url)
        out.append(p)
    return out


def post_to_lead_signal(post: Post, market_terms: List[str]) -> LeadSignal:
    signal_type, rule_hits = classify_signal_type(post.content)
    buying_intent = score_buying_intent(post.content)
    urgency = score_urgency(post.content)
    signal_strength = score_signal_strength(buying_intent, urgency, post.engagement, len(rule_hits))
    icp = classify_icp(post.content)
    emails = extract_emails(post.content)
    outreach_channel = outreach_channel_for(post, emails)
    terms = matched_keywords(post.content, market_terms + VALIDATION_KEYWORDS)

    return LeadSignal(
        platform=post.platform,
        author=post.author,
        author_profile_url=post.author_profile_url,
        source_url=post.url,
        created_at=post.created_at,
        signal_type=signal_type,
        buying_intent=buying_intent,
        urgency=urgency,
        signal_strength=signal_strength,
        icp=icp,
        outreach_channel=outreach_channel,
        emails_found=",".join(emails),
        outreach_hook=build_outreach_hook(signal_type, icp, post.content),
        matched_terms=",".join(terms),
        content_excerpt=" ".join(post.content.split())[:220],
    )


def append_jsonl(path: Path, rows: List[dict]) -> None:
    with path.open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def append_csv(path: Path, rows: List[LeadSignal]) -> None:
    if not rows:
        return
    headers = list(asdict(rows[0]).keys())
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not exists:
            writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def run_once(args) -> None:
    reddit = RedditSource()
    xsrc = XSource()

    posts: List[Post] = []
    posts.extend(reddit.search(args.subreddits, args.terms, args.limit))
    posts.extend(xsrc.search(args.terms, args.limit))
    posts = dedupe(posts)

    lead_signals = [post_to_lead_signal(p, args.terms) for p in posts]
    if args.min_intent:
        lead_signals = [s for s in lead_signals if s.buying_intent >= args.min_intent]

    append_jsonl(Path(args.raw_output), [asdict(p) for p in posts])
    append_jsonl(Path(args.leads_output), [asdict(s) for s in lead_signals])
    append_csv(Path(args.leads_csv), lead_signals)

    print(f"[{now_utc_iso()}] fetched_posts={len(posts)} leads_logged={len(lead_signals)}")
    for s in sorted(lead_signals, key=lambda x: (x.signal_strength, x.buying_intent, x.urgency), reverse=True)[:10]:
        print(
            f"- {s.platform} @{s.author} | signal={s.signal_type} | intent={s.buying_intent} | "
            f"urgency={s.urgency} | strength={s.signal_strength} | channel={s.outreach_channel}"
        )



def main():
    parser = argparse.ArgumentParser(
        description="Genesis Signal Radar: scrape Reddit/X and log contactable prelaunch + market snapshot demand signals"
    )
    parser.add_argument("--terms", nargs="+", required=True, help="Market terms to monitor")
    parser.add_argument(
        "--subreddits",
        nargs="+",
        default=["startups", "SaaS", "Entrepreneur", "smallbusiness"],
        help="Subreddits to search",
    )
    parser.add_argument("--limit", type=int, default=25, help="Max posts per platform per poll")
    parser.add_argument("--poll-seconds", type=int, default=0, help="If >0, poll continuously")
    parser.add_argument("--min-intent", type=int, default=3, help="Only log leads with buying intent >= this score (1-5)")
    parser.add_argument("--raw-output", default="data/raw_posts.jsonl", help="Path to append raw scraped posts")
    parser.add_argument("--leads-output", default="data/lead_signals.jsonl", help="Path to append enriched lead signals")
    parser.add_argument("--leads-csv", default="data/lead_signals.csv", help="Path to append CSV lead export")
    args = parser.parse_args()

    Path("data").mkdir(exist_ok=True)

    if args.poll_seconds > 0:
        while True:
            run_once(args)
            time.sleep(args.poll_seconds)
    else:
        run_once(args)


if __name__ == "__main__":
    main()
