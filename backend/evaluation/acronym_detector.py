"""
Vietnamese medical acronym detector.

Checks whether a response contains Vietnamese medical abbreviations that
should be spelled out in patient-facing or formal clinical text.

False-positive-safe rules:
  - BN  : NOT followed by a digit (avoids patient IDs like BN0003)
  - SA  : followed by whitespace/punctuation/end (avoids Vietnamese words "sa lầy", etc.)
  - All others use strict \\b word boundaries.
"""

import re

# (abbreviation, pattern, full_term)
_RULES: list[tuple[str, re.Pattern, str]] = [
    ("BN",      re.compile(r"\bBN\b(?!\d)"),            "bệnh nhân"),
    ("HATT",    re.compile(r"\bHATT\b"),                 "huyết áp tâm thu"),
    ("HATTr",   re.compile(r"\bHATTr\b"),                "huyết áp tâm trương"),
    ("CLS",     re.compile(r"\bCLS\b"),                  "cận lâm sàng"),
    ("XN",      re.compile(r"\bXN\b"),                   "xét nghiệm"),
    ("THA",     re.compile(r"\bTHA\b"),                  "tăng huyết áp"),
    ("ĐTĐ",     re.compile(r"\bĐTĐ\b"),                  "đái tháo đường"),
    ("NMCT",    re.compile(r"\bNMCT\b"),                 "nhồi máu cơ tim"),
    ("TBMMN",   re.compile(r"\bTBMMN\b"),                "tai biến mạch máu não"),
    ("XQ",      re.compile(r"\bXQ\b"),                   "X-quang"),
    ("BPTNMT",  re.compile(r"\bBPTNMT\b"),               "bệnh phổi tắc nghẽn mạn tính"),
    ("SA",      re.compile(r"\bSA\b(?=[\s,.\n]|$)"),    "siêu âm"),
]


def check_acronyms(text: str) -> list[dict]:
    """
    Return a list of violations found in `text`.
    Each violation: {"acronym": str, "full_term": str, "count": int}
    """
    violations = []
    for abbrev, pattern, full_term in _RULES:
        matches = pattern.findall(text)
        if matches:
            violations.append({
                "acronym": abbrev,
                "full_term": full_term,
                "count": len(matches),
            })
    return violations


def acronym_score(text: str) -> float:
    """1.0 = no acronyms found; 0.0 = at least one found."""
    return 0.0 if check_acronyms(text) else 1.0
