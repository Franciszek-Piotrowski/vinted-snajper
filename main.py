import time
from ai_agent import analyze_deal_with_ai
from database import load_seen_items, save_seen_items
from notifier import send_telegram_notification
from scraper import TARGET_URL, scrape_vinted_products

MAX_NOTIFICATIONS = 5


def main():
    print("🚀 Uruchamianie Vinted Snajpera z AI...")

    seen_items = load_seen_items()
    current_items = scrape_vinted_products(TARGET_URL)
    new_items_found = 0

    for item in current_items:
        item_id = item["id"]

        # Sprawdzamy po unikalnym ID zamiast po URL
        if item_id not in seen_items:
            print(
                f"🔎 Analizowanie nowej oferty przez AI (ID: {item_id}): {item['title']}..."
            )

            # 1. Agent Gemini ocenia ofertę
            should_send, ai_opinion = analyze_deal_with_ai(
                title=item["title"],
                price=item["price"],
                size=item.get("size", "Brak"),
                status=item.get("status", "Brak"),
                description=item.get("description", "Brak opisu"),
                image_url=item.get("image_url"),
            )

            # Jeśli błąd API, NIE dodajemy ID do bazy (spróbuje za 15 minut)
            if "Błąd" in ai_opinion or "niedostępne" in ai_opinion:
                print(
                    f"⚠️ Pominięto zapis w bazie dla ID {item_id} z powodu błędu API. Spróbuję za 15 min."
                )
                continue

            # Zapisujemy ID przedmiotu do bazy jako przeanalizowane
            seen_items.add(item_id)

            # 2. Jeśli DECYZJA: NIE, przechodzimy dalej
            if not should_send:
                print(
                    f"⛔ AI odrzuciło ofertę jako nieopłacalną/niezgodną: {item['title']}"
                )
                time.sleep(3)
                continue

            # 3. Jeśli DECYZJA: TAK, wysyłamy powiadomienie
            print(f"🔥 AI ZAAKCEPTOWAŁO PEREŁKĘ: {item['title']} - {item['price']}")

            caption = (
                f"🔥 <b>PEREŁKA Z VINTED (Zatwierdzona przez AI)!</b>\n\n"
                f"📌 <b>Przedmiot:</b> {item['title']}\n"
                f"💰 <b>Cena:</b> {item['price']}\n"
                f"📏 <b>Rozmiar:</b> {item.get('size', 'Brak')}\n"
                f"✨ <b>Stan:</b> {item.get('status', 'Brak')}\n\n"
                f"🧠 <b>Ocena i Wyliczenia Gemini:</b>\n{ai_opinion}\n\n"
                f"🔗 <a href='{item['url']}'>Kliknij tutaj, aby przejść do oferty</a>"
            )

            send_telegram_notification(
                caption=caption, photo_url=item.get("image_url")
            )

            new_items_found += 1

            time.sleep(3)

    if new_items_found > 0:
        save_seen_items(seen_items)
        print(f"✅ Zakończono! Wysłano {new_items_found} selektywnych perełek.")
    else:
        save_seen_items(seen_items)
        print("ℹ️ Baza zaktualizowana. Brak nowych ofert spełniających kryteria AI.")


if __name__ == "__main__":
    main()