import json
import os

DB_FILE = "seen_items.json"


def load_seen_items() -> set:
    """Odczytuje zapamiętane adresy URL z pliku JSON.

    Jeśli plik nie istnieje, zwraca pusty zbiór.
    """
    if not os.path.exists(DB_FILE):
        return set()

    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data)
    except (json.JSONDecodeError, Exception) as e:
        print(f"⚠️ Błąd odczytu bazy {DB_FILE}: {e}. Tworzę czystą bazę.")
        return set()


def save_seen_items(seen_items: set) -> None:
    """Zapisuje zaktualizowany zbiór adresów URL do pliku JSON."""
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(list(seen_items), f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"❌ Błąd zapisu bazy {DB_FILE}: {e}")


if __name__ == "__main__":
    # Test działania modułu
    baza = load_seen_items()
    print(f"Wczytano {len(baza)} zapamiętanych przedmiotów.")

    # Dodajemy testowy URL
    baza.add("https://www.vinted.pl/items/test-123")
    save_seen_items(baza)
    print("✅ Pomyślnie przetestowano zapis do bazy!")