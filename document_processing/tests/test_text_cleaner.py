import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from text_cleaner import clean_text


class CleanTextTests(unittest.TestCase):

    def test_preserves_paragraphs_and_headings(self):
        raw_text = (
            "  Artificial   Intelligence  \n\n\n"
            "Page 12\n\n"
            "is a field of\n"
            "computer science.  "
        )

        self.assertEqual(
            clean_text(raw_text),
            "Artificial Intelligence\n\n"
            "is a field of\n"
            "computer science.",
        )

    def test_normalizes_ligatures_and_line_end_hyphens(self):
        raw_text = "ﬁeld of\nﬂight and learn-\ning"

        self.assertEqual(
            clean_text(raw_text),
            "field of\nflight and learning",
        )

    def test_removes_page_markers(self):
        raw_text = (
            "Artificial Intelligence\n\n"
            "Page 12\n\n"
            "Machine Learning"
        )

        self.assertEqual(
            clean_text(raw_text),
            "Artificial Intelligence\n\n"
            "Machine Learning",
        )


if __name__ == "__main__":
    unittest.main()