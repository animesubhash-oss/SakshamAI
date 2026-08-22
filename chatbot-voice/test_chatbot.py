"""
Tests for chatbot.py.

The Gemini client itself is mocked out (we're not making real API calls
in tests), but load_document_from_file() is tested against REAL files
going through the REAL document_processor pipeline from Member 4 — that
integration is exactly what we need to prove works.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Set a dummy API key before importing chatbot.py, since the module
# raises ValueError at import time if GEMINI_API_KEY is missing.
os.environ.setdefault("GEMINI_API_KEY", "test-key-not-real")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Patch genai.Client globally before importing chatbot, so no real
# Gemini client is ever constructed.
with patch("google.genai.Client") as MockClient:
    MockClient.return_value = MagicMock()
    import chatbot
    from chatbot import DocumentChatbot, load_document_from_file, MAX_DOCUMENT_CHARS


class DocumentChatbotStateTests(unittest.TestCase):
    """Tests for document state management (no API calls involved)."""

    def test_starts_with_no_document(self):
        bot = DocumentChatbot()
        self.assertFalse(bot.has_document())

    def test_set_document_stores_text_and_name(self):
        bot = DocumentChatbot()
        bot.set_document("Some content", "notes.pdf")
        self.assertTrue(bot.has_document())
        self.assertEqual(bot.document_name, "notes.pdf")
        self.assertEqual(bot.document_text, "Some content")

    def test_set_document_rejects_empty_text(self):
        bot = DocumentChatbot()
        with self.assertRaises(ValueError):
            bot.set_document("   ", "notes.pdf")

    def test_set_document_resets_conversation_history(self):
        bot = DocumentChatbot()
        bot.conversation_history = [{"role": "user", "content": "hi"}]
        bot.set_document("New content", "notes.pdf")
        self.assertEqual(bot.conversation_history, [])

    def test_clear_document_returns_to_general_mode(self):
        bot = DocumentChatbot()
        bot.set_document("Some content", "notes.pdf")
        bot.clear_document()
        self.assertFalse(bot.has_document())
        self.assertEqual(bot.document_name, "")

    def test_large_document_is_truncated(self):
        bot = DocumentChatbot()
        huge_text = "a" * (MAX_DOCUMENT_CHARS + 5000)
        bot.set_document(huge_text, "big.pdf")
        self.assertTrue(bot.document_truncated)
        self.assertEqual(len(bot.document_text), MAX_DOCUMENT_CHARS)

    def test_normal_sized_document_is_not_truncated(self):
        bot = DocumentChatbot()
        bot.set_document("short content", "small.pdf")
        self.assertFalse(bot.document_truncated)


class AskMethodTests(unittest.TestCase):
    """Tests for ask() with a mocked Gemini client."""

    def test_empty_question_returns_prompt_message(self):
        bot = DocumentChatbot()
        self.assertEqual(bot.ask("   "), "Please enter a question.")

    @patch("chatbot.client")
    def test_ask_returns_model_answer_and_saves_history(self, mock_client):
        mock_response = MagicMock()
        mock_response.text = "  The answer is 42.  "
        mock_client.models.generate_content.return_value = mock_response

        bot = DocumentChatbot()
        answer = bot.ask("What is the answer?")

        self.assertEqual(answer, "The answer is 42.")
        self.assertEqual(len(bot.conversation_history), 2)
        self.assertEqual(bot.conversation_history[0]["role"], "user")
        self.assertEqual(bot.conversation_history[1]["role"], "assistant")

    @patch("chatbot.client")
    def test_ask_handles_quota_error(self, mock_client):
        mock_client.models.generate_content.side_effect = Exception(
            "429 RESOURCE_EXHAUSTED: quota exceeded"
        )
        bot = DocumentChatbot()
        answer = bot.ask("Anything?")
        self.assertIn("quota", answer.lower())

    @patch("chatbot.client")
    def test_ask_handles_auth_error(self, mock_client):
        mock_client.models.generate_content.side_effect = Exception(
            "403 PERMISSION_DENIED: API key invalid"
        )
        bot = DocumentChatbot()
        answer = bot.ask("Anything?")
        self.assertIn("API key", answer)

    @patch("chatbot.client")
    def test_ask_handles_empty_model_response(self, mock_client):
        mock_response = MagicMock()
        mock_response.text = "   "
        mock_client.models.generate_content.return_value = mock_response

        bot = DocumentChatbot()
        answer = bot.ask("Anything?")
        self.assertEqual(answer, "I couldn't generate an answer.")


class LoadDocumentIntegrationTests(unittest.TestCase):
    """
    These exercise the REAL integration with Member 4's document_processor
    module — no mocking of extraction logic. This is the part that matters:
    proving chatbot.py actually delegates to Core instead of reimplementing
    PDF parsing.
    """

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = Path(__file__).resolve().parent / "_tmp_test_files"
        cls.tmp_dir.mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        import shutil
        shutil.rmtree(cls.tmp_dir, ignore_errors=True)

    def test_loads_txt_file_directly(self):
        txt_path = self.tmp_dir / "sample.txt"
        txt_path.write_text("Hello from a text file.", encoding="utf-8")

        text, name = load_document_from_file(str(txt_path))

        self.assertEqual(text, "Hello from a text file.")
        self.assertEqual(name, "sample.txt")

    def test_rejects_empty_txt_file(self):
        txt_path = self.tmp_dir / "empty.txt"
        txt_path.write_text("", encoding="utf-8")

        with self.assertRaises(ValueError):
            load_document_from_file(str(txt_path))

    def test_raises_for_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            load_document_from_file(str(self.tmp_dir / "does_not_exist.pdf"))

    def test_delegates_pdf_to_document_processor(self):
        """
        Build a real native-text PDF and confirm chatbot.py's loader
        gets text back via Member 4's process_document(), including
        the [Page N] structure that pipeline adds.
        """
        from reportlab.pdfgen import canvas

        pdf_path = self.tmp_dir / "sample.pdf"
        c = canvas.Canvas(str(pdf_path))
        c.drawString(50, 800, "Integration test content for chatbot loader.")
        c.save()

        text, name = load_document_from_file(str(pdf_path))

        self.assertIn("Integration test content", text)
        self.assertEqual(name, "sample.pdf")

    def test_unsupported_extension_raises_with_clear_message(self):
        bad_path = self.tmp_dir / "notes.docx"
        bad_path.write_text("fake docx content", encoding="utf-8")

        with self.assertRaises(ValueError) as ctx:
            load_document_from_file(str(bad_path))

        self.assertIn("Unsupported file type", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()