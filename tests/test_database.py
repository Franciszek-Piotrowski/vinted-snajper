import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database


class SeenItemsTests(unittest.TestCase):
    def test_saves_only_latest_150_ids_in_order(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "seen_items.json"
            items = [str(index) for index in range(200)]

            with patch.object(database, "DB_FILE", str(path)):
                database.save_seen_items(items)

            saved_items = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved_items, items[:150])

    def test_loads_legacy_list_without_truncating_until_save(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "seen_items.json"
            legacy_items = [str(index) for index in range(905)]
            path.write_text(json.dumps(legacy_items), encoding="utf-8")

            with patch.object(database, "DB_FILE", str(path)):
                self.assertEqual(database.load_seen_items(), legacy_items)

    def test_rejects_corrupted_history_instead_of_resetting_it(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "seen_items.json"
            path.write_text('{"not": "a list"}', encoding="utf-8")

            with patch.object(database, "DB_FILE", str(path)):
                with self.assertRaises(ValueError):
                    database.load_seen_items()


if __name__ == "__main__":
    unittest.main()
