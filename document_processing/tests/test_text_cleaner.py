import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from text_cleaner import clean_text


class CleanTextTests(unittest.TestCase):

    def test_empty_input_returns_empty_string(self):
        self.assertEqual(clean_text(""), "")
        self.assertEqual(clean_text(None), "")

    def test_strips_lone_page_number_lines(self):
        raw = "Introduction to Photosynthesis\n\n12\n\nSome content here."
        result = clean_text(raw)
        self.assertNotIn("12", result.split("\n"))
        self.assertIn("Introduction to Photosynthesis", result)
        self.assertIn("Some content here.", result)

    def test_strips_page_prefixed_number_lines(self):
        raw = "Some content.\nPage 5\nMore content."
        result = clean_text(raw)
        self.assertNotIn("Page 5", result)

    def test_collapses_excess_blank_lines(self):
        raw = "Para one.\n\n\n\n\nPara two."
        result = clean_text(raw)
        self.assertNotIn("\n\n\n", result)

    def test_collapses_repeated_spaces(self):
        raw = "Word1     Word2"
        result = clean_text(raw)
        self.assertEqual(result, "Word1 Word2")

    def test_fixes_ligatures(self):
        raw = "The ﬁrst deﬁnition of ﬂow."
        result = clean_text(raw)
        self.assertIn("first", result)
        self.assertIn("definition", result)
        self.assertIn("flow", result)

    def test_dehyphenates_line_broken_words(self):
        raw = "This is a photosyn-\nthesis example."
        result = clean_text(raw)
        self.assertIn("photosynthesis", result)

    def test_preserves_paragraph_breaks(self):
        raw = "Paragraph one.\n\nParagraph two."
        result = clean_text(raw)
        self.assertIn("Paragraph one.\n\nParagraph two.", result)

    def test_trims_leading_and_trailing_whitespace(self):
        raw = "   \n  Some content.  \n   "
        result = clean_text(raw)
        self.assertEqual(result, "Some content.")


if __name__ == "__main__":
    unittest.main()