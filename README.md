# Vinted Sniper AI 🎯🤖

An automated, hands-free Vinted deal-sniper designed for finding and selecting reselling opportunities in branded apparel. The project leverages **Google Gemini 3.5 Flash Lite** multimodal AI to autonomously evaluate listings based on market profitability and potential profit margins.

*Note: Currently optimized for tracking Napapijri jackets, but designed with a modular architecture that can be easily adapted for any brand or clothing category.*

## 🚀 Architecture & Tech Stack

- **Language:** Python 3.11
- **Scraping & Automation:** Playwright (headless browser automation)
- **AI & Computer Vision:** Google GenAI SDK (`models/gemini-3.5-flash-lite`)
- **Notifications:** Telegram Bot API
- **CI/CD & Cloud Execution:** GitHub Actions (CRON schedule workflow)

## 💡 How It Works

1. **Scraping:** Periodically triggered scripts fetch the latest Vinted listings based on parameterized URL filters, extracting unique item IDs, titles, prices, descriptions, and cover image URLs.
2. **AI Gatekeeper (Gemini Multimodal):** Every new listing is analyzed by the Gemini model. The AI simultaneously evaluates text (title, description, condition, size) and visual data (identifying anorak cut, presence of fleece lining, verifying condition, and checking for flaws or authenticity issues).
3. **Smart Filtering:** Listings with low margins, bright/unpopular colorways, summer windbreakers, or basic fleece sweaters are automatically rejected (`DECYZJA: NIE`).
4. **Instant Alerts:** Upon approval (`DECYZJA: TAK`), the bot instantly sends a Telegram notification containing the listing photo, margin analysis, value score (1-10), and a direct link to buy.
5. **State Tracking:** Unique IDs of processed items are saved in `seen_items.json` and automatically synced back to the repository via GitHub Actions to prevent duplicate notifications.

## ⚙️ Local Setup

1. Clone the repository:
   ```bash
   git clone [https://github.com/Franciszek-Piotrowski/vinted-snajper.git](https://github.com/Franciszek-Piotrowski/vinted-snajper.git)
   cd vinted-snajper