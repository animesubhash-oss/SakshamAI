import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from text_cleaner import clean_text


class CleanTextTests(unittest.TestCase):
    def test_preserves_paragraphs_and_headings(self):
        raw_text = "  Artificial   Intelligence  \n\n\nPage 12\n\nis a field of\ncomputer science.  "

        self.assertEqual(
            clean_text(raw_text),
            "Artificial Intelligence\n\nis a field of\ncomputer science.",
        )

    def test_normalizes_ligatures_and_line_end_hyphens(self):
        self.assertEqual(clean_text("ﬁeld of\nﬂight and learn-\ning"), "field of\nflight and learning")


if __name__ == "__main__":
    unittest.main()
