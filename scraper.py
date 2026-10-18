# scraper.py
from playwright.sync_api import sync_playwright

# Twój URL z wyklikanymi filtrami z Vinted (np. z sortowaniem od najnowszych)
TARGET_URL = "https://www.vinted.pl/catalog?search_text=kurtki%20napapijri&brand_ids[]=214&size_ids[]=208&size_ids[]=209&size_ids[]=210&status_ids[]=1&status_ids[]=2&status_ids[]=3&status_ids[]=4&search_id=4664424788&order=newest_first&page=1&time=1792318093"


def scrape_vinted_products(url: str) -> list[dict]:
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )

        page = context.new_page()

        print("🌐 Otwieranie strony Vinted...")
        page.goto(url, wait_until="domcontentloaded", timeout=60000)

        # Obsługa banera RODO
        try:
            cookie_btn = page.locator("#onetrust-accept-btn-handler")
            if cookie_btn.is_visible(timeout=3000):
                cookie_btn.click()
        except Exception:
            pass

        # Czekamy na załadowanie kafelków
        page.wait_for_selector(
            '[data-testid="grid-item"], .feed-grid__item', timeout=15000
        )

        # Lekkie przewinięcie strony, aby Vinted wczytało komplet danych
        for _ in range(2):
            page.evaluate("window.scrollBy(0, 500)")
            page.wait_for_timeout(500)

        items = page.locator('[data-testid="grid-item"], .feed-grid__item').all()
        print(f"Znaleziono {len(items)} elementów na stronie. Wyciąganie danych...")

        for item in items:
            try:
                # 1. Tytuł
                title_element = item.locator(
                    '[data-testid*="title"], [data-testid*="description"], p'
                ).first
                title = (
                    title_element.inner_text().strip()
                    if title_element.is_visible()
                    else "Brak tytułu"
                )

                # 2. Cena
                price_element = item.locator(
                    '[data-testid="total-combined-price"], [data-testid*="price"]'
                ).first
                price = (
                    price_element.inner_text().strip()
                    if price_element.is_visible()
                    else "Brak ceny"
                )

                # 3. Rozmiar
                size_element = item.locator('[data-testid*="size"]').first
                size = (
                    size_element.inner_text().strip()
                    if size_element.count() and size_element.is_visible()
                    else "Brak rozmiaru"
                )

                # 4. Stan
                status_element = item.locator('[data-testid*="status"]').first
                status = (
                    status_element.inner_text().strip()
                    if status_element.count() and status_element.is_visible()
                    else "Brak stanu"
                )

                # 5. Link – wyciągamy czysty link do przedmiotu (omijamy profile /member/)
                link_element = item.locator('a[href*="/items/"]').first
                if not link_element.count():
                    link_element = item.locator('a:not([href*="/member/"])').first

                raw_link = link_element.get_attribute("href") if link_element else ""

                if not raw_link or "/items/" not in raw_link:
                    continue

                # Oczyszczamy link z parametrów pytajnika (tworzymy czysty link kanoniczny)
                clean_path = raw_link.split("?")[0]
                full_link = (
                    clean_path
                    if clean_path.startswith("http")
                    else f"https://www.vinted.pl{clean_path}"
                )

                # 6. Zdjęcie – wyciąganie URL grafiki z uwzględnieniem Lazy Loadingu
                img_element = item.locator("img").first
                image_url = ""
                if img_element.count():
                    candidate = (
                        img_element.get_attribute("data-src")
                        or img_element.get_attribute("src")
                        or img_element.get_attribute("srcset")
                        or ""
                    )
                    if candidate:
                        image_url = candidate.split(",")[0].split(" ")[0].strip()

                results.append(
                    {
                        "title": title,
                        "price": price,
                        "size": size,
                        "status": status,
                        "url": full_link,
                        "image_url": image_url,
                    }
                )
            except Exception:
                continue

        browser.close()

    return results


if __name__ == "__main__":
    oferty = scrape_vinted_products(TARGET_URL)

    print(f"\n✅ Pobrano {len(oferty)} ofert:")
    for i, o in enumerate(oferty[:5], 1):
        print(f"{i}. {o['title']} | Cena: {o['price']} | Rozmiar: {o['size']} | Stan: {o['status']}")
        print(f"   Czysty Link: {o['url']}")
        print(f"   Zdjęcie: {o['image_url']}\n")