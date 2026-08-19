"""
SakshamAI — Document Processing: shared data models.

Kept separate from the extraction logic so pdf_processor.py, image_processor.py,
and document_processor.py can all import the same result shapes without any
circular imports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PageResult:
    page_number: int
    text: str
    method: str  # "native" | "ocr" | "empty"
    char_count: int = 0

    def __post_init__(self):
        self.char_count = len(self.text)


@dataclass
class ProcessingResult:
    success: bool
    filename: str
    file_type: str  # "pdf" | "image" | "unknown"
    full_text: str = ""
    pages: list[PageResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    error: Optional[str] = None
    processing_time_seconds: float = 0.0

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "filename": self.filename,
            "file_type": self.file_type,
            "full_text": self.full_text,
            "char_count": len(self.full_text),
            "page_count": len(self.pages),
            "pages": [
                {"page_number": p.page_number, "method": p.method, "char_count": p.char_count}
                for p in self.pages
            ],
            "warnings": self.warnings,
            "error": self.error,
            "processing_time_seconds": round(self.processing_time_seconds, 2),
        }