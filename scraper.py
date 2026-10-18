# scraper.py
import re
from playwright.sync_api import sync_playwright

# Twój URL z wyklikanymi filtrami z Vinted (sortowanie od najnowszych)
TARGET_URL = "https://www.vinted.pl/catalog?search_text=kurtki%20napapijri&brand_ids[]=214&size_ids[]=208&size_ids[]=209&size_ids[]=210&status_ids[]=1&status_ids[]=2&status_ids[]=3&status_ids[]=4&search_id=4664424788&order=newest_first"


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

        # Czekamy na kafelki
        page.wait_for_selector(
            '[data-testid="grid-item"], .feed-grid__item', timeout=15000
        )

        # Przewinięcie pod Lazy Loading
        for _ in range(2):
            page.evaluate("window.scrollBy(0, 500)")
            page.wait_for_timeout(500)

        items = page.locator('[data-testid="grid-item"], .feed-grid__item').all()
        print(f"Znaleziono {len(items)} elementów na stronie. Wyciąganie danych...")

        for item in items:
            try:
                # 1. Wyciąganie czystego linku i unikalnego ID
                link_element = item.locator('a[href*="/items/"]').first
                if not link_element.count():
                    link_element = item.locator('a:not([href*="/member/"])').first

                raw_link = link_element.get_attribute("href") if link_element else ""

                if not raw_link or "/items/" not in raw_link:
                    continue

                # Wyciągamy sam numeryczny ID z linku (np. z /items/123456789-kurtka wyciąga '123456789')
                item_id = ""
                match = re.search(r"/items/(\d+)", raw_link)
                if match:
                    item_id = match.group(1)

                if not item_id:
                    continue  # Pomijamy, jeśli nie udało się wyciągnąć numeru ID

                clean_path = raw_link.split("?")[0]
                full_link = (
                    clean_path
                    if clean_path.startswith("http")
                    else f"https://www.vinted.pl{clean_path}"
                )

                # 2. Tytuł
                title_element = item.locator('[data-testid*="title"], p').first
                title = (
                    title_element.inner_text().strip()
                    if title_element.count() and title_element.is_visible()
                    else "Brak tytułu"
                )

                # 3. Cena
                price_element = item.locator(
                    '[data-testid="total-combined-price"], [data-testid*="price"]'
                ).first
                price = (
                    price_element.inner_text().strip()
                    if price_element.count() and price_element.is_visible()
                    else "Brak ceny"
                )

                # 4. Rozmiar
                size_element = item.locator(
                    '[data-testid*="size"], [data-testid*="subtitle"]'
                ).first
                size = "Brak rozmiaru"
                if size_element.count() and size_element.is_visible():
                    raw_size = size_element.inner_text().strip()
                    if raw_size:
                        size = raw_size

                # 5. Stan
                status_element = item.locator('[data-testid*="status"]').first
                status = "Sprawdź w opisie"
                if status_element.count() and status_element.is_visible():
                    raw_status = status_element.inner_text().strip()
                    if raw_status:
                        status = raw_status

                # 6. Opis z kafelka
                description_element = item.locator(
                    '[data-testid*="description"], [data-testid*="subtitle"]'
                ).first
                description = (
                    description_element.inner_text().strip()
                    if description_element.count() and description_element.is_visible()
                    else "Brak opisu"
                )

                # 7. Zdjęcie (zabezpieczone przed filtrowaniem awatarów profilowych)
                image_url = ""
                img_elements = item.locator(
                    'img[src*="/items/"], img[data-testid*="image"], img:not([src*="avatar"]):not([src*="user"])'
                ).all()

                for img in img_elements:
                    src_val = img.get_attribute("src") or ""
                    class_val = img.get_attribute("class") or ""
                    alt_val = img.get_attribute("alt") or ""

                    # Pomijamy awatary i zdjęcia użytkowników
                    if (
                        "avatar" in src_val.lower()
                        or "avatar" in class_val.lower()
                        or "user" in src_val.lower()
                    ):
                        continue

                    if alt_val and any(
                        x in alt_val.lower()
                        for x in ["profil", "użytkownik", "zdjęcie użytkownika", "avatar"]
                    ):
                        continue

                    candidate = (
                        img.get_attribute("data-src")
                        or img.get_attribute("src")
                        or img.get_attribute("srcset")
                        or ""
                    )
                    if candidate:
                        image_url = candidate.split(",")[0].split(" ")[0].strip()
                        break

                results.append(
                    {
                        "id": item_id,  # Unikalny klucz ID
                        "title": title,
                        "price": price,
                        "size": size,
                        "status": status,
                        "description": description,
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
        print(
            f"{i}. [ID: {o['id']}] {o['title']} | Cena: {o['price']} | Rozmiar: {o['size']} | Stan: {o['status']}"
        )
        print(f"   Opis: {o['description']}")
        print(f"   Link: {o['url']}")
        print(f"   Zdjęcie: {o['image_url']}\n")