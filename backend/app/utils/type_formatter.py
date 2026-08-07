"""Shared value/date formatting helpers for DB rows headed to templates or API responses."""

from __future__ import annotations

from datetime import datetime

NULL_VALUES = {"nan", "none", "", "0", "0.0", "0001-01-01 00:00:00"}


def format_value(val) -> str:
    if val is None:
        return ""
    s = str(val).strip()
    return "" if s.lower() in NULL_VALUES else s


def format_date(val) -> str:
    if val is None:
        return ""
    s = str(val).strip()
    if s.lower() in NULL_VALUES:
        return ""
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return s
