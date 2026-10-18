from config import GEMINI_API_KEY
from google import genai


def analyze_deal_with_ai(
    title: str, price: str, size: str, status: str
) -> str:
    """Agent Gemini ocenia potencjał resellingowy oferty."""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "TWÓJ_GEMINI_API_KEY":
        return "🤖 AI: Brak skonfigurowanego GEMINI_API_KEY w config.py."

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        prompt = f"""
Jesteś doświadczonym handlarzem i ekspertem ds. resellingu odzieży ulicznej (streetwear) oraz kurtek Napapijri.
Otrzymujesz nową ofertę z Vinted:
- Przedmiot: {title}
- Cena: {price}
- Rozmiar: {size}
- Stan podany przez sprzedawcę: {status}

Twoje zadanie:
1. Oceń opłacalność oferty pod dalszą odsprzedaż w skali 1-10.
2. Oszacuj realną cenę rynkową i potencjalny zysk netto (PLN).
3. Podaj krótki, dosadny werdykt (max 2-3 zdania). Użyj emoji.
"""

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
        )

        return response.text.strip()
    except Exception as e:
        print(f"❌ Błąd Gemini API: {e}")
        return "🤖 AI: Nie udało się pobrać opinii Gemini."