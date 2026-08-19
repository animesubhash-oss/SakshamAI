import unittest
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from document_models import PageResult
from document_processor import process_document


class ProcessDocumentTests(unittest.TestCase):
    def test_rejects_unsupported_files_without_processing(self):
        result = process_document(b"data", "lesson.docx")

        self.assertFalse(result.success)
        self.assertEqual(result.file_type, "unknown")
        self.assertIn("Supported", result.error)

    @patch("document_processor.extract_pdf")
    def test_routes_pdf_and_returns_structured_content(self, extract_pdf):
        extract_pdf.return_value = type("StubResult", (), {})()
        extract_pdf.return_value.success = True
        extract_pdf.return_value.filename = "lesson.pdf"
        extract_pdf.return_value.file_type = "pdf"
        extract_pdf.return_value.pages = [PageResult(1, "A lesson", "native")]
        extract_pdf.return_value.full_text = "A lesson"
        extract_pdf.return_value.warnings = []
        extract_pdf.return_value.error = None
        extract_pdf.return_value.processing_time_seconds = 0
        extract_pdf.return_value.to_dict = lambda: {"content": [{"page": 1, "text": "A lesson"}]}

        result = process_document(b"data", "lesson.pdf")

        extract_pdf.assert_called_once_with(b"data", "lesson.pdf", "eng")
        self.assertEqual(result.to_dict()["content"], [{"page": 1, "text": "A lesson"}])


if __name__ == "__main__":
    unittest.main()
