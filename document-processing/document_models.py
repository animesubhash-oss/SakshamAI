"""Data models shared by document processors and their consumers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PageResult:
    """Clean text and extraction metadata for one page."""

    page_number: int
    text: str
    method: str  # native, ocr, or empty
    char_count: int = field(init=False)

    def __post_init__(self) -> None:
        self.char_count = len(self.text)

    def to_content_dict(self) -> dict[str, object]:
        return {"page": self.page_number, "text": self.text}


@dataclass
class ProcessingResult:
    """Stable result format returned by every supported processor."""

    success: bool
    filename: str
    file_type: str
    full_text: str = ""
    pages: list[PageResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    error: Optional[str] = None
    processing_time_seconds: float = 0.0

    def to_dict(self) -> dict[str, object]:
        return {
            "success": self.success,
            "filename": self.filename,
            "file_type": self.file_type,
            "page_count": len(self.pages),
            "content": [page.to_content_dict() for page in self.pages],
            "full_text": self.full_text,
            "char_count": len(self.full_text),
            "pages": [
                {
                    "page_number": page.page_number,
                    "method": page.method,
                    "char_count": page.char_count,
                }
                for page in self.pages
            ],
            "warnings": self.warnings,
            "error": self.error,
            "processing_time_seconds": round(self.processing_time_seconds, 2),
        }
