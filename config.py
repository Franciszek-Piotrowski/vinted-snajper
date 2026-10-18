# config.py
import os

# Odczyt kluczy ze zmiennych środowiskowych (GitHub Secrets w chmurze lub plik .env lokalnie)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
Bot_Token = os.getenv("Bot_Token")
Chat_ID = os.getenv("Chat_ID")