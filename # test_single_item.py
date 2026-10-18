# test_single_item.py
import re
from ai_agent import analyze_deal_with_ai
from playwright.sync_api import sync_playwright


def scrape_and_eval_single_url(url: str):
    print(f"\n🌐 Pobieranie danych z linku: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Obsługa banera RODO
            try:
                cookie_btn = page.locator("#onetrust-accept-btn-handler")
                if cookie_btn.is_visible(timeout=2000):
                    cookie_btn.click()
            except Exception:
                pass

            # Czekamy na załadowanie elementów strony oferty
            page.wait_for_timeout(2500)

            # 1. Tytuł
            title_elem = page.locator(
                'h1, [data-testid="item-title"], .item-description__title'
            ).first
            title = (
                title_elem.inner_text().strip()
                if title_elem.count()
                else "Kurtka Napapijri"
            )

            # 2. Cena
            price_elem = page.locator(
                '[data-testid="item-price"], .item-price, h2'
            ).first
            price = (
                price_elem.inner_text().strip()
                if price_elem.count()
                else "Brak ceny"
            )

            # 3. Opis przedmiotu
            details_elem = page.locator(
                '[data-testid="item-description"], .item-description, div.item-description__content'
            ).first
            description = (
                details_elem.inner_text().strip()
                if details_elem.count()
                else "Brak opisu"
            )

            # 4. Rozmiar i Stan ze specyfikacji
            size = "Sprawdź w opisie / M / L"
            status = "Bardzo dobry"

            # Próba wyciągnięcia rozmiaru bezpośrednio ze specyfikacji oferty
            size_elem = page.locator('[data-testid="item-attributes-size"], .item-attributes__size').first
            if size_elem.count():
                size = size_elem.inner_text().strip()

            # 5. Zdjęcie okładkowe (Dedykowany selektor dla galerii ogłoszenia)
            image_url = ""
            
            # Szukamy głównego zdjęcia przedmiotu w galerii (omijamy ikony i UI Vinted)
            main_img_candidates = page.locator(
                'div[data-testid="item-photo"] img, .item-photo img, img[src*="/f800/"], img[src*="/items/"]'
            ).all()

            for img in main_img_candidates:
                candidate = (
                    img.get_attribute("src")
                    or img.get_attribute("data-src")
                    or img.get_attribute("srcset")
                    or ""
                )
                src_clean = candidate.split(",")[0].split(" ")[0].strip()

                # Ignorujemy ikony interfejsu, awatary i przyciski
                if src_clean and not any(
                    x in src_clean.lower()
                    for x in ["avatar", "user", "icon", "logo", "badge", "shield"]
                ):
                    image_url = src_clean
                    break

            browser.close()

            print("✅ Wyciągnięte dane z oferty:")
            print(f"   📌 Tytuł: {title}")
            print(f"   💰 Cena: {price}")
            print(f"   📏 Rozmiar: {size}")
            print(f"   📝 Opis: {description[:120]}...")
            print(f"   🖼️  Zdjęcie: {image_url}\n")

        except Exception as e:
            browser.close()
            print(f"⚠️ Błąd podczas pobierania strony: {e}")
            return

    # Przekazanie pobranych danych do Gemini AI
    print("🧠 Wysyłanie do Gemini AI do oceny...")
    should_send, ai_opinion = analyze_deal_with_ai(
        title=title,
        price=price,
        size=size,
        status=status,
        description=description,
        image_url=image_url,
    )

    print("\n" + "=" * 50)
    print(
        f"RESULT: {'🔥 ZAAKCEPTOWANO (DECYZJA: TAK)' if should_send else '⛔ ODRZUCONO (DECYZJA: NIE)'}"
    )
    print("=" * 50)
    print(f"OPINIA AI:\n{ai_opinion}")
    print("=" * 50)


if __name__ == "__main__":
    test_url = input("Wklej link do oferty Vinted: ").strip()
    if test_url:
        scrape_and_eval_single_url(test_url)
    else:
        print("Nie podano linku!")