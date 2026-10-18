# ai_agent.py
import time
from io import BytesIO
from config import GEMINI_API_KEY
from google import genai
from google.genai import types
from PIL import Image
import requests

client = genai.Client(api_key=GEMINI_API_KEY)


def download_image(url: str) -> Image.Image | None:
    if not url:
        return None
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
    except Exception as e:
        print(f"⚠️ Nie udało się pobrać zdjęcia do analizy AI: {e}")
    return None


def analyze_deal_with_ai(
    title: str, price: str, size: str, status: str, description: str, image_url: str
) -> tuple[bool, str]:

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

    contents = [prompt]

    pil_image = download_image(image_url)
    if pil_image:
        contents.append(pil_image)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=contents,
            )
            ai_response_text = response.text.strip()

            should_send = "DECYZJA: TAK" in ai_response_text
            return should_send, ai_response_text

        except Exception as e:
            error_str = str(e)
            print(f"⚠️ Błąd zapytania do Gemini (próba {attempt + 1}/{max_retries}): {error_str}")
            if "503" in error_str or "overloaded" in error_str.lower():
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                    continue
            return (
                False,
                f"⚠️ Błąd komunikacji z AI (Gemini niedostępne): {error_str}",
            )

    return False, "⚠️ Błąd: Przekroczono limit prób połączenia z AI."