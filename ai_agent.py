# ai_agent.py
import time
import requests
from config import GEMINI_API_KEY
from google import genai
from google.genai import types


def analyze_deal_with_ai(
    title: str,
    price: str,
    size: str,
    status: str,
    description: str = "Brak opisu",
    image_url: str = None,
) -> tuple[bool, str]:
    if not GEMINI_API_KEY or GEMINI_API_KEY == "TWÓJ_GEMINI_API_KEY":
        return False, "⚠️ Brak skonfigurowanego klucza Gemini."

    client = genai.Client(api_key=GEMINI_API_KEY)
    contents = []

    # Pobieranie zdjęcia
    if image_url:
        try:
            img_response = requests.get(image_url, timeout=5)
            if img_response.status_code == 200:
                image_part = types.Part.from_bytes(
                    data=img_response.content,
                    mime_type="image/jpeg",
                )
                contents.append(image_part)
        except Exception as e:
            print(f"⚠️ Błąd pobierania zdjęcia do AI: {e}")

    prompt = f"""
Jesteś bezwzględnym i doświadczonym ekspertem-resellerem odzieży markowej (specjalizacja: Napapijri Rainforest Winter / Skidoo). Twoim zadaniem jest ocenić, czy ta oferta z Vinted to opłacalny zakup do dalszej odsprzedaży z zyskiem.

Oto dane oferty:
- Tytuł: {title}
- Cena: {price}
- Rozmiar: {size}
- Stan podany przez sprzedawcę: {status}
- Opis: {description}

HIERARCHIA I KRYTERIA RESELLINGOWE:

1. **TYP PRODUKTU I KROJ (Główny filtr zimowy)**:
   - **WYMAGANE**: ZIMOWA kurtka typu Anorak / Kangurka Napapijri (Rainforest Winter / Skidoo) – wkładana przez głowę z dużą kieszenią z przodu.
   - **ANALIZA PODSZEWKI/MODELU**:
     * Szukaj w opisie słów: "polar", "ocieplana", "zimowa", "fleece", "ciepła", "winter".
     * Jeśli na zdjęciu/w opisie widać ocieplenie polarowe -> ZDECYDOWANE TAK.
     * Jeśli kategoria lub opis sugeruje wiatrówkę, ALE opis/zdjęcie nie wyklucza jednoznacznie polaru, a krój to klasyczna kangurka w świetnej cenie -> ZAAKCEPTUJ (daj TAK) i zaznacz w opinii, by dopytać sprzedawcę o polar.
     * Jeśli opis WPROST mówi "cienka / wiatrówka / letnia / summer / bez polaru" -> DECYZJA: NIE.
   - **BEZWZGLĘDNY ZAKAZ (DECYZJA: NIE)**:
     * Kurtki rozpinane na całej długości (Zip-Through / Open) – słaby popyt.
     * Zwykłe bluzy polarowe (fleece bez kurtki), t-shirty, spodnie, czapki, torby.
     * Rozmiary dziecięce / Junior (np. 14/16 lat, 164-170 cm z metki dziecięcej), nawet jeśli wpisano S lub M.

2. **KOLORYSTYKA (Wpływ na ocenę)**:
   - **TOP (+2 pkt)**: Czarny, Granatowy, Niebieski, Zielony, Khaki, Oliwkowy.
   - **TRUDNE (-3 pkt)**: Jaskrawy żółty, pomarańczowy, jaskrawy róż, krzykliwe wzory/wielokolorowe.

3. **ROZMIAR (Popyt)**:
   - **NAJLEPSZE**: M oraz L (najszybsza rotacja).
   - **SŁABSZE**: XL, XXL, S (obniżają ocenę).

4. **STAN I WADY**:
   - **BEZWZGLĘDNY ZAKAZ (DECYZJA: NIE)**: Dziury, plamy, uszkodzone zamki, zniszczone rzepy, plamy na fladze/logo.
   - Brak odpinanego futerka przy kapturze obniża ocenę o 1-2 pkt, ale nie dyskwalifikuje oferty, jeśli cena jest niska.

5. **CENA I BUDŻET**:
   - Maksymalny budżet to ok. 250 - 260 PLN. Czym niższa cena przy idealnym stanie, topowym kolorze i rozmiarze M/L, tym wyższa ocena.

ZASADY ODPOWIEDZI:
W pierwszej linijce musisz napisać dokładnie:
DECYZJA: TAK
lub
DECYZJA: NIE

W kolejnych linijkach napisz zwięzłą, konkretną analizę po polsku (3-4 zdania):
1. Potwierdź typ i model (oraz czy potwierdzono polar/zimówkę).
2. Oceń kolor i rozmiar.
3. Podaj ocenę opłacalności zakupu w skali 1-10 i uzasadnij przewidywaną marżę.
"""
    contents.append(prompt)

    # Używamy modelu z list z pełnym limitem 1500 zapytań/dzień
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=contents,
            )

            analysis_text = response.text.strip()
            should_send = "DECYZJA: TAK" in analysis_text

            clean_opinion = (
                analysis_text.replace("DECYZJA: TAK", "")
                .replace("DECYZJA: NIE", "")
                .strip()
            )

            return should_send, clean_opinion

        except Exception as e:
            if "503" in str(e) and attempt < max_retries:
                print(f"⚠️ Przeciążenie Gemini (503). Próba {attempt}/{max_retries}. Czekam 3 sekundy...")
                time.sleep(3)
            else:
                print(f"❌ Błąd Gemini API: {e}")
                return False, "🤖 AI: Nie udało się przeprowadzić analizy z powodu błędu API."

    return False, "🤖 AI: Serwery Gemini niedostępne."