"""
Signal Radar - Dashboard / export
Exports top companies to hot_companies.csv using Pandas.
Only prelaunch_high and prelaunch_medium rows; SPI and priority are per project/author.
"""

from pathlib import Path
from typing import List, Optional

import pandas as pd

import config


def export_hot_companies(
    company_rows: List[dict],
    path: Optional[Path] = None,
    columns: Optional[List[str]] = None,
    sort_by: str = "SPI",
    ascending: bool = False,
) -> Path:
    """
    Export company/scored rows to CSV with Pandas.
    Columns: company, author, signal_type, weight, SPI, priority, content.
    Sorted by SPI (highest first) by default. Ready for outreach.
    """
    path = path or config.HOT_COMPANIES_CSV
    columns = columns or config.EXPORT_COLUMNS

    df = pd.DataFrame(company_rows)
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    df = df[columns]
    df = df.sort_values(by=sort_by, ascending=ascending)

    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")
    return path


def load_hot_companies(path: Optional[Path] = None) -> pd.DataFrame:
    """Load hot_companies.csv as DataFrame."""
    path = path or config.HOT_COMPANIES_CSV
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, encoding="utf-8")
