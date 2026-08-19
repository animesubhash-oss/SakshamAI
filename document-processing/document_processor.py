"""Public entry point for the document-processing pipeline."""

from __future__ import annotations

import time
from pathlib import Path

from document_models import ProcessingResult
from image_processor import extract_image
from pdf_processor import extract_pdf

SUPPORTED_PDF_EXTENSIONS = {".pdf"}
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}


def process_document(file_bytes: bytes, filename: str, ocr_lang: str = "eng") -> ProcessingResult:
    """Extract and clean a supported educational document."""
    start = time.perf_counter()
    extension = Path(filename).suffix.lower()

    if extension in SUPPORTED_PDF_EXTENSIONS:
        result = extract_pdf(file_bytes, filename, ocr_lang)
    elif extension in SUPPORTED_IMAGE_EXTENSIONS:
        result = extract_image(file_bytes, filename, ocr_lang)
    else:
        result = ProcessingResult(
            success=False,
            filename=filename,
            file_type="unknown",
            error=(
                f"Unsupported file type '{extension}'. Supported: "
                "PDF, PNG, JPG, JPEG, WEBP, BMP, TIFF."
            ),
        )

    result.processing_time_seconds = time.perf_counter() - start
    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python document_processor.py <path_to_pdf_or_image>")
        raise SystemExit(1)

    document_path = Path(sys.argv[1])
    result = process_document(document_path.read_bytes(), document_path.name)
    print(result.to_dict())
