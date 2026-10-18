import time
from ai_agent import analyze_deal_with_ai
from database import load_seen_items, save_seen_items
from notifier import send_telegram_notification
from scraper import TARGET_URL, scrape_vinted_products

MAX_NOTIFICATIONS = 3


def main():
    print("🚀 Uruchamianie Vinted Snajpera z AI...")

    seen_items = load_seen_items()
    current_items = scrape_vinted_products(TARGET_URL)
    new_items_found = 0

    for item in current_items:
        url = item["url"]

        if url not in seen_items:
            if new_items_found >= MAX_NOTIFICATIONS:
                seen_items.add(url)
                continue

            new_items_found += 1
            print(f"🔥 Analizowanie oferty przez AI: {item['title']}...")

            # 1. Odpytujemy Agenta Gemini o ocenę
            ai_opinion = analyze_deal_with_ai(
                title=item["title"],
                price=item["price"],
                size=item.get("size", "Brak"),
                status=item.get("status", "Brak"),
            )

            # 2. Budujemy wiadomość z werdyktem AI
            caption = (
                f"🔥 <b>NOWA OFERTA VINTED!</b>\n\n"
                f"📌 <b>Przedmiot:</b> {item['title']}\n"
                f"💰 <b>Cena:</b> {item['price']}\n"
                f"📏 <b>Rozmiar:</b> {item.get('size', 'Brak')}\n"
                f"✨ <b>Stan:</b> {item.get('status', 'Brak')}\n\n"
                f"🧠 <b>Ocena Gemini AI:</b>\n{ai_opinion}\n\n"
                f"🔗 <a href='{url}'>Kliknij tutaj, aby przejść do oferty</a>"
            )

            # 3. Wysyłamy powiadomienie ze zdjęciem
            send_telegram_notification(
                caption=caption, photo_url=item.get("image_url")
            )
            seen_items.add(url)

            time.sleep(5)

    if new_items_found > 0:
        save_seen_items(seen_items)


if __name__ == "__main__":
    main()