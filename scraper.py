# scraper.py
import re
from collections.abc import Collection

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Locator, Page, sync_playwright

# Twój URL z wyklikanymi filtrami z Vinted (sortowanie od najnowszych)
TARGET_URL = "https://www.vinted.pl/catalog?search_text=kurtki%20napapijri&brand_ids[]=214&size_ids[]=208&size_ids[]=209&size_ids[]=210&status_ids[]=1&status_ids[]=2&status_ids[]=3&status_ids[]=4&search_id=4664424788&order=newest_first"


def _visible_text(locator: Locator, default: str) -> str:
    if locator.count() and locator.is_visible():
        value = locator.inner_text().strip()
        if value:
            return value
    return default


def _detail_text(page: Page, selectors: tuple[str, ...]) -> str:
    for selector in selectors:
        locator = page.locator(selector).first
        if locator.count() and locator.is_visible():
            value = locator.inner_text().strip()
            if value:
                return value
    return ""


def scrape_vinted_products(
    url: str,
    known_item_ids: Collection[str] = (),
) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    scraped_item_ids: set[str] = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 900},
            )
            page = context.new_page()
            print("🌐 Otwieranie strony Vinted...")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)

            cookie_btn = page.locator("#onetrust-accept-btn-handler")
            if cookie_btn.count() and cookie_btn.is_visible():
                cookie_btn.click()

            try:
                page.wait_for_selector(
                    '[data-testid="grid-item"], .feed-grid__item',
                    timeout=20000,
                )
            except PlaywrightError as e:
                raise RuntimeError("Vinted nie załadowało listy ofert.") from e

            for _ in range(2):
                page.evaluate("window.scrollBy(0, 500)")
                page.wait_for_timeout(500)

            items = page.locator(
                '[data-testid="grid-item"], .feed-grid__item'
            ).all()
            print(f"Znaleziono {len(items)} elementów na stronie. Wyciąganie danych...")

            for item in items:
                try:
                    link_element = item.locator('a[href*="/items/"]').first
                    if not link_element.count():
                        link_element = item.locator(
                            'a:not([href*="/member/"])'
                        ).first

                    raw_link = link_element.get_attribute("href") if link_element else ""
                    if not raw_link or "/items/" not in raw_link:
                        continue

                    match = re.search(r"/items/(\d+)", raw_link)
                    if not match:
                        continue
                    item_id = match.group(1)
                    if item_id in scraped_item_ids:
                        continue
                    scraped_item_ids.add(item_id)

                    clean_path = raw_link.split("?")[0]
                    full_link = (
                        clean_path
                        if clean_path.startswith("http")
                        else f"https://www.vinted.pl{clean_path}"
                    )

                    title = _visible_text(
                        item.locator('[data-testid*="title"], p').first,
                        "Brak tytułu",
                    )
                    price = _visible_text(
                        item.locator(
                            '[data-testid="total-combined-price"], [data-testid*="price"]'
                        ).first,
                        "Brak ceny",
                    )
                    size = _visible_text(
                        item.locator('[data-testid*="size"]').first,
                        "Brak rozmiaru",
                    )
                    status = _visible_text(
                        item.locator('[data-testid*="status"]').first,
                        "Brak danych",
                    )

                    image_url = ""
                    img_elements = item.locator(
                        'img[src*="/items/"], img[data-testid*="image"], '
                        'img:not([src*="avatar"]):not([src*="user"])'
                    ).all()
                    for img in img_elements:
                        src_val = img.get_attribute("src") or ""
                        class_val = img.get_attribute("class") or ""
                        alt_val = img.get_attribute("alt") or ""
                        if (
                            "avatar" in src_val.lower()
                            or "avatar" in class_val.lower()
                            or "user" in src_val.lower()
                        ):
                            continue
                        if alt_val and any(
                            x in alt_val.lower()
                            for x in [
                                "profil",
                                "użytkownik",
                                "zdjęcie użytkownika",
                                "avatar",
                            ]
                        ):
                            continue
                        candidate = (
                            img.get_attribute("data-src")
                            or src_val
                            or img.get_attribute("srcset")
                            or ""
                        )
                        if candidate:
                            image_url = candidate.split(",")[0].split(" ")[0].strip()
                            break

                    results.append(
                        {
                            "id": item_id,
                            "title": title,
                            "price": price,
                            "size": size,
                            "status": status,
                            "description": "",
                            "url": full_link,
                            "image_url": image_url,
                        }
                    )
                except PlaywrightError as e:
                    print(f"⚠️ Nie udało się odczytać kafelka oferty: {e}")

            details_page = context.new_page()
            for result in results:
                if result["id"] in known_item_ids:
                    continue
                try:
                    details_page.goto(
                        result["url"],
                        wait_until="domcontentloaded",
                        timeout=20000,
                    )
                    result["description"] = _detail_text(
                        details_page,
                        (
                            '[data-testid*="item-description"]',
                            '[data-testid="item-description"]',
                            '[itemprop="description"]',
                            ".item-description",
                        ),
                    )
                    result["status"] = _detail_text(
                        details_page,
                        (
                            '[data-testid*="item-condition"]',
                            '[data-testid*="item-status"]',
                            '[itemprop="itemCondition"]',
                        ),
                    ) or result["status"]
                except PlaywrightError as e:
                    print(
                        f"⚠️ Nie udało się pobrać szczegółów oferty {result['id']}: {e}"
                    )
        finally:
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