import importlib
import sys
import types
import unittest
from unittest.mock import patch


def load_main_module():
    ai_agent = types.ModuleType("ai_agent")
    ai_agent.analyze_deal_with_ai = None
    notifier = types.ModuleType("notifier")
    notifier.send_telegram_notification = None
    scraper = types.ModuleType("scraper")
    scraper.TARGET_URL = "https://example.invalid"
    scraper.scrape_vinted_products = None

    with patch.dict(
        sys.modules,
        {"ai_agent": ai_agent, "notifier": notifier, "scraper": scraper},
    ):
        sys.modules.pop("main", None)
        module = importlib.import_module("main")
    return module


main_module = load_main_module()


def item(item_id):
    return {
        "id": item_id,
        "title": "Kurtka <Napapijri>",
        "price": "100 & 20 PLN",
        "size": "M",
        "status": "Bardzo dobry",
        "description": "Opis",
        "url": f"https://www.vinted.pl/items/{item_id}-kurtka",
        "image_url": "",
    }


class MainTests(unittest.TestCase):
    def configure(self, items, decision, notification_result=True):
        self.saved = []
        notifier_patch = patch.object(
            main_module,
            "send_telegram_notification",
            return_value=notification_result,
        )
        self.notify_mock = notifier_patch.start()
        self.addCleanup(notifier_patch.stop)
        patches = [
            patch.object(main_module, "load_seen_items", return_value=[]),
            patch.object(main_module, "scrape_vinted_products", return_value=items),
            patch.object(main_module, "analyze_deal_with_ai", side_effect=decision),
            patch.object(main_module, "save_seen_items", side_effect=self.saved.append),
            patch.object(main_module.time, "sleep"),
        ]
        for active_patch in patches:
            active_patch.start()
            self.addCleanup(active_patch.stop)

    def test_ai_error_does_not_mark_item_as_seen(self):
        self.configure([item("1")], [(None, "API error")])

        main_module.main()

        self.assertEqual(self.saved, [])

    def test_failed_telegram_send_does_not_mark_accepted_item_as_seen(self):
        self.configure([item("1")], [(True, "Analiza")], notification_result=False)

        main_module.main()

        self.assertEqual(self.saved, [])

    def test_rejected_offer_is_persisted_for_deduplication(self):
        self.configure([item("1")], [(False, "Odrzucono")])

        main_module.main()

        self.assertEqual(self.saved, [["1"]])

    def test_legacy_history_reorders_visible_ids_before_save(self):
        legacy_history = [str(index) for index in range(200)]
        active_item = item("199")
        self.saved = []
        patches = [
            patch.object(main_module, "load_seen_items", return_value=legacy_history),
            patch.object(
                main_module,
                "scrape_vinted_products",
                return_value=[active_item],
            ),
            patch.object(main_module, "save_seen_items", side_effect=self.saved.append),
        ]
        for active_patch in patches:
            active_patch.start()
            self.addCleanup(active_patch.stop)

        main_module.main()

        self.assertEqual(len(self.saved), 1)
        self.assertEqual(len(self.saved[0]), 200)
        self.assertEqual(self.saved[0][0], "199")

    def test_notification_cap_is_applied_and_html_is_escaped(self):
        self.configure(
            [item(str(index)) for index in range(6)],
            [(True, "Analiza <wady>") for _ in range(6)],
        )

        main_module.main()

        self.assertEqual(len(self.saved), 5)
        self.assertEqual(self.notify_mock.call_count, 5)
        self.assertIn("&lt;Napapijri&gt;", self.notify_mock.call_args.kwargs["caption"])
        self.assertIn("&lt;wady&gt;", self.notify_mock.call_args.kwargs["caption"])


if __name__ == "__main__":
    unittest.main()
