# notifier.py
from typing import Optional

import requests
from config import BOT_TOKEN, CHAT_ID


def _send(url: str, payload: dict) -> bool:
    try:
        response = requests.post(url, json=payload, timeout=15)
    except requests.RequestException as e:
        print(f"❌ Błąd żądania Telegram API: {e}")
        return False

    try:
        response_data = response.json()
    except ValueError:
        response_data = {}
    result = response_data if isinstance(response_data, dict) else {}

    if response.ok and result.get("ok") is True:
        return True

    print(
        "❌ Telegram API odrzuciło wiadomość "
        f"(HTTP {response.status_code}): {result.get('description', response.text)}"
    )
    return False


def send_telegram_notification(
    caption: str,
    photo_url: Optional[str] = None,
) -> bool:
    """Wysyła post ze zdjęciem (sendPhoto) lub awaryjnie sam tekst (sendMessage)."""
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Brak BOT_TOKEN lub CHAT_ID; nie można wysłać powiadomienia.")
        return False

    if photo_url:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        payload = {
            "chat_id": CHAT_ID,
            "photo": photo_url,
            "caption": caption,
            "parse_mode": "HTML",
        }
        if _send(url, payload):
            return True
        print("⚠️ Nie udało się wysłać zdjęcia; próbuję wysłać sam tekst.")

    # Awaryjne wysłanie samego tekstu, jeśli brak zdjęcia lub Vinted zablokowało bezpośredni link
    url_text = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload_text = {
        "chat_id": CHAT_ID,
        "text": caption,
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True},
    }
    return _send(url_text, payload_text)