# ai_agent.py
import requests
from config import GEMINI_API_KEY
from google import genai
from google.genai import types


def analyze_deal_with_ai(
    title: str,
    price: str,
    size: str,
    status: str,
    description: str,
    image_url: str = None,
) -> tuple[bool, str]:
    if not GEMINI_API_KEY or GEMINI_API_KEY == "TWÓJ_GEMINI_API_KEY":
        return True, "⚠️ Brak skonfigurowanego klucza Gemini."

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        contents = []

        # Pobieranie pierwszego zdjęcia do analizy wizualnej
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
Jesteś ekspertem ds. resellingu odzieży ulicznej (streetwear) i selekcjonerem kurtek Napapijri (Rainforest / Kido / Anorak / Kangurka).

PRZEANALIZUJ DANE, OPIS ORAZ ZDJĘCIE OFERTY:
- Tytuł: {title}
- Cena: {price}
- Rozmiar: {size}
- Stan: {status}
- Opis ogłoszenia: {description}

RYGORYSTYCZNE KRYTERIA ODRZUCENIA (DECYZJA: NIE):
1. WADY I USZKODZENIA: Jeśli w opisie, tytule lub stanie pojawią się informacje o jakiejkolwiek wadzie (np. dziura, plama, uszkodzony zamek, przetarcie, plamy pod pachami, zniszczona podszewka, brak guzika), AUTOMATYCZNIE ODRZUĆ OFERTĘ!
2. TYP KURTKI: Szukamy kurtek kangurek/anorak (wkładanych przez głowę, preferowane ocieplane/puchowe/z futerkiem). Odrzuć zwykłe bluzy lub cienkie wiatrówki bez potencjału.
3. CENA: Sztywny limit ceny na Vinted to 250 zł (zakładając ~20 zł na wysyłkę/ochronę). Idealna cena <= 180-200 zł.

WYMAGANY FORMAT ODPOWIEDZI:
Na samej górze umieść dokładnie jedną z deklaracji:
DECYZJA: TAK (jeśli przedmiot jest w pełni sprawny, bez wad, okazyjny i zgodny z typem)
DECYZJA: NIE (jeśli ma jakąkolwiek wadę w opisie, jest za drogi lub niezgodny)

Pod spodem dodaj 2-3 krótkie zdania opinii (weryfikacja braku wad, oszacowany zysk, ocena 1-10 i emoji).
"""
        contents.append(prompt)

        # Wywołanie z aktualnym personelem modelu
        response = client.models.generate_content(
            model="gemini-3.8-flash",
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
        print(f"❌ Błąd Gemini API: {e}")
        return True, "🤖 AI: Nie udało się przeprowadzić pełnej analizy."