"""Conservative text normalization for extracted educational content."""

from __future__ import annotations

import re


def clean_text(raw_text: str) -> str:
    """Normalize extraction artifacts while preserving content and paragraphs."""
    if not raw_text:
        return ""

    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl")
    text = re.sub(r"-\n(?=[A-Za-z])", "", text)

    cleaned_lines: list[str] = []
    for line in text.split("\n"):
        line = line.strip()
        if re.fullmatch(r"(page\s*)?[-–]?\s*\d{1,4}\s*[-–]?", line, re.IGNORECASE):
            continue
        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()
