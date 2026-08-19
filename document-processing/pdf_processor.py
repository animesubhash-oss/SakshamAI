"""PDF-only extraction, including OCR fallback for scanned pages."""

from __future__ import annotations

import io

import pdfplumber
import pymupdf as fitz
import pytesseract
from PIL import Image

from document_models import PageResult, ProcessingResult
from text_cleaner import clean_text

MIN_CHARS_FOR_NATIVE_TEXT = 20
OCR_RENDER_ZOOM = 2.0


def _ocr_image(image: Image.Image, lang: str) -> str:
    return pytesseract.image_to_string(image, lang=lang)


def extract_pdf(file_bytes: bytes, filename: str, ocr_lang: str = "eng") -> ProcessingResult:
    result = ProcessingResult(success=False, filename=filename, file_type="pdf")

    try:
        rendered_pdf = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as error:
        result.error = f"Could not open PDF (possibly corrupted or encrypted): {error}"
        return result

    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf_document:
            for index, page in enumerate(pdf_document.pages):
                page_number = index + 1
                native_text = ""
                try:
                    native_text = page.extract_text() or ""
                except Exception as error:
                    result.warnings.append(
                        f"Page {page_number}: native extraction failed ({error}); trying OCR."
                    )

                if len(native_text.strip()) >= MIN_CHARS_FOR_NATIVE_TEXT:
                    result.pages.append(PageResult(page_number, clean_text(native_text), "native"))
                    continue

                try:
                    rendered_page = rendered_pdf.load_page(index)
                    pixmap = rendered_page.get_pixmap(
                        matrix=fitz.Matrix(OCR_RENDER_ZOOM, OCR_RENDER_ZOOM)
                    )
                    image = Image.open(io.BytesIO(pixmap.tobytes("png")))
                    ocr_text = _ocr_image(image, ocr_lang)
                    method = "ocr" if ocr_text.strip() else "empty"
                    result.pages.append(PageResult(page_number, clean_text(ocr_text), method))
                    if method == "empty":
                        result.warnings.append(f"Page {page_number}: no text found (native or OCR).")
                except Exception as error:
                    result.pages.append(PageResult(page_number, "", "empty"))
                    result.warnings.append(f"Page {page_number}: OCR failed ({error}).")
    except Exception as error:
        result.error = f"Failed while reading PDF pages: {error}"
        return result
    finally:
        rendered_pdf.close()

    result.full_text = clean_text(
        "\n\n".join(
            f"[Page {page.page_number}]\n{page.text}"
            for page in result.pages
            if page.text.strip()
        )
    )
    result.success = bool(result.full_text)
    if not result.success:
        result.error = "No extractable text found in this PDF."
    return result
