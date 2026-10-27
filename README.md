# Vinted Sniper AI

Bot monitoruje nowe oferty Napapijri z Vinted, analizuje ich zdjęcia i dane przez Gemini oraz wysyła wybrane oferty na Telegram.

## Wymagania

- Python 3.11
- Klucz API Gemini
- Bot Telegrama oraz identyfikator czatu
- Chromium zainstalowany przez Playwright

## Uruchomienie lokalne

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
playwright install chromium
```

Ustaw zmienne środowiskowe `GEMINI_API_KEY`, `BOT_TOKEN` i `CHAT_ID`, a następnie uruchom:

```bash
python main.py
```

Jeśli nie aktywujesz środowiska poleceniem `source .venv/bin/activate`, uruchom program bezpośrednio przez `.venv/bin/python main.py`. W VS Code ustaw interpreter workspace na `.venv/bin/python`.

Historia przetworzonych ofert jest przechowywana w `seen_items.json`; zapis zachowuje maksymalnie 150 najnowszych ID.

## GitHub Actions

Workflow `.github/workflows/vinted_sniper.yml` obsługuje ręczne uruchomienie przez `workflow_dispatch`. Sekrety `GEMINI_API_KEY`, `BOT_TOKEN` i `CHAT_ID` ustaw w **Settings → Secrets and variables → Actions**. Job zapisuje zmiany `seen_items.json` z powrotem do repozytorium, a błędy zapisu/push nie są ukrywane. Zależności i przeglądarka Playwright są buforowane, żeby skrócić kolejne uruchomienia.

## Wyzwalanie co 5 minut tylko w dzień

Repozytorium zawiera Cloudflare Worker, który sprawdza czas `Europe/Warsaw` i uruchamia workflow tylko od 08:00 do 21:55. Worker jest tylko zegarem — bot i przeglądarka nadal działają w GitHub Actions. GitHub może opóźnić start runnera, więc harmonogram nie gwarantuje dokładności co do minuty.

1. Utwórz bezpłatne konto Cloudflare i zainstaluj Node.js/npm na komputerze.
2. Utwórz fine-grained personal access token GitHuba ograniczony do tego repozytorium z uprawnieniem **Actions: Read and write**. Nie zapisuj tokena w repozytorium.
3. Zainstaluj Wrangler i zaloguj się:

   ```bash
   npm install --global wrangler
   wrangler login
   ```

4. Z katalogu repozytorium wdroż Workera, a następnie dodaj token jako sekret:

   ```bash
   wrangler deploy
   wrangler secret put GH_TOKEN
   ```

   Worker będzie raportował brak tokena do czasu dodania sekretu. Wklej token wyłącznie w interaktywnym promptcie `wrangler secret put`; nie przekazuj go jako argumentu polecenia ani nie umieszczaj w pliku.
5. W Cloudflare sprawdź, czy Worker `lively-sky-b286` ma aktywny Cron Trigger `*/5 * * * *`.
6. Podgląd **Visit/Preview** sprawdza tylko status HTTP Workera — nie wywołuje harmonogramu. Test zdarzenia Cron uruchom w Cloudflare z panelu Workera; potwierdź wtedy nowy run w **Actions** w GitHubie. Gdy potwierdzisz poprawne wyzwalanie, wyłącz dotychczasowy zewnętrzny kliker, żeby nie uruchamiać workflow podwójnie.

Worker wywołuje `workflow_dispatch` dla gałęzi `main`. Cron działa w UTC, ale Worker sam przelicza czas na `Europe/Warsaw`, więc uwzględnia zmianę czasu letniego. Równoległe przebiegi GitHub Actions są serializowane przez grupę `concurrency`.
