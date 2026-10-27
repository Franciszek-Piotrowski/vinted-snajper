import html
import time

from ai_agent import analyze_deal_with_ai
from config import validate_config
from database import MAX_SEEN_ITEMS, load_seen_items, save_seen_items
from notifier import send_telegram_notification
from scraper import TARGET_URL, scrape_vinted_products

MAX_NOTIFICATIONS = 5


def main() -> None:
    print("🚀 Uruchamianie Vinted Snajpera z AI...")
    validate_config()

    seen_items = load_seen_items()
    seen_item_ids = set(seen_items)
    current_items = scrape_vinted_products(TARGET_URL, seen_item_ids)
    if len(seen_items) > MAX_SEEN_ITEMS:
        visible_seen_ids = [
            item["id"] for item in current_items if item["id"] in seen_item_ids
        ]
        visible_seen_set = set(visible_seen_ids)
        seen_items = visible_seen_ids + [
            item_id for item_id in seen_items if item_id not in visible_seen_set
        ]
        save_seen_items(seen_items)
    new_items_found = 0

    for item in current_items:
        item_id = item["id"]
        if item_id in seen_item_ids:
            continue

        print(
            f"🔎 Analizowanie nowej oferty przez AI (ID: {item_id}): {item['title']}..."
        )
        should_send, ai_opinion = analyze_deal_with_ai(
            title=item["title"],
            price=item["price"],
            size=item.get("size", "Brak rozmiaru"),
            status=item.get("status", "Brak danych"),
            description=item.get("description", "Brak opisu"),
            image_url=item.get("image_url"),
        )

        if should_send is None:
            print(
                f"⚠️ Nie zapisuję ID {item_id}; analiza AI nie powiodła się i oferta wróci do ponownej próby."
            )
            continue

        if not should_send:
            print(f"⛔ AI odrzuciło ofertę: {item['title']}")
            seen_items.insert(0, item_id)
            seen_item_ids.add(item_id)
            save_seen_items(seen_items)
            time.sleep(3)
            continue

        safe_title = html.escape(item["title"])
        safe_price = html.escape(item["price"])
        safe_size = html.escape(item.get("size", "Brak rozmiaru"))
        safe_status = html.escape(item.get("status", "Brak danych"))
        safe_opinion = html.escape(ai_opinion)
        safe_url = html.escape(item["url"], quote=True)
        caption = (
            "🔥 <b>PEREŁKA Z VINTED (Zatwierdzona przez AI)!</b>\n\n"
            f"📌 <b>Przedmiot:</b> {safe_title}\n"
            f"💰 <b>Cena:</b> {safe_price}\n"
            f"📏 <b>Rozmiar:</b> {safe_size}\n"
            f"✨ <b>Stan:</b> {safe_status}\n\n"
            f"🧠 <b>Ocena i Wyliczenia Gemini:</b>\n{safe_opinion}\n\n"
            f'🔗 <a href="{safe_url}">Kliknij tutaj, aby przejść do oferty</a>'
        )

        if not send_telegram_notification(
            caption=caption,
            photo_url=item.get("image_url"),
        ):
            print(
                f"⚠️ Telegram nie potwierdził wysyłki dla ID {item_id}; oferta wróci do ponownej próby."
            )
            continue

        seen_items.insert(0, item_id)
        seen_item_ids.add(item_id)
        save_seen_items(seen_items)
        new_items_found += 1
        time.sleep(3)

        if new_items_found >= MAX_NOTIFICATIONS:
            print(f"ℹ️ Osiągnięto limit {MAX_NOTIFICATIONS} powiadomień na uruchomienie.")
            break

    if new_items_found:
        print(f"✅ Zakończono! Wysłano {new_items_found} selektywnych perełek.")
    else:
        print("ℹ️ Baza zaktualizowana. Brak nowych ofert spełniających kryteria AI.")


if __name__ == "__main__":
    main()
