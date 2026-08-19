"""
SakshamAI — Document Processing: PDF extraction.

Tries native text extraction first (fast, accurate for typed/digital PDFs).
Falls back to OCR per-page for scanned/image-only pages.
"""

from __future__ import annotations

import io

import pdfplumber
import pymupdf as fitz  # PyMuPDF — used only for rendering scanned pages to images
from PIL import Image

from document_models import PageResult, ProcessingResult
from text_cleaner import clean_text

# If native extraction yields fewer than this many characters on a page,
# we assume it's a scanned/image-only page and OCR it instead.
MIN_CHARS_FOR_NATIVE_TEXT = 20

# Render scale for OCR fallback (higher = more accurate, slower).
OCR_RENDER_ZOOM = 2.0


def _ocr_image(image: Image.Image, lang: str) -> str:
    import pytesseract

    return pytesseract.image_to_string(image, lang=lang)


def extract_pdf(file_bytes: bytes, filename: str, ocr_lang: str = "eng") -> ProcessingResult:
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