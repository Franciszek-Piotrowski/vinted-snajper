import json
import os
import tempfile
from collections.abc import Iterable

DB_FILE = "seen_items.json"
MAX_SEEN_ITEMS = 150


def load_seen_items() -> list[str]:
    """Load processed listing IDs in their persisted order."""
    if not os.path.exists(DB_FILE):
        return []

    with open(DB_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
        raise ValueError(f"Nieprawidłowy format historii ofert w {DB_FILE}.")

    return list(dict.fromkeys(data))


def save_seen_items(seen_items: Iterable[str]) -> None:
    """Atomically save the 150 most recently processed listing IDs."""
    recent_items = list(dict.fromkeys(seen_items))[:MAX_SEEN_ITEMS]
    directory = os.path.dirname(os.path.abspath(DB_FILE))
    temporary_path = ""

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=directory,
            delete=False,
        ) as f:
            temporary_path = f.name
            json.dump(recent_items, f, ensure_ascii=False, indent=4)
            f.write("\n")
        os.replace(temporary_path, DB_FILE)
    except OSError:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)
        raise


if __name__ == "__main__":
    baza = load_seen_items()
    print(f"Wczytano {len(baza)} zapamiętanych przedmiotów.")
    baza.insert(0, "test-123")
    save_seen_items(baza)
    print("✅ Pomyślnie przetestowano zapis do bazy!")