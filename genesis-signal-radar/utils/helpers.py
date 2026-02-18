"""
Signal Radar - Helper utilities
Company and author extraction from post content using regex and simple heuristics.
"""

import re
from typing import Tuple


# Common patterns for company/project/startup names in posts (MVP: regex; can add NLP later)
# Order matters: more specific patterns first.
COMPANY_PATTERNS = [
    # "My startup XYZ is launching" / "my startup XYZ is"
    r"(?:my|our)\s+startup\s+([A-Z][A-Za-z0-9&\.\-]+(?:\s+[A-Z][A-Za-z0-9&\.\-]+){0,1})\s+(?:is|just|we're)",
    # "Pre-launch for ABC" / "pre-launch for XYZ"
    r"pre-launch\s+for\s+([A-Z][A-Za-z0-9&\.\-]+)\b",
    # "Testing product XYZ" / "testing product-market fit for XYZ"
    r"testing\s+product(?:-market\s+fit)?\s+(?:for\s+)?([A-Z][A-Za-z0-9&\.\-]+)\b",
    # "Our project XYZ" / "my project ABC"
    r"(?:my|our)\s+project\s+([A-Z][A-Za-z0-9&\.\-]+)\b",
    # "Launching XYZ" at start or after colon
    r"(?:launching|launched)\s+([A-Z][A-Za-z0-9&\.\-]+)\b",
    # "at CompanyName", "at Acme"
    r"\bat\s+([A-Z][A-Za-z0-9&\.\-]+)\b",
    # "founder of Company"
    r"(?:founder|ceo|coo|cto)\s+of\s+([A-Z][A-Za-z0-9&\.\-]+(?:\s+[A-Z][A-Za-z0-9&\.\-]+){0,2})\b",
    # "building Company", "launched Company"
    r"(?:building|launched|starting)\s+([A-Z][A-Za-z0-9&\.\-]+(?:\s+[A-Z][A-Za-z0-9&\.\-]+){0,2})\b",
    # "Company is launching/validating/testing"
    r"(?:^|\.\s)([A-Z][A-Za-z0-9&\.\-]+)\s+is\s+(?:launching|validating|testing)",
    # "we at Company", "team at Company"
    r"(?:we|our team)\s+at\s+([A-Z][A-Za-z0-9&\.\-]+)\b",
    # After colon: "Launching soon: FitTrack"
    r"(?:soon|:)\s*([A-Z][A-Za-z0-9&\.\-]+)\b",
    # Quoted company/project name
    r'"([A-Za-z0-9\s&\.\-]{2,40})"',
]

# Blacklist: words that are not company names
COMPANY_BLACKLIST = {
    "linkedin", "twitter", "facebook", "instagram", "google", "amazon",
    "market", "customer", "product", "launch", "idea", "fit", "research",
    "trends", "opportunities", "segments", "competitors", "soon", "tbd",
}


def extract_company(content: str) -> str:
    """
    Extract company name from post content using regex patterns.
    Returns first plausible match or empty string.
    """
    if not content or not isinstance(content, str):
        return ""
    text = content.strip()
    for pattern in COMPANY_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            candidate = m.strip()
            # Filter out too short or blacklisted
            if len(candidate) < 3:
                continue
            lower = candidate.lower()
            # Blacklist whole words only (so "FitTrack" is not rejected for containing "fit")
            if any(re.search(r"\b" + re.escape(b) + r"\b", lower) for b in COMPANY_BLACKLIST):
                continue
            if candidate and candidate[0].isupper():
                return candidate
    return ""


def extract_author_from_content(content: str) -> str:
    """
    Try to infer author/founder from content (e.g. 'I'm John, founder of...').
    MVP: simple regex; returns 'TBD' if nothing found.
    """
    if not content or not isinstance(content, str):
        return "TBD"
    text = content.strip()
    # "I'm Name", "I am Name", "This is Name"
    for pat in [
        r"(?:I'm|I am)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[,.]",
        r"(?:This is|Hi,)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[,.]",
        r"([A-Z][a-z]+\s+[A-Z][a-z]+),\s*(?:founder|ceo|co-founder)",
    ]:
        m = re.search(pat, text)
        if m:
            name = m.group(1).strip()
            if len(name) >= 2 and len(name) <= 50:
                return name
    return "TBD"


def normalize_author(author: str, from_content: str) -> str:
    """
    Use provided author if non-empty; otherwise try extraction from content.
    """
    if author and str(author).strip():
        return str(author).strip()
    return extract_author_from_content(from_content or "")
