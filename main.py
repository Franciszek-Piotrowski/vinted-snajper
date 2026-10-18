# main.py
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
        url = item["url"]

        if url not in seen_items:
            print(f"🔎 Analizowanie nowej oferty przez AI: {item['title']}...")

            # 1. Agent Gemini ocenia ofertę
            should_send, ai_opinion = analyze_deal_with_ai(
                title=item["title"],
                price=item["price"],
                size=item.get("size", "Brak"),
                status=item.get("status", "Brak"),
                description=item.get("description", "Brak opisu"),
                image_url=item.get("image_url"),
            )

            # ZABEZPIECZENIE: Jeśli AI wywaliło błąd API, NIE dodajemy linku do bazy.
            if "Błąd" in ai_opinion or "niedostępne" in ai_opinion:
                print(f"⚠️ Pomięto zapis w bazie dla {item['title']} z powodu błędu AI. Spróbuję w kolejnym cyklu.")
                continue

            # Jeśli analiza przebiegła pomyślnie, zapisujemy link do bazy
            seen_items.add(url)

            # 2. Jeśli AI odrzuciło ofertę (DECYZJA: NIE), po cichu przechodzimy dalej
            if not should_send:
                print(f"⛔ AI odrzuciło ofertę jako nieopłacalną/niezgodną: {item['title']}")
                continue

            # 3. Jeśli AI zaakceptowało ofertę (DECYZJA: TAK), wysyłamy powiadomienie
            new_items_found += 1
            print(f"🔥 AI ZAAKCEPTOWAŁO PERAŁKĘ: {item['title']} - {item['price']}")

            caption = (
                f"🔥 <b>PERAŁKA Z VINTED (Zatwierdzona przez AI)!</b>\n\n"
                f"📌 <b>Przedmiot:</b> {item['title']}\n"
                f"💰 <b>Cena:</b> {item['price']}\n"
                f"📏 <b>Rozmiar:</b> {item.get('size', 'Brak')}\n"
                f"✨ <b>Stan:</b> {item.get('status', 'Brak')}\n\n"
                f"🧠 <b>Ocena i Wyliczenia Gemini:</b>\n{ai_opinion}\n\n"
                f"🔗 <a href='{url}'>Kliknij tutaj, aby przejść do oferty</a>"
            )

            send_telegram_notification(
                caption=caption, photo_url=item.get("image_url")
            )

            if new_items_found >= MAX_NOTIFICATIONS:
                print(f"⚠️ Osiągnięto limit {MAX_NOTIFICATIONS} wysłanych perełek w tym cyklu.")
                break

            time.sleep(5)

    if new_items_found > 0:
        save_seen_items(seen_items)
        print(f"✅ Zakończono! Wysłano {new_items_found} selektywnych perełek.")
    else:
        save_seen_items(seen_items)
        print("ℹ️ Baza zaktualizowana. Brak nowych ofert spełniających rygorystyczne kryteria AI.")


if __name__ == "__main__":
    main()