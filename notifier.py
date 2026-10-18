# notifier.py
import requests
from config import Bot_Token, Chat_ID


def send_telegram_notification(caption: str, photo_url: str = None) -> bool:
    """Wysyła post ze zdjęciem (sendPhoto) lub awaryjnie sam tekst (sendMessage)."""
    if photo_url:
        url = f"https://api.telegram.org/bot{Bot_Token}/sendPhoto"
        payload = {
            "chat_id": Chat_ID,
            "photo": photo_url,
            "caption": caption,
            "parse_mode": "HTML",
        }
        try:
            res = requests.post(url, json=payload)
            if res.status_code == 200:
                return True
            else:
                print(f"⚠️ Telegram odrzucił zdjęcie (status {res.status_code}). Wysyłam tekst.")
        except Exception as e:
            print(f"⚠️ Błąd wysyłania zdjęcia: {e}")

    # Awaryjne wysłanie samego tekstu, jeśli brak zdjęcia lub Vinted zablokowało bezpośredni link
    url_text = f"https://api.telegram.org/bot{Bot_Token}/sendMessage"
    payload_text = {
        "chat_id": Chat_ID,
        "text": caption,
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True},
    }
    try:
        res = requests.post(url_text, json=payload_text)
        return res.status_code == 200
    except Exception as e:
        print(f"❌ Błąd wysyłania tekstu: {e}")
        return False