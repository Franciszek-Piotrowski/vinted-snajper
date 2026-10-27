import unittest
from unittest.mock import Mock

from scraper import _detail_attribute


class DetailAttributeTests(unittest.TestCase):
    def test_reads_value_from_label_and_value_lines(self):
        row = Mock()
        row.inner_text.return_value = "Rozmiar\nM"
        page = Mock()
        page.locator.return_value.all.return_value = [row]

        self.assertEqual(_detail_attribute(page, ("Rozmiar", "Size")), "M")

    def test_reads_condition_from_inline_label(self):
        row = Mock()
        row.inner_text.return_value = "Stan: Nowy bez metki"
        page = Mock()
        page.locator.return_value.all.return_value = [row]

        self.assertEqual(
            _detail_attribute(page, ("Stan", "Condition")),
            "Nowy bez metki",
        )

    def test_returns_empty_when_label_is_missing(self):
        row = Mock()
        row.inner_text.return_value = "Dodane 3 min."
        page = Mock()
        page.locator.return_value.all.return_value = [row]

        self.assertEqual(_detail_attribute(page, ("Rozmiar", "Size")), "")


if __name__ == "__main__":
    unittest.main()
