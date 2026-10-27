import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import ai_agent


class AiAgentTests(unittest.TestCase):
    def test_returns_decision_from_exact_first_line(self):
        client = SimpleNamespace(
            models=SimpleNamespace(
                generate_content=Mock(
                    return_value=SimpleNamespace(text="DECYZJA: NIE\nOferta ma wadę.")
                )
            )
        )

        with (
            patch.object(ai_agent, "GEMINI_API_KEY", "test-key"),
            patch.object(ai_agent.genai, "Client", return_value=client),
        ):
            decision, opinion = ai_agent.analyze_deal_with_ai(
                "Kurtka", "100 PLN", "M", "Bardzo dobry", "Brak wad"
            )

        self.assertIs(decision, False)
        self.assertIn("Oferta ma wadę", opinion)

    def test_does_not_accept_decision_embedded_in_unstructured_response(self):
        client = SimpleNamespace(
            models=SimpleNamespace(
                generate_content=Mock(
                    return_value=SimpleNamespace(text="Opis oferty\nDECYZJA: TAK")
                )
            )
        )

        with (
            patch.object(ai_agent, "GEMINI_API_KEY", "test-key"),
            patch.object(ai_agent.genai, "Client", return_value=client),
        ):
            decision, _ = ai_agent.analyze_deal_with_ai(
                "Kurtka", "100 PLN", "M", "Brak danych", ""
            )

        self.assertIsNone(decision)

    def test_missing_api_key_is_an_error_not_a_rejection(self):
        with patch.object(ai_agent, "GEMINI_API_KEY", None):
            decision, _ = ai_agent.analyze_deal_with_ai(
                "Kurtka", "100 PLN", "M", "Brak danych", ""
            )

        self.assertIsNone(decision)


if __name__ == "__main__":
    unittest.main()
