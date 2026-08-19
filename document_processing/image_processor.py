"""Image-only extraction kept separate from the PDF processor."""

from __future__ import annotations

import io

import pytesseract
from PIL import Image

from document_models import PageResult, ProcessingResult
from text_cleaner import clean_text


def extract_image(file_bytes: bytes, filename: str, ocr_lang: str = "eng") -> ProcessingResult:
    result = ProcessingResult(success=False, filename=filename, file_type="image")
    try:
        image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    except Exception as error:
        result.error = f"Could not open image (unsupported or corrupted file): {error}"
        return result

    try:
        raw_text = pytesseract.image_to_string(image, lang=ocr_lang)
    except Exception as error:
        result.error = f"OCR failed: {error}"
        return result

    result.pages.append(PageResult(1, clean_text(raw_text), "ocr"))
    result.full_text = result.pages[0].text
    result.success = bool(result.full_text)
    if not result.success:
        result.error = "No text could be read from this image. Try a clearer photo or scan."
    return result
