# main.py
import time
from database import load_seen_items, save_seen_items
from notifier import send_telegram_notification
from scraper import TARGET_URL, scrape_vinted_products

MAX_NOTIFICATIONS = 3  # Limit powiadomień na jedno uruchomienie


def main():
    print("🚀 Uruchamianie Vinted Snajpera...")

    seen_items = load_seen_items()
    current_items = scrape_vinted_products(TARGET_URL)
    new_items_found = 0

    for item in current_items:
        url = item["url"]

        if url not in seen_items:
            if new_items_found >= MAX_NOTIFICATIONS:
                print(f"⚠️ Osiągnięto limit {MAX_NOTIFICATIONS} powiadomień. Reszta trafia do bazy po cichu.")
                seen_items.add(url)
                continue

            new_items_found += 1
            print(f"🔥 Nowa okazja: {item['title']} - {item['price']}")

            # Budujemy treść podpisu pod zdjęciem
            caption = (
                f"🔥 <b>NOWA OFERTA VINTED!</b>\n\n"
                f"📌 <b>Przedmiot:</b> {item['title']}\n"
                f"💰 <b>Cena:</b> {item['price']}\n"
                f"📏 <b>Rozmiar:</b> {item.get('size', 'Brak')}\n"
                f"✨ <b>Stan:</b> {item.get('status', 'Brak')}\n\n"
                f"🔗 <a href='{url}'>Kliknij tutaj, aby przejść do oferty</a>"
            )

            # Wysyłamy zdjęcie wraz z podpisem
            send_telegram_notification(caption=caption, photo_url=item.get("image_url"))
            seen_items.add(url)

            # 5 sekund przerwy, aby serwery nie nakładały blokad
            print("⏳ Czekam 5 sekund przed kolejnym powiadomieniem...")
            time.sleep(5)

    if new_items_found > 0:
        save_seen_items(seen_items)
        print(f"✅ Zakończono! Wysłano {new_items_found} nowych powiadomień ze zdjęciami.")
    else:
        print("ℹ️ Brak nowych ofert.")


if __name__ == "__main__":
    main()