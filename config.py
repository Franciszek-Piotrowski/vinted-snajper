import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"), override=False)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


def validate_config() -> None:
    missing = [
        name
        for name, value in (
            ("GEMINI_API_KEY", GEMINI_API_KEY),
            ("BOT_TOKEN", BOT_TOKEN),
            ("CHAT_ID", CHAT_ID),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Brak wymaganych zmiennych środowiskowych: "
            + ", ".join(missing)
            + ". Ustaw je w GitHub Actions albo lokalnym pliku .env."
        )