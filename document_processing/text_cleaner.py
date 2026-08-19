"""
SakshamAI — Document Processing: text cleaning.

Normalizes raw extracted text (from either native PDF extraction or OCR)
into something usable as LLM context.
"""

from __future__ import annotations

import re


def clean_text(raw: str) -> str:
    """
    - collapse repeated whitespace/newlines
    - strip page-artifact lines (lone page numbers, repeated headers)
    - fix common OCR ligature/spacing issues
    - trim each line
    """
    if not raw:
        return ""

    text = raw.replace("\r\n", "\n").replace("\r", "\n")

    # Common OCR artifacts
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl")
    text = re.sub(r"-\n(?=[a-z])", "", text)  # de-hyphenate words split across lines

    lines = [line.strip() for line in text.split("\n")]

    cleaned_lines = []
    for line in lines:
        if not line:
            cleaned_lines.append("")  # keep paragraph breaks
            continue
        # Drop lone page-number lines like "12" or "Page 12" or "- 12 -"
        if re.fullmatch(r"(page\s*)?[-–]?\s*\d{1,4}\s*[-–]?", line, flags=re.IGNORECASE):
            continue
        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)

    # Collapse 3+ blank lines into 2 (keep paragraph structure, drop excess)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse repeated spaces
    text = re.sub(r"[ \t]{2,}", " ", text)

    return text.strip()