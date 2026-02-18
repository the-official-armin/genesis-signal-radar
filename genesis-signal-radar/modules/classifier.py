"""
Signal Radar - Post classifier
Keyword-based classification into high / medium / other intent (no ML for MVP).
"""

from typing import Tuple

import config


def _normalize(text: str) -> str:
    """Lowercase for case-insensitive matching."""
    return (text or "").lower().strip()


def classify_post(content: str) -> Tuple[str, int]:
    """
    Classify a post by intent using keyword matching.
    Returns (signal_type, weight).
    signal_type: 'prelaunch_high' | 'prelaunch_medium' | 'other'
    weight: 100 | 50 | 20
    """
    text = _normalize(content)
    if not text:
        return "other", config.WEIGHT_OTHER

    # High intent: strong pre-launch / validation language
    for kw in config.HIGH_INTENT_KEYWORDS:
        if _normalize(kw) in text:
            return "prelaunch_high", config.WEIGHT_HIGH

    # Medium intent: exploratory / research
    for kw in config.MEDIUM_INTENT_KEYWORDS:
        if _normalize(kw) in text:
            return "prelaunch_medium", config.WEIGHT_MEDIUM

    return "other", config.WEIGHT_OTHER


def classify_posts(posts: list) -> list:
    """
    Classify each post; add signal_type and weight to each record.
    Expects list of dicts with 'content' key.
    """
    result = []
    for p in posts:
        row = dict(p)
        content = row.get("content", "")
        signal_type, weight = classify_post(content)
        row["signal_type"] = signal_type
        row["weight"] = weight
        result.append(row)
    return result
