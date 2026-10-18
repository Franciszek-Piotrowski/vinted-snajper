import requests
from config import Bot_Token, Chat_ID


def send_telegram_message(message: str) -> bool:
    """Wysyła wiadomość tekstową na Telegram za pomocą API HTTP."""
    url = f"https://api.telegram.org/bot{Bot_Token}/sendMessage"
    payload = {"chat_id": Chat_ID, "text": message, "parse_mode": "HTML"}

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("✅ Powiadomienie wysłane pomyślnie na Telegrama!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Błąd podczas wysyłania powiadomienia: {e}")
        return False


if __name__ == "__main__":
    # Test działania modułu
    send_telegram_message(
        "🚀 <b>Vinted Sniper</b>\nCześć Franek! Bot działa i jest gotowy do szukania okazji!"
    )

