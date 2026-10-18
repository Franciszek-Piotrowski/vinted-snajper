import time
from database import load_seen_items, save_seen_items
from notifier import send_telegram_message
from scraper import TARGET_URL, scrape_vinted_products


def main():
    print("🚀 Uruchamianie Vinted Snajpera...")

    # 1. Wczytujemy z bazy linki, które już wcześniej widzieliśmy
    seen_items = load_seen_items()
    print(f"Baza pamięta obecnie {len(seen_items)} wcześniej sprawdzonych ofert.")

    # 2. Pobieramy aktualne oferty z Vinted
    current_items = scrape_vinted_products(TARGET_URL)
    new_items_found = 0

    # 3. Przeglądamy pobrane oferty
    for item in current_items:
        url = item["url"]

        # Jeśli oferta jest nowa (nie ma jej w bazie seen_items)
        if url not in seen_items:
            new_items_found += 1
            print(f"🔥 Znaleziono nową okazję: {item['title']} - {item['price']}")

            # Przygotowujemy treść wiadomości
            message = (
                f"🔥 <b>NOWA OFERTA VINTED!</b>\n\n"
                f"📌 <b>Przedmiot:</b> {item['title']}\n"
                f"💰 <b>Cena:</b> {item['price']}\n\n"
                f"🔗 <a href='{url}'>Kliknij tutaj, aby przejść do oferty</a>"
            )

            # Wysyłamy powiadomienie na Telegrama
            send_telegram_message(message)

            # Zapamiętujemy link w bazie, żeby nie wysłać go drugi raz
            seen_items.add(url)

            # Krótka pauza między powiadomieniami
            time.sleep(5)

    # 4. Zapisujemy zaktualizowaną bazę do pliku JSON
    if new_items_found > 0:
        save_seen_items(seen_items)
        print(
            f"✅ Znaleziono i wysłano {new_items_found} nowych ofert. Baza zaktualizowana."
        )
    else:
        print("ℹ️ Brak nowych ofert na Vinted.")


if __name__ == "__main__":
    main()