import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from document_models import PageResult
from document_processor import process_document


class ProcessDocumentTests(unittest.TestCase):

    def test_rejects_unsupported_files_without_processing(self):
        """Unsupported file types should be rejected."""
        result = process_document(b"data", "lesson.docx")

        self.assertFalse(result.success)
        self.assertEqual(result.file_type, "unknown")
        self.assertIn("Supported", result.error)

    @patch("document_processor.extract_pdf")
    def test_routes_pdf_and_returns_structured_content(self, extract_pdf):
        """PDF files should be routed to extract_pdf()."""

        mock_result = Mock()
        mock_result.success = True
        mock_result.filename = "lesson.pdf"
        mock_result.file_type = "pdf"
        mock_result.pages = [
            PageResult(1, "A lesson", "native")
        ]
        mock_result.full_text = "A lesson"
        mock_result.warnings = []
        mock_result.error = None
        mock_result.processing_time_seconds = 0
        mock_result.to_dict.return_value = {
            "success": True,
            "filename": "lesson.pdf",
            "file_type": "pdf",
            "full_text": "A lesson",
            "pages": [
                {"page_number": 1, "method": "native", "char_count": 8}
            ],
        }

        extract_pdf.return_value = mock_result

        result = process_document(b"data", "lesson.pdf")

        extract_pdf.assert_called_once_with(
            b"data",
            "lesson.pdf",
            "eng"
        )

        self.assertTrue(result.success)
        self.assertEqual(result.file_type, "pdf")
        self.assertEqual(
            result.to_dict()["pages"],
            [
                {"page_number": 1, "method": "native", "char_count": 8}
            ],
        )

    @patch("document_processor.extract_pdf")
    def test_handles_pdf_extraction_failure(self, extract_pdf):
        """PDF extraction failures should be returned correctly."""

        mock_result = Mock()
        mock_result.success = False
        mock_result.filename = "lesson.pdf"
        mock_result.file_type = "pdf"
        mock_result.pages = []
        mock_result.full_text = ""
        mock_result.warnings = []
        mock_result.error = "Failed to extract PDF content."
        mock_result.processing_time_seconds = 0

        extract_pdf.return_value = mock_result

        result = process_document(b"invalid pdf data", "lesson.pdf")

        extract_pdf.assert_called_once_with(
            b"invalid pdf data",
            "lesson.pdf",
            "eng"
        )

        self.assertFalse(result.success)
        self.assertEqual(result.file_type, "pdf")
        self.assertEqual(
            result.error,
            "Failed to extract PDF content."
        )

    @patch("document_processor.extract_image")
    def test_routes_image_to_extract_image(self, extract_image):
        """Image files should be routed to extract_image()."""

        mock_result = Mock()
        mock_result.success = True
        mock_result.filename = "photo.png"
        mock_result.file_type = "image"
        mock_result.pages = [PageResult(1, "Scanned text", "ocr")]
        mock_result.full_text = "Scanned text"
        mock_result.warnings = []
        mock_result.error = None
        mock_result.processing_time_seconds = 0

        extract_image.return_value = mock_result

        result = process_document(b"imgdata", "photo.png", ocr_lang="eng+hin")

        extract_image.assert_called_once_with(
            b"imgdata",
            "photo.png",
            "eng+hin"
        )

        self.assertTrue(result.success)
        self.assertEqual(result.file_type, "image")

    def test_records_processing_time(self):
        """process_document should always populate processing_time_seconds."""
        result = process_document(b"data", "lesson.docx")
        self.assertIsInstance(result.processing_time_seconds, float)
        self.assertGreaterEqual(result.processing_time_seconds, 0)


if __name__ == "__main__":
    unittest.main()