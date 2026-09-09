"""Turn an uploaded file (or pasted text) into a :class:`StudyDocument`.

Extraction itself is done by the untouched ``document_processing`` package;
``.txt`` files go through the chatbot's own loader.  This module only maps the
backend result onto the interface's state model and phrases failures kindly.
"""

from __future__ import annotations

import logging
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from ..state.session_state import StudyDocument
from .bootstrap import BackendError, prepare_backend

logger = logging.getLogger("sakshamai.ui.documents")

PDF_TYPES = {".pdf"}
IMAGE_TYPES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}
TEXT_TYPES = {".txt"}
ACCEPTED = sorted(PDF_TYPES | IMAGE_TYPES | TEXT_TYPES)
ACCEPT_ATTRIBUTE = ",".join(ACCEPTED)
MAX_BYTES = 20 * 1024 * 1024
LIBRARY_PATH = Path(__file__).resolve().parents[2] / ".sakshamai" / "document_library.json"


def _friendly(filename: str, detail: str) -> BackendError:
    lower = detail.lower()
    if "tesseract" in lower:
        message = (
            f"'{filename}' needs to be scanned with OCR, but the OCR engine "
            "(Tesseract) is not available on this computer."
        )
    elif "unsupported file type" in lower:
        message = f"SakshamAI cannot read '{filename}'. Try a PDF, an image, or a .txt file."
    elif "no readable text" in lower or "empty" in lower:
        message = f"No readable text was found in '{filename}'."
    else:
        message = f"SakshamAI could not prepare '{filename}'."
    return BackendError(message, detail)


def _extract_text_file(file_bytes: bytes, filename: str) -> str:
    """Reuse the chatbot's own .txt loader rather than re-implementing it."""
    prepare_backend()
    from chatbot import load_document_from_file

    handle, temp_path = tempfile.mkstemp(suffix=".txt", prefix="sakshamai_upload_")
    os.close(handle)
    try:
        Path(temp_path).write_bytes(file_bytes)
        text, _ = load_document_from_file(temp_path)
        return text
    finally:
        Path(temp_path).unlink(missing_ok=True)


def extract_document(file_bytes: bytes, filename: str) -> StudyDocument:
    """Run the existing extraction pipeline and describe the result."""
    prepare_backend()

    if not file_bytes:
        raise BackendError(f"'{filename}' is empty.", "empty upload")
    if len(file_bytes) > MAX_BYTES:
        size = len(file_bytes) / (1024 * 1024)
        raise BackendError(
            f"'{filename}' is {size:.1f} MB. Please use a file under 20 MB.",
            "file too large",
        )

    suffix = Path(filename).suffix.lower()
    if suffix not in PDF_TYPES | IMAGE_TYPES | TEXT_TYPES:
        raise BackendError(
            f"SakshamAI cannot read '{filename}'. Supported files: "
            + ", ".join(ACCEPTED),
            f"unsupported extension {suffix}",
        )

    if suffix in TEXT_TYPES:
        try:
            text = _extract_text_file(file_bytes, filename)
        except Exception as error:
            logger.exception("Text upload failed")
            raise _friendly(filename, str(error)) from error
        return StudyDocument(name=filename, text=text.strip(), file_type="text")

    from document_processing.document_processor import process_document

    try:
        result = process_document(file_bytes, filename)
    except Exception as error:  # pragma: no cover - depends on local OCR stack
        logger.exception("Document processing crashed")
        raise _friendly(filename, str(error)) from error

    if not result.success or not result.full_text.strip():
        detail = result.error or "no readable text"
        logger.error("Document processing failed for %s: %s", filename, detail)
        raise _friendly(filename, detail)

    return StudyDocument(
        name=result.filename,
        text=result.full_text.strip(),
        file_type=result.file_type,
        page_count=len(result.pages),
        native_pages=sum(1 for page in result.pages if page.method == "native"),
        ocr_pages=sum(1 for page in result.pages if page.method == "ocr"),
        warnings=list(result.warnings),
        seconds=result.processing_time_seconds,
    )


def document_from_text(text: str, name: str = "Pasted text") -> StudyDocument:
    """Accept text the student pasted straight into the composer."""
    cleaned = (text or "").strip()
    if len(cleaned) < 40:
        raise BackendError(
            "Please paste a little more text - at least a few sentences to study.",
            "pasted text too short",
        )
    return StudyDocument(name=name, text=cleaned, file_type="text", source="pasted")


def _document_to_record(document: StudyDocument) -> dict[str, object]:
    return {
        "name": document.name,
        "text": document.text,
        "file_type": document.file_type,
        "page_count": document.page_count,
        "native_pages": document.native_pages,
        "ocr_pages": document.ocr_pages,
        "warnings": document.warnings,
        "source": document.source,
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }


def _record_to_document(record: dict[str, object]) -> StudyDocument:
    return StudyDocument(
        name=str(record.get("name", "Saved document")),
        text=str(record.get("text", "")),
        file_type=str(record.get("file_type", "text")),
        page_count=int(record.get("page_count", 0)),
        native_pages=int(record.get("native_pages", 0)),
        ocr_pages=int(record.get("ocr_pages", 0)),
        warnings=[str(item) for item in record.get("warnings", [])],
        source=str(record.get("source", "library")),
    )


def load_document_library() -> list[StudyDocument]:
    """Load locally saved documents without contacting any external service."""
    if not LIBRARY_PATH.exists():
        return []
    try:
        records = json.loads(LIBRARY_PATH.read_text(encoding="utf-8"))
        return [_record_to_document(record) for record in records if record.get("text")]
    except (OSError, ValueError, TypeError) as error:
        logger.warning("Could not load the document library: %s", error)
        return []


def save_document_to_library(document: StudyDocument) -> None:
    """Save or replace a document in the local document library."""
    documents = load_document_library()
    documents = [item for item in documents if item.name != document.name]
    documents.append(document)
    LIBRARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    records = [_document_to_record(item) for item in documents]
    LIBRARY_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def process_uploaded_document(file_bytes: bytes, filename: str) -> StudyDocument:
    """Backward-compatible wrapper used by the legacy NiceGUI entrypoint."""
    return extract_document(file_bytes, filename)
