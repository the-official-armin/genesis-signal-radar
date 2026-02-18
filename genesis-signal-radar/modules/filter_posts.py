"""
Signal Radar - Post filter
Keeps only high/medium intent posts (prelaunch_high, prelaunch_medium) for scoring and export.
"""

from typing import List, Tuple

# Only these signal types are kept; "other" is dropped
ALLOWED_SIGNAL_TYPES: Tuple[str, ...] = ("prelaunch_high", "prelaunch_medium")


def filter_by_signal_type(classified_posts: List[dict], allowed: Tuple[str, ...] = None) -> List[dict]:
    """
    Keep only posts whose signal_type is in allowed (default: prelaunch_high, prelaunch_medium).
    Drops irrelevant posts (signal_type = other) so CSV is actionable.
    """
    allowed = allowed or ALLOWED_SIGNAL_TYPES
    return [p for p in classified_posts if (p.get("signal_type") or "").strip() in allowed]
