"""
Signal Radar - Scoring engine
Computes Sales Pressure Index (SPI) per project/company (or per author when company is TBD).
Only receives prelaunch_high and prelaunch_medium posts (filtered upstream).
"""

from typing import List
from collections import defaultdict

import config
from utils.helpers import extract_company, normalize_author


def _aggregation_key(company: str, author: str) -> str:
    """
    Group by project when we have a company name; otherwise by author so
    TBD rows don't inflate one global bucket (per-project/author SPI).
    """
    c = (company or "").strip()
    if c and c.upper() != "TBD":
        return ("company", c.lower())
    return ("author", (author or "unknown").strip().lower() or "unknown")


def compute_spi_and_priority(classified_posts: list) -> List[dict]:
    """
    Aggregate signals per project/author. For each company (or author if company=TBD):
    sum of weights = SPI; assign priority from config thresholds.
    Returns list of records (one per project/author) with company, author, signal_type, weight, SPI, priority, content.
    """
    # Group by (company or author): list of signal dicts
    groups = defaultdict(list)

    for row in classified_posts:
        content = row.get("content", "")
        company = (row.get("company") or "").strip() or extract_company(content)
        company = company or "TBD"
        author = normalize_author(
            row.get("author_name") or row.get("author", ""),
            content,
        )
        signal_type = row.get("signal_type", "other")
        weight = int(row.get("weight", config.WEIGHT_OTHER))
        key = _aggregation_key(company, author)
        groups[key].append({
            "company": company,
            "author": author,
            "signal_type": signal_type,
            "weight": weight,
            "content": content[:500],
        })

    # One row per project/author with per-project SPI and priority
    out = []
    for key, signals in groups.items():
        spi = sum(s["weight"] for s in signals)
        if spi >= config.SPI_HIGH_PRIORITY:
            priority = "High"
        elif spi >= config.SPI_MEDIUM_PRIORITY:
            priority = "Medium"
        else:
            priority = "Low"
        first = signals[0]
        content_agg = " | ".join(s["content"] for s in signals[:3])
        out.append({
            "company": first["company"],
            "author": first["author"],
            "signal_type": first["signal_type"],
            "weight": first["weight"],
            "SPI": spi,
            "priority": priority,
            "content": content_agg,
            "signal_count": len(signals),
        })

    return out
