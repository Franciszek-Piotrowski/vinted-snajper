# scraper.py
from playwright.sync_api import sync_playwright

# Twój URL z wyklikanymi filtrami z Vinted
TARGET_URL = "https://www.vinted.pl/catalog?search_text=kurtki%20napapijri&size_ids[]=208&size_ids[]=209&size_ids[]=210&brand_ids[]=214&order=newest_first&status_ids[]=1&status_ids[]=2&status_ids[]=3"


def scrape_vinted_products(url: str) -> list[dict]:
    results = []

    with sync_playwright() as p:
        # headless=True sprawia, że przeglądarka działa w tle
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )

        page = context.new_page()

        print("🌐 Otwieranie strony Vinted...")
        page.goto(url, wait_until="domcontentloaded", timeout=60000)

        # Zamknięcie baneru z ciasteczkami, jeśli się pojawi
        try:
            cookie_btn = page.locator("#onetrust-accept-btn-handler")
            if cookie_btn.is_visible(timeout=3000):
                cookie_btn.click()
        except Exception:
            pass

        # Czekamy na załadowanie kafelków ogłoszeń
        page.wait_for_selector(
            '[data-testid="grid-item"], .feed-grid__item', timeout=10000
        )

        items = page.locator('[data-testid="grid-item"], .feed-grid__item').all()
        print(f"Znaleziono {len(items)} elementów na stronie. Wyciąganie danych...")

        for item in items:
            try:
                # Tytuł przedmiotu
                title_element = item.locator(
                    '[data-testid*="title"], [data-testid*="description"], p'
                ).first
                title = (
                    title_element.inner_text().strip()
                    if title_element.is_visible()
                    else "Brak tytułu"
                )

                # Cena przedmiotu – dopasowana do data-testid="total-combined-price"
                price_element = item.locator(
                    '[data-testid="total-combined-price"], [data-testid*="price"]'
                ).first
                price = (
                    price_element.inner_text().strip()
                    if price_element.is_visible()
                    else "Brak ceny"
                )

                # Link do oferty
                link_element = item.locator("a").first
                link = link_element.get_attribute("href") if link_element else ""

                if link and not link.startswith("http"):
                    link = "https://www.vinted.pl" + link

                if link:
                    results.append(
                        {"title": title, "price": price, "url": link}
                    )
            except Exception:
                continue

        browser.close()

    return results


if __name__ == "__main__":
    oferty = scrape_vinted_products(TARGET_URL)

    print(f"\n✅ Pobrano {len(oferty)} ofert:")
    for i, o in enumerate(oferty[:5], 1):  # Wyświetlamy pierwsze 5 ofert
        print(f"{i}. {o['title']} | Cena: {o['price']}")
        print(f"   Link: {o['url']}\n")