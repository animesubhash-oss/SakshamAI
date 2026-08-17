"""
SakshamAI — Document Processing Module
Owner: Member 4 (Document Processing, UI & Documentation)

Purpose
-------
Takes a raw PDF or image (educational material) and turns it into clean,
usable text that Member 2 (Gemini core) and Member 3 (chatbot) can consume
as document context.

Pipeline
--------
1. Detect file type (PDF vs image).
2. PDF:
   a. Try native text extraction (pdfplumber) — fast, accurate, works for
      digitally-created PDFs (typed notes, textbooks exported as PDF, etc.)
   b. If a page yields little/no text, treat it as a scanned page and fall
      back to OCR (render page -> image -> tesseract).
3. Image (jpg/png/etc.): OCR directly.
4. Clean text: strip repeated whitespace, fix common OCR artifacts, drop
   near-empty lines, normalize line breaks.
5. Return a structured result so upstream modules always get a predictable
   shape, even on partial failure.

This module has ZERO dependency on Gemini, Flask, or any UI — it's a pure
processing layer. api.py wraps it as an HTTP service for the rest of the team.
"""

from __future__ import annotations

import io
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pymupdf as fitz  # PyMuPDF — used only for rendering scanned pages to images
import pdfplumber
import pytesseract
from PIL import Image

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SUPPORTED_PDF_EXTENSIONS = {".pdf"}
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}

# If native extraction yields fewer than this many characters on a page,
# we assume it's a scanned/image-only page and OCR it instead.
MIN_CHARS_FOR_NATIVE_TEXT = 20

# Render scale for OCR fallback (higher = more accurate, slower).
OCR_RENDER_ZOOM = 2.0


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

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
    file_type: str  # "pdf" | "image"
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


# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------

def clean_text(raw: str) -> str:
    """
    Normalize extracted text so it's usable as LLM context:
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
    text = re.sub(r"-\n(?=[A-Z a-z])", "", text)  # de-hyphenate words split across lines

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


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def _ocr_image(image: Image.Image, lang: str = "eng") -> str:
    """Run tesseract OCR on a PIL image."""
    return pytesseract.image_to_string(image, lang=lang)


def _extract_pdf(file_bytes: bytes, filename: str, ocr_lang: str = "eng") -> ProcessingResult:
    result = ProcessingResult(success=False, filename=filename, file_type="pdf")

    try:
        doc_fitz = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        result.error = f"Could not open PDF (possibly corrupted or encrypted): {e}"
        return result

    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf_plumber_doc:
            num_pages = len(pdf_plumber_doc.pages)

            for i in range(num_pages):
                page_num = i + 1
                native_text = ""
                try:
                    native_text = pdf_plumber_doc.pages[i].extract_text() or ""
                except Exception as e:
                    result.warnings.append(f"Page {page_num}: native extraction failed ({e}); trying OCR.")

                if len(native_text.strip()) >= MIN_CHARS_FOR_NATIVE_TEXT:
                    result.pages.append(PageResult(page_num, native_text, "native"))
                    continue

                # Fall back to OCR — render this page as an image via PyMuPDF
                try:
                    fitz_page = doc_fitz.load_page(i)
                    pix = fitz_page.get_pixmap(matrix=fitz.Matrix(OCR_RENDER_ZOOM, OCR_RENDER_ZOOM))
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    ocr_text = _ocr_image(img, lang=ocr_lang)
                    if ocr_text.strip():
                        result.pages.append(PageResult(page_num, ocr_text, "ocr"))
                    else:
                        result.pages.append(PageResult(page_num, "", "empty"))
                        result.warnings.append(f"Page {page_num}: no text found (native or OCR).")
                except Exception as e:
                    result.pages.append(PageResult(page_num, "", "empty"))
                    result.warnings.append(f"Page {page_num}: OCR failed ({e}).")

    except Exception as e:
        result.error = f"Failed while reading PDF pages: {e}"
        return result
    finally:
        doc_fitz.close()

    combined = "\n\n".join(
        f"[Page {p.page_number}]\n{p.text}" for p in result.pages if p.text.strip()
    )
    result.full_text = clean_text(combined)
    result.success = len(result.full_text) > 0
    if not result.success:
        result.error = "No extractable text found in this PDF."

    return result


def _extract_image(file_bytes: bytes, filename: str, ocr_lang: str = "eng") -> ProcessingResult:
    result = ProcessingResult(success=False, filename=filename, file_type="image")

    try:
        img = Image.open(io.BytesIO(file_bytes))
        img = img.convert("RGB")
    except Exception as e:
        result.error = f"Could not open image (unsupported or corrupted file): {e}"
        return result

    try:
        raw_text = _ocr_image(img, lang=ocr_lang)
    except Exception as e:
        result.error = f"OCR failed: {e}"
        return result

    result.pages.append(PageResult(1, raw_text, "ocr"))
    result.full_text = clean_text(raw_text)
    result.success = len(result.full_text) > 0
    if not result.success:
        result.error = "No text could be read from this image. Try a clearer photo or scan."

    return result


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def process_document(file_bytes: bytes, filename: str, ocr_lang: str = "eng") -> ProcessingResult:
    """
    Main entry point. Give it raw file bytes + a filename, get back a
    ProcessingResult with clean text ready for the Gemini core.

    ocr_lang: tesseract language code(s), e.g. "eng", "eng+hin", "eng+mar"
              (useful later if study material includes Hindi/Marathi text).
    """
    start = time.time()
    ext = Path(filename).suffix.lower()

    if ext in SUPPORTED_PDF_EXTENSIONS:
        result = _extract_pdf(file_bytes, filename, ocr_lang)
    elif ext in SUPPORTED_IMAGE_EXTENSIONS:
        result = _extract_image(file_bytes, filename, ocr_lang)
    else:
        result = ProcessingResult(
            success=False,
            filename=filename,
            file_type="unknown",
            error=f"Unsupported file type '{ext}'. Supported: PDF, PNG, JPG, JPEG, WEBP, BMP, TIFF.",
        )

    result.processing_time_seconds = time.time() - start
    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python document_processor.py <path_to_pdf_or_image>")
        sys.exit(1)

    path = Path(sys.argv[1])
    data = path.read_bytes()
    res = process_document(data, path.name)

    print(f"success: {res.success}")
    print(f"file_type: {res.file_type}")
    print(f"pages: {len(res.pages)}")
    print(f"char_count: {len(res.full_text)}")
    if res.warnings:
        print(f"warnings: {res.warnings}")
    if res.error:
        print(f"error: {res.error}")
    print("\n--- extracted text (first 1000 chars) ---")
    print(res.full_text[:1000])
